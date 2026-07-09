"""Servicio de notificaciones y reportes SMS via ModemManager."""

import asyncio
import logging
import os
import re
import subprocess
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.config import SmsConfig
from src.models import Weighing

logger = logging.getLogger(__name__)

_SMS_INDEX_RE = re.compile(r"/org/freedesktop/ModemManager1/SMS/(\d+)")


class SMSDeliveryError(Exception):
    """Se lanza cuando mmcli falla al enviar un SMS."""
    pass


class SMSService:
    """Servicio de envio de SMS con soporte dual dev/prod.

    En modo desarrollo (dev_mode=True) simula el envio mediante log.
    En modo produccion ejecuta mmcli contra el modem gestionado por ModemManager.
    """

    def __init__(self, config: SmsConfig, modem_index: int, dev_mode: bool) -> None:
        self._config = config
        self._modem_index = modem_index
        self._dev_mode = dev_mode
        self._scheduler_task: asyncio.Task | None = None
        self._sent_today: set[str] = set()
        self._current_report_day: str = ""
        self._template_service = None  # Se inyecta externamente
        self._persistence = None  # SmsPersistenceService, se inyecta externamente

    def set_template_service(self, template_service) -> None:
        """Inyecta el ReportTemplateService para reportes basados en plantillas."""
        self._template_service = template_service

    def set_persistence_service(self, persistence) -> None:
        """Inyecta el SmsPersistenceService para persistir mensajes SMS.

        Feature 27 — sms_persistence.
        Si no se inyecta, send_sms() funciona en modo legacy (sin persistencia).
        """
        self._persistence = persistence
        self._send_queue = None

    def set_send_queue(self, send_queue):
        self._send_queue = send_queue

    # ------------------------------------------------------------------
    # Envio individual
    # ------------------------------------------------------------------

    def _persist_sms(self, phone: str, message: str) -> int | None:
        """Persiste un SMS en sms_messages (helper reutilizable).

        Crea/recupera conversacion y crea el mensaje con status='pending'.
        Retorna el id del mensaje persistido, o None si falla o no hay
        servicio de persistencia inyectado.
        """
        if self._persistence is None:
            return None
        try:
            conv = self._persistence.get_or_create_active_conversation(
                peer_number=phone, workflow_type="unknown",
            )
            msg = self._persistence.create_message(
                conversation_id=conv.id,
                direction="sent",
                peer_number=phone,
                body=message,
                handler="sms_service",
                status="pending",
            )
            return msg.id
        except Exception:
            logger.exception("sms_service: error persistiendo mensaje SMS")
            return None

    def _update_persisted_status(self, msg_id: int | None, status: str, error_message: str | None = None) -> None:
        """Actualiza el status de un mensaje persistido (helper reutilizable)."""
        if msg_id is None or self._persistence is None:
            return
        try:
            self._persistence.update_message_status(msg_id, status, error_message=error_message)
        except Exception:
            logger.exception("sms_service: error actualizando status de mensaje")

    def send_sms(self, phone: str, message: str) -> bool:
        """Envia un SMS al numero indicado.

        En dev mode simula el envio con log. En prod ejecuta mmcli.
        Si hay persistencia inyectada, registra el mensaje en sms_messages
        antes de enviar y actualiza el status segun el resultado.

        B3: Si SMS_DRY_RUN=true, simula exito sin tocar el modem.

        Returns:
            True si el envio tuvo exito (dev mode siempre True),
            False en caso de fallo (el error se loggea internamente).
        """
        # B3: SMS_DRY_RUN bloquea envios reales
        dry_run = os.getenv("SMS_DRY_RUN", "false").lower() in ("true", "1", "yes")
        if dry_run:
            logger.info("[DRY_RUN] SMS bloqueado -> %s: %s", phone, message)
            self._persist_sms(phone, message)
            return True

        if not phone or not message:
            logger.warning("send_sms llamado con phone o message vacio, omitiendo")
            return False

        # R18: Persistir en sms_messages antes de enviar
        persisted_msg_id = self._persist_sms(phone, message)

        if self._dev_mode:
            logger.info(
                "[DEV_MODE] SMS simulado -> %s: %s", phone, message
            )
            self._update_persisted_status(persisted_msg_id, "sent")
            return True

        # Envio atomico sincrono: marcar como sending, enviar, actualizar.
        # Esto evita race conditions con SmsSendQueue (que solo ve "pending")
        # y el doble-envio (Bug #26).
        if persisted_msg_id is not None:
            self._update_persisted_status(persisted_msg_id, "sending")
        success = self._send_via_mmcli(phone, message, persisted_msg_id)
        if success:
            logger.info("SMS enviado correctamente a %s (msg_id=%s)", phone, persisted_msg_id)
        return success

    def send_sms_sync(self, phone: str, message: str) -> bool:
        """Envia un SMS de forma sincrona (bloqueante).

        Para casos legacy que requieren confirmacion inmediata de entrega.
        Persiste en sms_messages y ejecuta mmcli directamente sin pasar
        por la cola asincrona.

        B3: Si SMS_DRY_RUN=true, simula exito sin tocar el modem.

        Returns:
            True si mmcli confirmo el envio, False si fallo.
        """
        # B3: SMS_DRY_RUN bloquea envios reales
        dry_run = os.getenv("SMS_DRY_RUN", "false").lower() in ("true", "1", "yes")
        if dry_run:
            logger.info("[DRY_RUN] SMS bloqueado (sync) -> %s: %s", phone, message)
            self._persist_sms(phone, message)
            return True

        if not phone or not message:
            logger.warning("send_sms_sync llamado con phone o message vacio")
            return False

        # R18: Persistir antes de enviar
        persisted_msg_id = self._persist_sms(phone, message)

        if self._dev_mode:
            logger.info("[DEV_MODE] SMS simulado (sync) -> %s: %s", phone, message)
            self._update_persisted_status(persisted_msg_id, "sent")
            return True

        success = self._send_via_mmcli_sync(phone, message)

        new_status = "sent" if success else "failed"
        self._update_persisted_status(
            persisted_msg_id, new_status,
            error_message=None if success else "mmcli send failed (sync)",
        )

        return success

    def _send_via_mmcli(self, phone: str, message: str, message_id: int | None = None) -> bool:
        """Envia un SMS usando mmcli. Retorna True si exitoso, False si falla.
        
        Ejecuta subprocess.run en un ThreadPoolExecutor para no bloquear
        el event loop asyncio. Esto evita que el watchdog heartbeat se detenga
        cuando mmcli tarda en responder (ej: QMI protocol errors).
        """
        try:
            asyncio.get_running_loop()
            # Hay event loop: ejecutar en thread para no bloquear
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(self._send_via_mmcli_sync, phone, message, message_id).result()
        except RuntimeError:
            # No hay event loop: ejecutar sincrono
            return self._send_via_mmcli_sync(phone, message, message_id)

    def _delete_orphan_sms(self, sms_index: str) -> None:
        """Elimina un SMS huerfano del modem tras un fallo de envio (B1).

        Si mmcli creo el objeto SMS pero --send fallo, el objeto queda
        en el modem. El dispatcher lo detectaria como SMS entrante en
        el siguiente ciclo, creando un loop infinito.
        """
        try:
            subprocess.run(
                ["sudo", "-n", "mmcli", "-m", str(self._modem_index),
                 f"--messaging-delete-sms={sms_index}"],
                capture_output=True, timeout=10,
            )
            logger.info("SMS huerfano %s eliminado del modem tras fallo de envio", sms_index)
        except Exception:
            logger.warning("No se pudo eliminar SMS huerfano %s del modem", sms_index)

    def _send_via_mmcli_sync(self, phone: str, message: str, message_id: int | None = None) -> bool:
        """Version sincrona de _send_via_mmcli (se ejecuta en un thread).

        Args:
            phone: Numero de telefono destino.
            message: Texto del mensaje.
            message_id: ID del mensaje en sms_messages para persistir modem_sms_id.
                Solo se pasa desde SmsSendQueue (cola asincrona).
        """
        mmcli_path = "sudo"
        modem_arg = str(self._modem_index)

        escaped = message.replace("'", "")
        smsc = os.getenv("MMCLI_SMSC", "+573003690025")
        props = f"number='{phone}',text='{escaped}',smsc='{smsc}'"

        # Paso 1: crear el SMS
        create_args = [
            mmcli_path, "-n", "mmcli", "-m", modem_arg,
            "--messaging-create-sms",
            props,
        ]
        try:
            result = subprocess.run(
                create_args,
                capture_output=True,
                text=True,
                timeout=20,
            )
        except FileNotFoundError:
            logger.error("mmcli no encontrado en el sistema")
            return False
        except subprocess.TimeoutExpired:
            logger.error("Timeout al crear SMS via mmcli para %s", phone)
            return False
        except OSError as exc:
            logger.error("Error de SO al ejecutar mmcli (crear SMS): %s", exc)
            return False

        if result.returncode != 0:
            stderr = result.stderr.strip() if result.stderr else "unknown error"
            logger.error("mmcli fallo al crear SMS (exit %d): %s", result.returncode, stderr)
            return False

        match = _SMS_INDEX_RE.search(result.stdout)
        if not match:
            logger.error("No se pudo extraer el indice del SMS de la salida de mmcli: %s", result.stdout)
            return False

        sms_index = match.group(1)

        # Paso 2: enviar el SMS
        send_args = ["sudo", "-n", "mmcli", "-s", sms_index, "--send"]
        try:
            result = subprocess.run(
                send_args,
                capture_output=True,
                text=True,
                timeout=20,
            )
        except subprocess.TimeoutExpired:
            logger.error("Timeout al enviar SMS %s para %s", sms_index, phone)
            # B1: Limpiar SMS huerfano del modem
            self._delete_orphan_sms(sms_index)
            return False
        except OSError as exc:
            logger.error("Error de SO al ejecutar mmcli (enviar SMS): %s", exc)
            # B1: Limpiar SMS huerfano del modem
            self._delete_orphan_sms(sms_index)
            return False

        if result.returncode != 0:
            stderr = result.stderr.strip() if result.stderr else "unknown error"
            logger.error("mmcli fallo al enviar SMS %s (exit %d): %s", sms_index, result.returncode, stderr)
            # B1: Limpiar SMS huerfano del modem
            self._delete_orphan_sms(sms_index)
            return False

        # Fix 2: Persistir modem_sms_id si se proporciono message_id
        if message_id is not None and self._persistence is not None:
            try:
                self._persistence.update_message_status(
                    message_id, "sent",
                    modem_sms_id=int(sms_index),
                )
            except Exception:
                logger.exception(
                    "Error guardando modem_sms_id para msg %s", message_id,
                )

        logger.info("SMS enviado correctamente a %s (modem_id=%s)", phone, sms_index)
        return True

    # ------------------------------------------------------------------
    # Envio a administradores
    # ------------------------------------------------------------------

    def send_alert_to_admins(self, message: str) -> None:
        """Envia un mensaje de alerta a todos los numeros en admin_phones."""
        self._send_to_all_admins(message)

    def send_scheduled_report(self, report_text: str, recipients: list[str] | None = None) -> None:
        """Envia un reporte programado a los destinatarios especificados.

        Si recipients es None, envia a todos los admin_phones.
        """
        if recipients:
            for phone in recipients:
                if phone:
                    self.send_sms(phone, report_text)
        else:
            self._send_to_all_admins(report_text)

    def _send_to_all_admins(self, message: str) -> None:
        """Envia el mensaje a todos los numeros en admin_phones."""
        if not self._config.admin_phones:
            logger.info("admin_phones vacio, no se envia SMS")
            return
        for phone in self._config.admin_phones:
            if phone:
                self.send_sms(phone, message)

    # ------------------------------------------------------------------
    # Generacion de reportes de turno
    # ------------------------------------------------------------------

    def generate_turn_report(self, db: Session, turn_start: str, turn_end: str) -> str:
        """Genera el texto del reporte de turno consultando la BD.

        turn_start y turn_end son strings en formato "HH:MM".
        """
        today = datetime.now(timezone.utc).date()
        count = (
            db.query(func.count(Weighing.id))
            .filter(
                func.date(Weighing.created_at) == today,
                func.time(Weighing.created_at) >= turn_start,
                func.time(Weighing.created_at) <= turn_end,
            )
            .scalar()
        ) or 0
        total_weight = (
            db.query(func.coalesce(func.sum(
                Weighing.peso_muestra
                + Weighing.peso_mineral
                + Weighing.peso_vegetal_extrano
            ), 0))
            .filter(
                func.date(Weighing.created_at) == today,
                func.time(Weighing.created_at) >= turn_start,
                func.time(Weighing.created_at) <= turn_end,
            )
            .scalar()
        ) or 0.0

        report = (
            f"Reporte de turno [{turn_start} - {turn_end}]: "
            f"{count} pesajes realizados, "
            f"peso total: {float(total_weight):.2f} kg"
        )
        return report

    # ------------------------------------------------------------------
    # Planificador asincrono
    # ------------------------------------------------------------------

    def start_scheduler(self) -> None:
        """Lanza la corutina asyncio del planificador de reportes."""
        if self._scheduler_task is not None and not self._scheduler_task.done():
            logger.warning("El planificador de SMS ya esta corriendo")
            return
        logger.info("Iniciando planificador de reportes SMS")
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())

    def stop_scheduler(self) -> None:
        """Cancela la corutina del planificador."""
        if self._scheduler_task is not None and not self._scheduler_task.done():
            logger.info("Deteniendo planificador de reportes SMS")
            self._scheduler_task.cancel()

    async def _scheduler_loop(self) -> None:
        """Bucle del planificador: verifica cada 30 s si toca enviar reporte."""
        while True:
            try:
                await self._check_and_send_reports()
            except asyncio.CancelledError:
                logger.info("Planificador de reportes SMS cancelado")
                break
            except Exception:
                logger.exception("Error inesperado en el planificador de SMS")
            try:
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                logger.info("Planificador de reportes SMS cancelado durante sleep")
                break

    async def _check_and_send_reports(self) -> None:
        """Verifica si la hora actual coincide con un horario de reporte.

        Soporta dos fuentes de reportes programados:
        1. Horarios fijos de config.yaml (sms.scheduled_reports)
        2. Plantillas activas en report_templates (BD)
        """
        now = datetime.now(timezone.utc)
        current_day = now.strftime("%Y-%m-%d")

        # Resetear el set de enviados si cambia el dia
        if current_day != self._current_report_day:
            self._sent_today.clear()
            self._current_report_day = current_day

        current_time = now.strftime("%H:%M")

        # 1. Reportes de horarios fijos (config.yaml)
        for scheduled in self._config.scheduled_reports:
            if scheduled == current_time and scheduled not in self._sent_today:
                self._sent_today.add(scheduled)
                logger.info("Enviando reporte programado para %s", scheduled)
                await self._do_send_report(scheduled)

        # 2. Reportes de plantillas activas (T26)
        if self._template_service is not None:
            template_key = f"tpl_{current_time}"
            if template_key not in self._sent_today:
                self._sent_today.add(template_key)
                await self._send_template_reports(current_time)

    async def _send_template_reports(self, current_time: str) -> None:
        """Envia reportes para todas las plantillas activas en este horario."""
        try:
            templates = self._template_service.get_active_by_schedule(current_time)
        except Exception:
            logger.exception("Error consultando plantillas de reporte")
            return

        if not templates:
            return

        import src.database as _db
        db = _db.SessionLocal()
        try:
            for template in templates:
                try:
                    report_text = self._template_service.generate_report(template, db)
                    # Resolver destinatarios via JOIN a tabla pivote + users
                    recipients = self._template_service.get_recipient_phones(template.id)
                    self.send_scheduled_report(report_text, recipients=recipients)
                    logger.info("Reporte de plantilla '%s' enviado a %d destinatarios",
                               template.name, len(recipients))
                except Exception:
                    logger.exception("Error generando reporte para plantilla %s", template.id)
        finally:
            db.close()

    async def _do_send_report(self, time_slot: str) -> None:
        """Ejecuta el envio del reporte para el horario dado.

        Calcula el turno correspondiente segun el horario:
        - 06:00 -> turno 00:00-06:00
        - 14:00 -> turno 06:00-14:00
        - 22:00 -> turno 14:00-22:00
        Para otros horarios, usa la ventana desde el reporte anterior.
        """
        # Determinar inicio del turno en base al horario
        slot_to_start: dict[str, str] = {
            "06:00": "00:00",
            "14:00": "06:00",
            "22:00": "14:00",
        }
        if time_slot in slot_to_start:
            turn_start = slot_to_start[time_slot]
        else:
            # Para horarios personalizados: ventana desde el reporte anterior
            turn_start = self._find_previous_slot(time_slot)

        turn_end = time_slot

        # Obtener sesion de BD desde la app
        import src.database as _db
        db = _db.SessionLocal()
        try:
            report_text = self.generate_turn_report(db, turn_start, turn_end)
            self.send_scheduled_report(report_text)
        finally:
            db.close()

    def _find_previous_slot(self, time_slot: str) -> str:
        """Encuentra el horario de reporte inmediatamente anterior al dado."""
        sorted_slots = sorted(self._config.scheduled_reports)
        try:
            idx = sorted_slots.index(time_slot)
        except ValueError:
            return "00:00"
        if idx == 0:
            return "00:00"
        return sorted_slots[idx - 1]
