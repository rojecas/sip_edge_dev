"""Password reset via SMS: service, parser, endpoints, and models.

Feature #12 — Restablecimiento remoto de contrasena via SMS.
"""

import logging
import random
import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.auth import (
    create_reset_token,
    decode_reset_token,
    hash_password,
)
from src.database import get_db
from src.models import User

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Parser de comando SMS
# ------------------------------------------------------------------

_RESET_CMD_RE = re.compile(
    r"^\s*reset\s+password\s+(\S+)\s*$", re.IGNORECASE
)


def _parse_reset_command(text: str) -> str | None:
    """Extrae el username del patron 'reset password <username>'.

    Retorna el username si el texto coincide (case-insensitive),
    o None si no coincide.

    Ejemplos:
      'reset password juan'    → 'juan'
      '  RESET PASSWORD ana '  → 'ana'
      'hello world'            → None
    """
    match = _RESET_CMD_RE.match(text)
    if match:
        return match.group(1)
    return None


# ------------------------------------------------------------------
# Excepciones
# ------------------------------------------------------------------


class PasswordResetError(Exception):
    """Error base del modulo de reset de contrasena."""
    pass


class InvalidPinError(PasswordResetError):
    """PIN invalido o expirado."""
    pass


# ------------------------------------------------------------------
# Pydantic models
# ------------------------------------------------------------------


class VerifyResetPinRequest(BaseModel):
    username: str = Field(min_length=1)
    pin: str = Field(min_length=4, max_length=4)


class VerifyResetPinResponse(BaseModel):
    reset_token: str
    token_type: str = "bearer"


class CompleteResetRequest(BaseModel):
    reset_token: str = Field(min_length=1)
    new_password: str = Field(min_length=1)
    confirm_password: str = Field(min_length=1)


# ------------------------------------------------------------------
# PasswordResetService
# ------------------------------------------------------------------


