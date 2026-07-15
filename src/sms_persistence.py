"""Capa de persistencia para SMS: conversaciones y mensajes.

Feature 27 — sms_persistence.
Provee operaciones CRUD para sms_conversations y sms_messages.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models import SmsConversation, SmsMessage, User

logger = logging.getLogger(__name__)


class SmsPersistenceError(Exception):
    """Error base de operaciones de persistencia SMS."""
    pass


class SmsPersistenceService:
    """Servicio de persistencia para SMS entrantes y salientes.

    Centraliza las operaciones CRUD sobre sms_conversations y sms_messages.
    """

    def __init__(self, db_session_factory) -> None:
        self._db_session_factory = db_session_factory

    # ------------------------------------------------------------------
    # Conversaciones
    # ------------------------------------------------------------------

    def create_conversation(
        self,
        peer_number: str,
        workflow_type: str,
        status: str = "active",
        metadata: dict | None = None,
        expires_at: datetime | None = None,
    ) -> SmsConversation:
        """Crea una nueva conversacion SMS."""
        if workflow_type not in ("emergency", "password_reset", "ai_query", "unknown"):
            raise SmsPersistenceError(f"workflow_type invalido: {workflow_type}")

        if status not in ("active", "completed", "expired", "cancelled", "failed", "archived"):
            raise SmsPersistenceError(f"status invalido: {status}")

        db: Session = self._db_session_factory()
        try:
            now = datetime.now(timezone.utc)
            conv = SmsConversation(
                peer_number=peer_number,
                workflow_type=workflow_type,
                status=status,
                started_at=now,
                last_activity=now,
                expires_at=expires_at,
                conv_metadata=metadata,
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)
            logger.debug(
                "Conversacion creada: id=%s, peer=%s, type=%s, status=%s",
                conv.id, peer_number, workflow_type, status,
            )
            return conv
        finally:
            db.close()

    def get_or_create_active_conversation(
        self, peer_number: str, workflow_type: str,
    ) -> SmsConversation:
        """Obtiene una conversacion activa existente o crea una nueva.

        Si existe una conversacion activa para ese peer+type, actualiza
        last_activity. Si no, crea una nueva.
        """
        db: Session = self._db_session_factory()
        try:
            conv = (
                db.query(SmsConversation)
                .filter(
                    SmsConversation.peer_number == peer_number,
                    SmsConversation.workflow_type == workflow_type,
                    SmsConversation.status == "active",
                )
                .order_by(SmsConversation.last_activity.desc())
                .first()
            )
            if conv:
                conv.last_activity = datetime.now(timezone.utc)
                db.commit()
                db.refresh(conv)
            else:
                db.close()
                return self.create_conversation(
                    peer_number=peer_number,
                    workflow_type=workflow_type,
                    status="active",
                )
            return conv
        finally:
            db.close()

    def update_conversation_status(
        self, conversation_id: int, status: str,
    ) -> None:
        """Actualiza el status de una conversacion."""
        if status not in ("active", "completed", "expired", "cancelled", "failed", "archived"):
            raise SmsPersistenceError(f"status invalido: {status}")

        db: Session = self._db_session_factory()
        try:
            conv = (
                db.query(SmsConversation)
                .filter(SmsConversation.id == conversation_id)
                .first()
            )
            if conv is None:
                raise SmsPersistenceError(
                    f"Conversacion {conversation_id} no encontrada"
                )
            conv.status = status
            conv.last_activity = datetime.now(timezone.utc)
            db.commit()
            logger.debug(
                "Conversacion %s actualizada a status=%s", conversation_id, status,
            )
        finally:
            db.close()

    def update_conversation_last_activity(
        self, conversation_id: int,
    ) -> None:
        """Actualiza el timestamp de ultima actividad de una conversacion."""
        db: Session = self._db_session_factory()
        try:
            conv = (
                db.query(SmsConversation)
                .filter(SmsConversation.id == conversation_id)
                .first()
            )
            if conv:
                conv.last_activity = datetime.now(timezone.utc)
                db.commit()
        finally:
            db.close()

    def get_active_conversation_by_peer(
        self, peer_number: str, workflow_type: str,
    ) -> SmsConversation | None:
        """Busca una conversacion activa por peer_number y workflow_type."""
        db: Session = self._db_session_factory()
        try:
            return (
                db.query(SmsConversation)
                .filter(
                    SmsConversation.peer_number == peer_number,
                    SmsConversation.workflow_type == workflow_type,
                    SmsConversation.status == "active",
                )
                .order_by(SmsConversation.last_activity.desc())
                .first()
            )
        finally:
            db.close()

    def get_conversation_by_request_id(
        self, request_id: int,
    ) -> SmsConversation | None:
        """Busca una conversacion por request_id almacenado en conv_metadata."""
        db: Session = self._db_session_factory()
        try:
            # request_id se almacena como conv_metadata JSON { "request_id": N }
            return (
                db.query(SmsConversation)
                .filter(
                    func.json_extract(SmsConversation.conv_metadata, "$.request_id")
                    == str(request_id)
                )
                .first()
            )
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Mensajes
    # ------------------------------------------------------------------

    def create_message(
        self,
        conversation_id: int,
        direction: str,
        peer_number: str,
        body: str,
        handler: str | None = None,
        status: str = "pending",
        modem_sms_id: int | None = None,
    ) -> SmsMessage:
        """Crea un nuevo registro de mensaje SMS."""
        if direction not in ("sent", "received"):
            raise SmsPersistenceError(f"direction invalido: {direction}")

        if status not in ("pending", "sending", "sent", "failed", "timeout", "delivered", "received"):
            raise SmsPersistenceError(f"status invalido: {status}")

        db: Session = self._db_session_factory()
        try:
            msg = SmsMessage(
                conversation_id=conversation_id,
                direction=direction,
                peer_number=peer_number,
                body=body,
                handler=handler,
                status=status,
                modem_sms_id=modem_sms_id,
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)

            # Actualizar last_activity de la conversacion
            conv = (
                db.query(SmsConversation)
                .filter(SmsConversation.id == conversation_id)
                .first()
            )
            if conv:
                conv.last_activity = datetime.now(timezone.utc)
                db.commit()

            logger.debug(
                "Mensaje creado: id=%s, conv=%s, dir=%s, status=%s, peer=%s",
                msg.id, conversation_id, direction, status, peer_number,
            )
            return msg
        finally:
            db.close()

    def update_message_status(
        self,
        message_id: int,
        status: str,
        error_message: str | None = None,
        modem_sms_id: int | None = None,
    ) -> None:
        """Actualiza el estado de un mensaje SMS."""
        if status not in ("pending", "sending", "sent", "failed", "timeout", "delivered", "received"):
            raise SmsPersistenceError(f"status invalido: {status}")

        db: Session = self._db_session_factory()
        try:
            msg = (
                db.query(SmsMessage)
                .filter(SmsMessage.id == message_id)
                .first()
            )
            if msg is None:
                raise SmsPersistenceError(f"Mensaje {message_id} no encontrado")
            msg.status = status
            if error_message is not None:
                msg.error_message = error_message
            if modem_sms_id is not None:
                msg.modem_sms_id = modem_sms_id
            db.commit()
            logger.debug(
                "Mensaje %s actualizado a status=%s, error=%s",
                message_id, status, error_message,
            )
        finally:
            db.close()

    def get_pending_outgoing_messages(
        self, limit: int = 10,
    ) -> list[SmsMessage]:
        """Recupera mensajes salientes pendientes de envio."""
        db: Session = self._db_session_factory()
        try:
            return (
                db.query(SmsMessage)
                .filter(
                    SmsMessage.direction == "sent",
                    SmsMessage.status == "pending",
                )
                .order_by(SmsMessage.created_at.asc())
                .limit(limit)
                .all()
            )
        finally:
            db.close()

    def message_exists_by_modem_id(self, modem_sms_id: int) -> bool:
        """Verifica si existe un mensaje con el modem_sms_id dado.

        Args:
            modem_sms_id: ID del SMS en el modem (modem_sms_id).

        Returns:
            True si existe al menos un mensaje con ese modem_sms_id.
        """
        db: Session = self._db_session_factory()
        try:
            # Solo mensajes ENVIADOS por nosotros (direction='sent'). El modem
            # recicla IDs — los SMS recibidos de otros numeros pueden reusar IDs
            # que ya existen en BD, pero NO son auto-generados.
            count = db.query(func.count(SmsMessage.id)).filter(
                SmsMessage.modem_sms_id == modem_sms_id,
                SmsMessage.direction == "sent",
            ).scalar()
            return count > 0
        finally:
            db.close()

    def get_message(self, message_id: int) -> SmsMessage | None:
        """Recupera un mensaje por su ID."""
        db: Session = self._db_session_factory()
        try:
            return (
                db.query(SmsMessage)
                .filter(SmsMessage.id == message_id)
                .first()
            )
        finally:
            db.close()

    def get_conversation(
        self, conversation_id: int,
    ) -> SmsConversation | None:
        """Recupera una conversacion por ID."""
        db: Session = self._db_session_factory()
        try:
            return (
                db.query(SmsConversation)
                .filter(SmsConversation.id == conversation_id)
                .first()
            )
        finally:
            db.close()

    def get_messages_by_conversation(
        self, conversation_id: int, limit: int = 50,
    ) -> list[SmsMessage]:
        """Recupera los mensajes de una conversacion, ordenados por fecha."""
        db: Session = self._db_session_factory()
        try:
            return (
                db.query(SmsMessage)
                .filter(SmsMessage.conversation_id == conversation_id)
                .order_by(SmsMessage.created_at.asc())
                .limit(limit)
                .all()
            )
        finally:
            db.close()

    def update_conversation_metadata(
        self, conversation_id: int, metadata: dict,
    ) -> None:
        """Actualiza la columna metadata de una conversacion."""
        db: Session = self._db_session_factory()
        try:
            conv = (
                db.query(SmsConversation)
                .filter(SmsConversation.id == conversation_id)
                .first()
            )
            if conv is None:
                raise SmsPersistenceError(
                    f"Conversacion {conversation_id} no encontrada"
                )
            conv.conv_metadata = metadata
            conv.last_activity = datetime.now(timezone.utc)
            db.commit()
            logger.debug(
                "Metadata de conversacion %s actualizada", conversation_id,
            )
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Usuarios (whitelist SMS)
    # ------------------------------------------------------------------

    def get_user_role_by_phone(self, phone: str) -> str | None:
        """Busca el rol de un usuario por su numero de telefono.

        Normaliza el numero antes de buscar: elimina prefijo +,
        espacios, y prueba con/sin codigo de pais (57 para Colombia).

        Args:
            phone: Numero de telefono del remitente (formato mmcli).

        Returns:
            El rol del usuario (str) o None si no se encuentra.
        """
        db: Session = self._db_session_factory()
        try:
            clean = phone.strip().lstrip("+").replace(" ", "")
            variants = [clean]
            if clean.startswith("57") and len(clean) > 2:
                variants.append(clean[2:])
            elif len(clean) == 10:
                variants.append("57" + clean)
            for v in variants:
                user = db.query(User).filter(User.phone == v).first()
                if user is not None:
                    return user.role
            return None
        finally:
            db.close()
