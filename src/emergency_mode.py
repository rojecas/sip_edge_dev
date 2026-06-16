"""Modulo de modo manual de emergencia.

Gestiona solicitudes desde el kiosco, comandos SMS entrantes,
activacion/desactivacion/extension del modo manual, y auditoria completa
en emergency_mode_log.
"""

import asyncio
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.auth import check_inactivity, get_current_user
from src.database import get_db
from src.models import EmergencyModeLog, User

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# SMS Parser
# ------------------------------------------------------------------

_SMS_MANUAL_ON_RE = re.compile(
    r"^\s*manual\s+on\s*$", re.IGNORECASE
)
_SMS_MANUAL_ON_H_RE = re.compile(
    r"^\s*manual\s+on\s+(\d+)\s*h\s*$", re.IGNORECASE
)
_SMS_MANUAL_ON_M_RE = re.compile(
    r"^\s*manual\s+on\s+(\d+)\s*m\s*$", re.IGNORECASE
)
_SMS_MANUAL_ON_EXT_H_RE = re.compile(
    r"^\s*manual\s+on\s+ext\s+(\d+)\s*h\s*$", re.IGNORECASE
)
_SMS_MANUAL_ON_EXT_M_RE = re.compile(
    r"^\s*manual\s+on\s+ext\s+(\d+)\s*m\s*$", re.IGNORECASE
)
_SMS_MANUAL_OFF_RE = re.compile(
    r"^\s*manual\s+off\s*$", re.IGNORECASE
)

# Regex para parsear salida de mmcli
_SMS_ID_RE = re.compile(r"/org/freedesktop/ModemManager1/SMS/(\d+)")


@dataclass(frozen=True)
class ParsedSmsCommand:
    """Resultado del parsing de un SMS de emergencia."""

    action: str  # "activate", "extend", "deactivate", "invalid"
    duration_minutes: int | None = None
    raw_text: str = ""


def parse_emergency_sms(text: str) -> ParsedSmsCommand:
    """Analiza el texto de un SMS y determina el comando.

    Patrones soportados (case-insensitive):
      - "manual on"                    → activate, 1440 min (24h)
      - "manual on <N>h"               → activate, N*60 min
      - "manual on <N>m"               → activate, N min
      - "manual on ext <N>h"           → extend, N*60 min
      - "manual on ext <N>m"           → extend, N min
      - "manual off"                   → deactivate
      - cualquier otro                 → invalid
    """
    trimmed = text.strip()

    match = _SMS_MANUAL_ON_H_RE.match(trimmed)
    if match:
        hours = int(match.group(1))
        if hours <= 0:
            return ParsedSmsCommand(action="invalid", raw_text=trimmed)
        return ParsedSmsCommand(action="activate", duration_minutes=hours * 60, raw_text=trimmed)

    match = _SMS_MANUAL_ON_M_RE.match(trimmed)
    if match:
        minutes = int(match.group(1))
        if minutes <= 0:
            return ParsedSmsCommand(action="invalid", raw_text=trimmed)
        return ParsedSmsCommand(action="activate", duration_minutes=minutes, raw_text=trimmed)

    match = _SMS_MANUAL_ON_EXT_H_RE.match(trimmed)
    if match:
        hours = int(match.group(1))
        if hours <= 0:
            return ParsedSmsCommand(action="invalid", raw_text=trimmed)
        return ParsedSmsCommand(action="extend", duration_minutes=hours * 60, raw_text=trimmed)

    match = _SMS_MANUAL_ON_EXT_M_RE.match(trimmed)
    if match:
        minutes = int(match.group(1))
        if minutes <= 0:
            return ParsedSmsCommand(action="invalid", raw_text=trimmed)
        return ParsedSmsCommand(action="extend", duration_minutes=minutes, raw_text=trimmed)

    if _SMS_MANUAL_ON_RE.match(trimmed):
        return ParsedSmsCommand(action="activate", duration_minutes=1440, raw_text=trimmed)

    if _SMS_MANUAL_OFF_RE.match(trimmed):
        return ParsedSmsCommand(action="deactivate", raw_text=trimmed)

    return ParsedSmsCommand(action="invalid", raw_text=trimmed)


# ------------------------------------------------------------------
# Excepciones
# ------------------------------------------------------------------


class EmergencyModeError(Exception):
    """Error base del modulo de emergencia."""
    pass