class PasswordResetService:
    """Servicio de restablecimiento de contrasena via SMS.

    Gestiona la recepcion de comandos SMS 'reset password <username>',
    generacion de PIN de 4 digitos, verificacion, y cambio de contrasena.
    """

    def __init__(self, db_session_factory, sms_service) -> None:
        self._db_session_factory = db_session_factory
        self._sms_service = sms_service

    # ------------------------------------------------------------------
    # Handler para IncomingSmsDispatcher
    # ------------------------------------------------------------------

    def handle_incoming_sms(self, sender_phone: str, text: str) -> bool:
        """Procesa un SMS entrante como handler del dispatcher compartido.

        Retorna True si el SMS fue reconocido como comando 'reset password',
        False en caso contrario.
        """
        username = _parse_reset_command(text)
        if username is None:
            return False

        self.generate_and_send_pin(username, sender_phone)
        return True

    # ------------------------------------------------------------------
    # Generacion de PIN
    # ------------------------------------------------------------------

    def generate_and_send_pin(self, username: str, sender_phone: str) -> bool:
        """Genera un PIN de 4 digitos para el usuario y lo envia por SMS.

        Args:
            username: Nombre de usuario (case-insensitive).
            sender_phone: Numero del remitente del SMS (para respuestas de error).

        Returns:
            True si el PIN fue generado y enviado exitosamente.
            False si hubo un error (usuario no existe, sin telefono, etc.).
            En caso de error, se envia un SMS explicativo al remitente.
        """
        db: Session = self._db_session_factory()
        try:
            # Buscar usuario por username (case-insensitive)
            user = (
                db.query(User)
                .filter(User.username.ilike(username))
                .first()
            )

            if user is None:
                self._sms_service.send_sms(
                    sender_phone,
                    f"SIP-Edge: Usuario '{username}' no encontrado.",
                )
                logger.info(
                    "Password reset: usuario '%s' no encontrado, "
                    "solicitado por %s", username, sender_phone
                )
                return False

            if not user.phone or not user.phone.strip():
                self._sms_service.send_sms(
                    sender_phone,
                    f"SIP-Edge: El usuario '{user.username}' no tiene "
                    "telefono registrado. Debe realizar el cambio de "
                    "contrasena en sitio.",
                )
                logger.info(
                    "Password reset: usuario '%s' sin telefono, "
                    "solicitado por %s", username, sender_phone
                )
                return False

            # Generar PIN aleatorio de 4 digitos (1000-9999)
            pin = str(random.randint(1000, 9999))
            pin_hash = hash_password(pin)

            # Persistir en BD
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            user.reset_pin = pin_hash
            user.reset_pin_expires_at = expires_at
            user.force_password_change = True
            db.commit()

            # Enviar PIN por SMS al usuario
            sms_text = (
                f"SIP-Edge: Su PIN de restablecimiento es {pin}. "
                "Este PIN es valido por 1 hora y de un solo uso. "
                "Ingrese a la pantalla de login y use 'Olvido su "
                "contrasena' para cambiar su clave."
            )
            self._sms_service.send_sms(user.phone, sms_text)

            logger.info(
                "Password reset: PIN generado para '%s', "
                "enviado a %s, expira %s",
                user.username, user.phone,
                expires_at.isoformat(),
            )
            return True
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Verificacion de PIN
    # ------------------------------------------------------------------

    def verify_pin(self, username: str, pin: str) -> str:
        """Verifica el PIN y retorna un reset_token JWT.

        Args:
            username: Nombre de usuario.
            pin: PIN de 4 digitos en texto plano.

        Returns:
            reset_token JWT valido por 5 minutos.

        Raises:
            InvalidPinError: Si el username no existe, el PIN es invalido,
                             el PIN ya fue usado, o el PIN expiro.
        """
        db: Session = self._db_session_factory()
        try:
            user = (
                db.query(User)
                .filter(User.username.ilike(username))
                .first()
            )
            if user is None:
                raise InvalidPinError("Invalid username or PIN")

            if user.reset_pin is None:
                raise InvalidPinError("Invalid username or PIN")

            if user.reset_pin_expires_at is None:
                raise InvalidPinError("Invalid username or PIN")

            # Verificar expiracion
            now = datetime.now(timezone.utc)
            if user.reset_pin_expires_at.tzinfo is None:
                expires = user.reset_pin_expires_at.replace(tzinfo=timezone.utc)
            else:
                expires = user.reset_pin_expires_at
            if now >= expires:
                raise InvalidPinError("Invalid username or PIN")

            # Verificar PIN contra hash
            from src.auth import verify_password
            if not verify_password(pin, user.reset_pin):
                raise InvalidPinError("Invalid username or PIN")

            # Invalidar PIN (single-use)
            user.reset_pin = None
            user.reset_pin_expires_at = None
            db.commit()

            # Emitir reset_token
            token = create_reset_token(user.id)
            logger.info(
                "Password reset: PIN verificado para '%s', "
                "reset_token emitido", user.username,
            )
            return token
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Cambio de contrasena
    # ------------------------------------------------------------------

    def complete_reset(
        self, reset_token: str, new_password: str, confirm_password: str
    ) -> None:
        """Completa el restablecimiento cambiando la contrasena.

        Args:
            reset_token: JWT emitido por verify_pin.
            new_password: Nueva contrasena (min 1 caracter).
            confirm_password: Confirmacion de la nueva contrasena.

        Raises:
            HTTPException 401: Si el token es invalido o expiro.
            HTTPException 422: Si las contrasenas no coinciden.
        """
        if new_password != confirm_password:
            raise HTTPException(
                status_code=422,
                detail="Passwords do not match",
            )

        # Decodificar reset_token
        try:
            payload = decode_reset_token(reset_token)
        except Exception:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired reset token",
            )

        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired reset token",
            )

        user_id = int(user_id_str)

        db: Session = self._db_session_factory()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user is None:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or expired reset token",
                )

            # Actualizar contrasena
            user.password_hash = hash_password(new_password)
            user.force_password_change = False
            user.reset_pin = None
            user.reset_pin_expires_at = None
            db.commit()

            logger.info(
                "Password reset: contrasena cambiada para user_id=%s",
                user_id,
            )
        finally:
            db.close()


# ------------------------------------------------------------------
# API Router y endpoints
# ------------------------------------------------------------------


password_reset_router = APIRouter(prefix="/api/auth", tags=["auth"])


def _get_password_reset_service(request):
    """Dependencia: obtiene PasswordResetService del app state."""
    return request.app.state.password_reset_service


@password_reset_router.post(
    "/verify-reset-pin",
    response_model=VerifyResetPinResponse,
)
def verify_reset_pin(
    body: VerifyResetPinRequest,
    db: Session = Depends(get_db),
):
    """Verifica el PIN de restablecimiento y emite un reset_token."""
    import src.database as _db

    # Crear servicio con la sesion actual
    svc = PasswordResetService(
        db_session_factory=_db.SessionLocal,
        sms_service=None,  # No se necesita SMS para verificar
    )

    try:
        reset_token = svc.verify_pin(body.username, body.pin)
    except InvalidPinError:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or PIN",
        )

    return VerifyResetPinResponse(reset_token=reset_token)


@password_reset_router.post("/complete-reset")
def complete_reset(
    body: CompleteResetRequest,
    db: Session = Depends(get_db),
):
    """Completa el restablecimiento de contrasena."""
    import src.database as _db

    svc = PasswordResetService(
        db_session_factory=_db.SessionLocal,
        sms_service=None,
    )

    svc.complete_reset(body.reset_token, body.new_password, body.confirm_password)
    return {"message": "Password updated successfully"}
