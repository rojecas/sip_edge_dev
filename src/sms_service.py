"""Servicio de notificaciones y reportes SMS via ModemManager."""

import asyncio
import logging
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

    def set_template_service(self, template_service) -> None:
        """Inyecta el ReportTemplateService para reportes basados en plantillas."""
        self._template_service = template_service

    # ------------------------------------------------------------------
    # Envio individual
    # ------------------------------------------------------------------

    def send_sms(self, phone: str, message: str) -> bool:
        """Envia un SMS al numero indicado.

        En dev mode simula el envio con log. En prod ejecuta mmcli.
        Devuelve True si el envio tuvo exito, False en caso de fallo
        (el error se loggea internamente).
        """
        if not phone or not message:
            logger.warning("send_sms llamado con phone o message vacio, omitiendo")
            return False

        if self._dev_mode:
            logger.info(
                "[DEV_MODE] SMS simulado -> %s: %s", phone, message
            )
            return True

        return self._send_via_mmcli(phone, message)

    def _send_via_mmcli(self, phone: str, message: str) -> bool:
        """Envia un SMS usando mmcli. Retorna True si exitoso, False si falla."""
        mmcli_path = "sudo"
        modem_arg = str(self._modem_index)

        # Escapar comillas simples para mmcli: '' representa una comilla literal
        escaped = message.replace('"', '\"')
        # Envolver en comillas simples para que mmcli no interprete comas ni otros chars
        props = f"number={phone},text=\"{escaped}\""

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
                timeout=30,
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

        # Extraer indice del SMS creado
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
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            logger.error("Timeout al enviar SMS %s para %s", sms_index, phone)
            return False
        except OSError as exc:
            logger.error("Error de SO al ejecutar mmcli (enviar SMS): %s", exc)
            return False

        if result.returncode != 0:
            stderr = result.stderr.strip() if result.stderr else "unknown error"
            logger.error("mmcli fallo al enviar SMS %s (exit %d): %s", sms_index, result.returncode, stderr)
            return False

        logger.info("SMS enviado correctamente a %s", phone)
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
                    # Obtener destinatarios de la plantilla
                    import json
                    try:
                        recipients = json.loads(template.recipients)
                    except (json.JSONDecodeError, TypeError):
                        recipients = []
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