class InvalidSmsCommandError(EmergencyModeError):
    """Se lanza cuando un comando SMS no es reconocido."""
    pass


class UnauthorizedSenderError(EmergencyModeError):
    """Se lanza cuando el emisor del SMS no es un admin registrado."""
    pass


# ------------------------------------------------------------------
# Pydantic models
# ------------------------------------------------------------------


class EmergencyRequest(BaseModel):
    supervisor_id: int = Field(gt=0)
    motivo: str = Field(min_length=1)


# ------------------------------------------------------------------
# EmergencyModeService
# ------------------------------------------------------------------


class EmergencyModeService:
    """Servicio central del modo manual de emergencia.

    Gestiona solicitudes, autorizaciones por SMS, estado activo/inactivo,
    persistencia en BD y tareas en segundo plano (polling SMS, expiry).
    """

    DEFAULT_DURATION_MINUTES = 1440  # 24 horas

    def __init__(
        self,
        db_session_factory,
        sms_service,
        modem_index: int = 0,
        dev_mode: bool = False,
    ) -> None:
        self._db_session_factory = db_session_factory
        self._sms_service = sms_service
        self._modem_index = modem_index
        self._dev_mode = dev_mode

        self._active: bool = False
        self._expires_at: datetime | None = None
        self._active_record_id: int | None = None

        self._sms_poll_task: asyncio.Task | None = None
        self._expiry_check_task: asyncio.Task | None = None

        # Cola interna para simulacion en dev mode
        self._dev_incoming_queue: list[tuple[str, str]] = []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Inicia las tareas en segundo plano (polling SMS + expiry checker)."""
        if self._expiry_check_task is None or self._expiry_check_task.done():
            self._expiry_check_task = asyncio.create_task(self._check_expiry_loop())
            logger.info("EmergencyModeService: expiry checker started")

        if self._sms_poll_task is None or self._sms_poll_task.done():
            self._sms_poll_task = asyncio.create_task(self._poll_incoming_sms())
            logger.info("EmergencyModeService: SMS polling started")

    async def stop(self) -> None:
        """Cancela las tareas en segundo plano."""
        for task in (self._sms_poll_task, self._expiry_check_task):
            if task is not None and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self._sms_poll_task = None
        self._expiry_check_task = None
        logger.info("EmergencyModeService: background tasks stopped")

    # ------------------------------------------------------------------
    # Dev mode: simulacion de SMS entrantes
    # ------------------------------------------------------------------

    def enqueue_incoming_sms(self, sender_phone: str, text: str) -> None:
        """Encola un SMS entrante simulado (dev mode)."""
        self._dev_incoming_queue.append((sender_phone, text))

    # ------------------------------------------------------------------
    # Solicitudes desde kiosco
    # ------------------------------------------------------------------

    def create_request(
        self, analyst_id: int, supervisor_id: int, motivo: str
    ) -> int:
        """Crea una solicitud en BD y envia SMS al supervisor.

        Returns:
            request_id (int) de la solicitud creada.

        Raises:
            ValueError: Si supervisor_id no corresponde a un admin activo.
            ValueError: Si motivo esta vacio o solo contiene espacios.
        """
        motivo = motivo.strip()
        if not motivo:
            raise ValueError("El motivo es obligatorio")

        db: Session = self._db_session_factory()
        try:
            supervisor = (
                db.query(User)
                .filter(
                    User.id == supervisor_id,
                    User.role == "admin",
                    User.is_active == True,
                )
                .first()
            )
            if supervisor is None:
                raise ValueError("Supervisor no valido: no es admin activo")

            analyst = db.query(User).filter(User.id == analyst_id).first()
            analyst_name = (
                analyst.full_name if analyst else str(analyst_id)
            )

            log_entry = EmergencyModeLog(
                status="pending",
                analyst_id=analyst_id,
                supervisor_id=supervisor_id,
                motivo=motivo,
                cmd_source="ui",
                cmd_raw="ui_request",
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            request_id = log_entry.id

            # Enviar SMS al supervisor
            if supervisor.phone:
                sms_text = (
                    f"SIP-Edge: {analyst_name} solicita activar modo manual. "
                    f"Motivo: {motivo}. "
                    f"Responda 'manual on' para activar (24h), "
                    f"'manual on Xh/Xm' para duracion especifica, "
                    f"o 'manual off' para denegar."
                )
                self._sms_service.send_sms(supervisor.phone, sms_text)

            return request_id
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------

    def is_active(self) -> bool:
        """Retorna True si el modo manual esta actualmente activo."""
        return self._active

    def get_status(self) -> dict:
        """Retorna el estado actual del modo manual."""
        remaining = None
        if self._active and self._expires_at is not None:
            now = datetime.now(timezone.utc)
            remaining = max(0, int((self._expires_at - now).total_seconds()))

        return {
            "active": self._active,
            "expires_at": (
                self._expires_at.isoformat() if self._expires_at else None
            ),
            "remaining_seconds": remaining,
            "active_record_id": self._active_record_id,
        }

    # ------------------------------------------------------------------
    # Activacion / desactivacion programatica
    # ------------------------------------------------------------------

    def activate(
        self,
        request_id: int | None,
        supervisor_id: int,
        duration_minutes: int,
        cmd_raw: str,
        cmd_source: str,
        sender_phone: str = "",
    ) -> None:
        """Activa el modo manual.

        Args:
            request_id: ID de solicitud si proviene de una, None si es directa.
            supervisor_id: ID del admin que autoriza.
            duration_minutes: Duracion en minutos.
            cmd_raw: Texto crudo del comando que origino la activacion.
            cmd_source: "sms" o "ui".
            sender_phone: Numero de telefono del remitente (para SMS).
        """
        db: Session = self._db_session_factory()
        try:
            # Validar que el supervisor existe y es admin
            supervisor = (
                db.query(User)
                .filter(User.id == supervisor_id, User.role == "admin")
                .first()
            )
            if supervisor is None:
                raise EmergencyModeError(
                    f"Usuario {supervisor_id} no es admin valido"
                )

            now = datetime.now(timezone.utc)
            expires_at = datetime.fromtimestamp(
                now.timestamp() + duration_minutes * 60, tz=timezone.utc
            )

            # Si ya habia un modo activo, marcarlo como cancelled (R12: reinicio)
            if self._active and self._active_record_id is not None:
                prev_record = db.query(EmergencyModeLog).filter(
                    EmergencyModeLog.id == self._active_record_id
                ).first()
                if prev_record:
                    prev_record.status = "cancelled"
                    prev_record.updated_at = now

            # Cancelar solicitudes pending al mismo supervisor (R5)
            pending_requests = (
                db.query(EmergencyModeLog)
                .filter(
                    EmergencyModeLog.supervisor_id == supervisor_id,
                    EmergencyModeLog.status == "pending",
                )
                .all()
            )
            for req in pending_requests:
                req.status = "cancelled"
                req.updated_at = now

            # Si hay un request_id, actualizarlo para vincular
            if request_id is not None:
                orig_request = db.query(EmergencyModeLog).filter(
                    EmergencyModeLog.id == request_id
                ).first()
                if orig_request:
                    orig_request.status = "cancelled"
                    orig_request.updated_at = now

            # Crear registro de activacion
            duration_seconds = duration_minutes * 60
            activation = EmergencyModeLog(
                request_id=request_id,
                status="active",
                supervisor_id=supervisor_id,
                started_at=now,
                duration_seconds=duration_seconds,
                expires_at=expires_at,
                cmd_source=cmd_source,
                cmd_raw=cmd_raw,
                sender_phone=sender_phone,
            )
            db.add(activation)
            db.commit()
            db.refresh(activation)

            self._active = True
            self._expires_at = expires_at
            self._active_record_id = activation.id

            logger.info(
                "Modo manual ACTIVADO por supervisor %s (record %s), "
                "expira %s, duracion %s min",
                supervisor_id,
                activation.id,
                expires_at.isoformat(),
                duration_minutes,
            )
        finally:
            db.close()

    def extend(
        self, supervisor_id: int, extra_minutes: int, cmd_raw: str,
        sender_phone: str = "",
    ) -> None:
        """Extiende el modo manual activo sumando minutos al expires_at actual.

        Raises:
            EmergencyModeError: Si el modo manual no esta activo.
        """
        if not self._active or self._active_record_id is None:
            raise EmergencyModeError(
                "No se puede extender: el modo manual no esta activo"
            )

        db: Session = self._db_session_factory()
        try:
            now = datetime.now(timezone.utc)

            new_expires = self._expires_at
            if new_expires < now:
                new_expires = now
            new_expires = datetime.fromtimestamp(
                new_expires.timestamp() + extra_minutes * 60, tz=timezone.utc
            )

            # Registrar extension
            ext_log = EmergencyModeLog(
                request_id=self._active_record_id,
                status="extended",
                supervisor_id=supervisor_id,
                duration_seconds=extra_minutes * 60,
                expires_at=new_expires,
                cmd_source="sms",
                cmd_raw=cmd_raw,
                sender_phone=sender_phone,
            )
            db.add(ext_log)

            # Actualizar registro activo con nueva expiracion
            active_record = db.query(EmergencyModeLog).filter(
                EmergencyModeLog.id == self._active_record_id
            ).first()
            if active_record:
                active_record.expires_at = new_expires
                active_record.updated_at = now

            db.commit()

            self._expires_at = new_expires
            logger.info(
                "Modo manual EXTENDIDO por supervisor %s: +%s min, "
                "nueva expiracion %s",
                supervisor_id,
                extra_minutes,
                new_expires.isoformat(),
            )
        finally:
            db.close()

    def deactivate(
        self,
        supervisor_id: int | None,
        cmd_raw: str,
        sender_phone: str = "",
        reason: str = "manual_off",
    ) -> None:
        """Desactiva el modo manual inmediatamente.

        Args:
            supervisor_id: ID del admin (None si es por expiracion automatica).
            cmd_raw: Texto crudo del comando o "auto_expire".
            sender_phone: Numero de telefono del remitente (para SMS).
            reason: "manual_off" o "auto_expire".
        """
        if not self._active:
            return

        db: Session = self._db_session_factory()
        try:
            now = datetime.now(timezone.utc)

            # Marcar registro activo como cancelled/expired
            new_status = "expired" if reason == "auto_expire" else "cancelled"
            active_record = db.query(EmergencyModeLog).filter(
                EmergencyModeLog.id == self._active_record_id
            ).first()
            if active_record:
                active_record.status = new_status
                active_record.updated_at = now

            # Insertar registro de cierre
            close_log = EmergencyModeLog(
                request_id=self._active_record_id,
                status=new_status,
                supervisor_id=supervisor_id,
                cmd_source="sms",
                cmd_raw=cmd_raw,
                sender_phone=sender_phone,
            )
            db.add(close_log)
            db.commit()

            self._active = False
            self._expires_at = None
            self._active_record_id = None

            logger.info(
                "Modo manual DESACTIVADO: reason=%s, supervisor=%s",
                reason,
                supervisor_id,
            )
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Restauracion desde BD
    # ------------------------------------------------------------------

    def restore_from_db(self) -> None:
        """Restaura el estado del modo manual desde la BD (R14).

        Busca el registro mas reciente con status='active' y expires_at futuro,
        y restablece self._active, self._expires_at y self._active_record_id.
        Si expires_at ya expiro, actualiza el registro a status='expired'.
        """
        db: Session = self._db_session_factory()
        try:
            latest_active = (
                db.query(EmergencyModeLog)
                .filter(EmergencyModeLog.status == "active")
                .order_by(EmergencyModeLog.created_at.desc())
                .first()
            )
            if latest_active is None:
                logger.info("restore_from_db: no active record found")
                return

            now = datetime.now(timezone.utc)
            # Make expires_at timezone-aware if stored as naive (SQLite quirk)
            expires_at_value = latest_active.expires_at
            if expires_at_value is not None and expires_at_value.tzinfo is None:
                expires_at_value = expires_at_value.replace(tzinfo=timezone.utc)

            if expires_at_value is not None and expires_at_value > now:
                self._active = True
                self._expires_at = expires_at_value
                self._active_record_id = latest_active.id
                logger.info(
                    "restore_from_db: modo manual restaurado, "
                    "expires_at=%s, record_id=%s",
                    expires_at_value.isoformat(),
                    latest_active.id,
                )
            else:
                # Ya expiro: marcar como expired
                latest_active.status = "expired"
                latest_active.updated_at = now
                expired_log = EmergencyModeLog(
                    request_id=latest_active.id,
                    status="expired",
                    cmd_source="sms",
                    cmd_raw="auto_expire_restore",
                )
                db.add(expired_log)
                db.commit()
                logger.info(
                    "restore_from_db: registro %s expirado, marcado como expired",
                    latest_active.id,
                )
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Procesamiento interno de SMS
    # ------------------------------------------------------------------

    def process_incoming_sms(self, sender_phone: str, text: str) -> None:
        """Procesa un SMS entrante: parsea, verifica emisor, ejecuta comando.

        Args:
            sender_phone: Numero de telefono del remitente.
            text: Texto completo del SMS.
        """
        db: Session = self._db_session_factory()
        try:
            # Buscar usuario por numero de telefono (R17)
            user = (
                db.query(User)
                .filter(User.phone == sender_phone, User.is_active == True)
                .first()
            )

            if user is None or user.role != "admin":
                # R17: Emisor no autorizado
                invalid_log = EmergencyModeLog(
                    status="invalid",
                    cmd_source="sms",
                    cmd_raw=f"Unauthorized sender: {sender_phone}",
                    sender_phone=sender_phone,
                )
                db.add(invalid_log)
                db.commit()
                logger.warning(
                    "SMS de emisor no autorizado o no admin: %s", sender_phone
                )
                # Responder al remitente
                self._sms_service.send_sms(
                    sender_phone,
                    "SIP-Edge: Comando no autorizado. Solo administradores "
                    "registrados pueden controlar el modo manual.",
                )
                return

            supervisor_id = user.id

            # Parsear el comando (R16)
            parsed = parse_emergency_sms(text)

            if parsed.action == "invalid":
                # R16: Comando invalido
                invalid_log = EmergencyModeLog(
                    status="invalid",
                    supervisor_id=supervisor_id,
                    cmd_source="sms",
                    cmd_raw=parsed.raw_text,
                    sender_phone=sender_phone,
                )
                db.add(invalid_log)
                db.commit()
                # Responder con comandos validos
                self._sms_service.send_sms(
                    sender_phone,
                    "SIP-Edge: Comando no valido. Comandos aceptados: "
                    "'manual on', 'manual on Xh/Xm', "
                    "'manual on EXT Xh/Xm', 'manual off'.",
                )
                return

            if parsed.action == "activate":
                self.activate(
                    request_id=None,
                    supervisor_id=supervisor_id,
                    duration_minutes=parsed.duration_minutes,
                    cmd_raw=parsed.raw_text,
                    cmd_source="sms",
                    sender_phone=sender_phone,
                )

            elif parsed.action == "extend":
                # R19: Si no esta activo, rechazar extension
                if not self._active:
                    invalid_log = EmergencyModeLog(
                        status="invalid",
                        supervisor_id=supervisor_id,
                        cmd_source="sms",
                        cmd_raw=parsed.raw_text,
                        sender_phone=sender_phone,
                    )
                    db.add(invalid_log)
                    db.commit()
                    self._sms_service.send_sms(
                        sender_phone,
                        "SIP-Edge: El modo manual no esta activo. "
                        "Use 'manual on' o 'manual on Xh/Xm' para activarlo.",
                    )
                    return
                self.extend(
                    supervisor_id=supervisor_id,
                    extra_minutes=parsed.duration_minutes,
                    cmd_raw=parsed.raw_text,
                    sender_phone=sender_phone,
                )

            elif parsed.action == "deactivate":
                if self._active:
                    self.deactivate(
                        supervisor_id=supervisor_id,
                        cmd_raw=parsed.raw_text,
                        sender_phone=sender_phone,
                        reason="manual_off",
                    )
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Tareas asyncio
    # ------------------------------------------------------------------

    async def _check_expiry_loop(self) -> None:
        """Tarea asyncio que cada 30 segundos verifica expiracion (R10)."""
        while True:
            try:
                if self._active and self._expires_at is not None:
                    now = datetime.now(timezone.utc)
                    if now >= self._expires_at:
                        logger.info(
                            "Modo manual expirado automaticamente "
                            "(expires_at=%s, now=%s)",
                            self._expires_at.isoformat(),
                            now.isoformat(),
                        )
                        self.deactivate(
                            supervisor_id=None,
                            cmd_raw="auto_expire",
                            reason="auto_expire",
                        )
            except asyncio.CancelledError:
                logger.info("Expiry checker cancelled")
                break
            except Exception:
                logger.exception("Error in expiry checker loop")
            try:
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                logger.info("Expiry checker cancelled during sleep")
                break

    async def _poll_incoming_sms(self) -> None:
        """Tarea asyncio que cada 15 segundos consulta SMS entrantes via mmcli."""
        while True:
            try:
                if self._dev_mode:
                    # En desarrollo: consumir de la cola interna
                    while self._dev_incoming_queue:
                        phone, text = self._dev_incoming_queue.pop(0)
                        self.process_incoming_sms(phone, text)
                else:
                    await self._poll_mmcli_sms()
            except asyncio.CancelledError:
                logger.info("SMS polling cancelled")
                break
            except Exception:
                logger.exception("Error in SMS polling loop")
            try:
                await asyncio.sleep(15)
            except asyncio.CancelledError:
                logger.info("SMS polling cancelled during sleep")
                break

    async def _poll_mmcli_sms(self) -> None:
        """Ejecuta mmcli para listar y procesar SMS entrantes."""
        try:
            # 1. Listar SMS
            result = await asyncio.to_thread(
                subprocess.run,
                [
                    "mmcli", "-m", str(self._modem_index),
                    "--messaging-list-sms",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                logger.warning(
                    "mmcli list-sms failed: %s",
                    (result.stderr or "").strip(),
                )
                return

            # 2. Extraer IDs
            sms_ids = _SMS_ID_RE.findall(result.stdout)
            for sms_id in sms_ids:
                try:
                    read = await asyncio.to_thread(
                        subprocess.run,
                        ["mmcli", "-s", sms_id],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if read.returncode != 0:
                        continue

                    sender = _extract_sms_field(read.stdout, "number")
                    text = _extract_sms_field(read.stdout, "text")
                    if sender and text:
                        self.process_incoming_sms(sender, text)

                    # 3. Eliminar SMS procesado
                    await asyncio.to_thread(
                        subprocess.run,
                        ["mmcli", "-s", sms_id, "--delete"],
                        capture_output=True,
                        timeout=10,
                    )
                except Exception:
                    logger.exception(
                        "Error processing SMS id=%s", sms_id
                    )
        except subprocess.TimeoutExpired:
            logger.warning("mmcli SMS polling timed out")
        except FileNotFoundError:
            if not self._dev_mode:
                logger.warning("mmcli not found, SMS polling disabled")


def _extract_sms_field(mmcli_output: str, field: str) -> str | None:
    """Extrae el valor de un campo de la salida de mmcli -s <id>."""
    pattern = re.compile(
        r"^\s*" + re.escape(field) + r"\s*\|\s*(.+?)(?:\s*\[.*?\])?\s*$",
        re.MULTILINE,
    )
    match = pattern.search(mmcli_output)
    if match:
        return match.group(1).strip()
    # Fallback: formato sin pipes
    pattern2 = re.compile(
        r"^\s*" + re.escape(field) + r"\s*:\s*(.+)$", re.MULTILINE
    )
    match2 = pattern2.search(mmcli_output)
    if match2:
        return match2.group(1).strip()
    return None


# ------------------------------------------------------------------
# API Router
# ------------------------------------------------------------------


emergency_router = APIRouter(prefix="/api/emergency", tags=["emergency"])


@emergency_router.get("/admins")
def list_admin_users(
    request: Request,
    _auth: dict = Depends(check_inactivity),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Retorna lista de usuarios con rol admin y is_active=true.

    Cada elemento incluye: id, full_name, document.
    Accesible por: cualquier rol autenticado.
    """
    users = (
        db.query(User)
        .filter(User.role == "admin", User.is_active == True)
        .all()
    )
    return [
        {
            "id": u.id,
            "full_name": u.full_name,
            "document": u.document,
        }
        for u in users
    ]


@emergency_router.post("/request")
def create_emergency_request(
    body: EmergencyRequest,
    request: Request,
    _auth: dict = Depends(check_inactivity),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Crea una solicitud de modo manual.

    Body: { supervisor_id: int, motivo: str }
    El analista actual se obtiene del token JWT.

    Retorna: { request_id: int, message: str }
    """
    svc: EmergencyModeService = request.app.state.emergency_service
    try:
        request_id = svc.create_request(
            analyst_id=current_user["user_id"],
            supervisor_id=body.supervisor_id,
            motivo=body.motivo,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return {
        "request_id": request_id,
        "message": "Solicitud enviada. Esperando autorizacion por SMS.",
    }


@emergency_router.get("/status")
def get_emergency_status(
    request: Request,
    _auth: dict = Depends(check_inactivity),
) -> dict:
    """Retorna el estado actual del modo manual.

    No requiere rol especifico (cualquier usuario autenticado puede consultar).

    Retorna:
    {
        "active": bool,
        "expires_at": str | None,
        "remaining_seconds": int | None,
        "active_record_id": int | None,
    }
    """
    svc: EmergencyModeService = request.app.state.emergency_service
    return svc.get_status()
