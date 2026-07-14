"""Servicio de gestion de contexto multiturno para consultas AI via SMS.

Feature 28 — ai_multi_turn.
Maneja el historial conversacional, tool logging, deteccion de despedida,
y archivado de conversaciones antiguas.
"""

import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from src.models import SmsAiToolLog, SmsConversation
from src.sms_persistence import SmsPersistenceService

logger = logging.getLogger(__name__)


class AiMultiTurnError(Exception):
    """Error base del servicio de conversacion multiturno AI."""
    pass


FAREWELL_PATTERNS: list[str] = [
    "gracias",
    "bye",
    "adios",
    "chao",
    "eso es todo",
    "es todo",
    "nada mas",
    "no mas",
    "terminamos",
    "suficiente",
    "ok gracias",
]

DEFAULT_MAX_EXCHANGES = 10


class AiMultiTurnService:
    """Servicio de gestion de contexto multiturno para consultas AI.

    Responsable de:
    - Obtener/crear conversaciones ai_query.
    - Gestionar historial de mensajes (message_history en metadata).
    - Registrar tool_calls en sms_ai_tool_log.
    - Detectar despedidas del usuario.
    - Archivar conversaciones antiguas.
    """

    def __init__(
        self,
        db_session_factory,
        persistence: SmsPersistenceService,
    ) -> None:
        self._db_session_factory = db_session_factory
        self._persistence = persistence

    # ------------------------------------------------------------------
    # Conversacion
    # ------------------------------------------------------------------

    def get_or_create_ai_conversation(
        self,
        peer_number: str,
        conversation_id: int | None = None,
    ) -> SmsConversation:
        """Retorna la conversacion ai_query activa para peer_number.

        Si conversation_id es provisto (por el dispatcher):
          - Recupera la conversacion por ID.
          - Si workflow_type == 'unknown': actualiza a 'ai_query' y retorna.
          - Si workflow_type == 'ai_query' y status == 'active': reutiliza.
          - Si status != 'active': crea nueva.

        Si conversation_id NO es provisto (modo legacy):
          - Busca conversacion ai_query activa por peer_number.
          - Si existe, reutiliza.
          - Si no existe, crea nueva.
        """
        if conversation_id is not None:
            conv = self._persistence.get_conversation(conversation_id)
            if conv is not None:
                # Caso: dispatcher creo conversacion como 'unknown'
                if conv.workflow_type == "unknown":
                    self._update_conversation_workflow_type(
                        conv.id, "ai_query", "active",
                    )
                    # Re-leer despues de update
                    return self._persistence.get_conversation(conv.id)

                # Caso: conversacion ai_query activa -> reutilizar
                if conv.workflow_type == "ai_query" and conv.status == "active":
                    return conv

                # Caso: conversacion no activa -> crear nueva
                return self._persistence.create_conversation(
                    peer_number=peer_number,
                    workflow_type="ai_query",
                    status="active",
                )

        # Modo legacy: sin conversation_id
        existing = self._persistence.get_active_conversation_by_peer(
            peer_number, "ai_query",
        )
        if existing is not None and existing.status == "active":
            return existing

        return self._persistence.create_conversation(
            peer_number=peer_number,
            workflow_type="ai_query",
            status="active",
        )

    def _update_conversation_workflow_type(
        self, conversation_id: int, workflow_type: str, status: str,
    ) -> None:
        """Actualiza el workflow_type y status de una conversacion directamente."""
        db: Session = self._db_session_factory()
        try:
            conv = (
                db.query(SmsConversation)
                .filter(SmsConversation.id == conversation_id)
                .first()
            )
            if conv is not None:
                conv.workflow_type = workflow_type
                conv.status = status
                conv.last_activity = datetime.now(timezone.utc)
                db.commit()
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Historial de mensajes
    # ------------------------------------------------------------------

    def get_message_history(
        self, conversation: SmsConversation,
    ) -> list[dict]:
        """Retorna message_history desde metadata como lista de dicts.

        Formato: [{"user": "...", "assistant": "..."}, ...].
        Si no hay metadata o no contiene message_history, retorna [].
        """
        meta = conversation.conv_metadata or {}
        history = meta.get("message_history", [])
        if not isinstance(history, list):
            return []
        return history

    def build_llm_messages(
        self,
        message_history: list[dict],
        new_user_text: str,
        system_prompt: str,
    ) -> list[dict]:
        """Construye el arreglo de mensajes para el LLM.

        Combina el system prompt, los exchanges del historial
        (user + assistant), y el nuevo mensaje del usuario.
        """
        messages: list[dict] = [
            {"role": "system", "content": system_prompt},
        ]

        for exchange in message_history:
            user_text = exchange.get("user", "")
            assistant_text = exchange.get("assistant", "")
            if user_text:
                messages.append({"role": "user", "content": user_text})
            if assistant_text:
                messages.append({"role": "assistant", "content": assistant_text})

        messages.append({"role": "user", "content": new_user_text})
        return messages

    def append_exchange(
        self,
        conversation_id: int,
        message_history: list[dict],
        user_text: str,
        assistant_text: str,
        max_exchanges: int = DEFAULT_MAX_EXCHANGES,
    ) -> None:
        """Agrega un exchange al historial, aplicando FIFO si se supera el limite.

        Si message_history ya tiene max_exchanges exchanges, elimina el mas
        antiguo antes de agregar el nuevo.  Persiste el metadata actualizado.
        """
        # FIFO: si ya alcanzo el limite, eliminar el mas antiguo
        if len(message_history) >= max_exchanges:
            message_history.pop(0)

        message_history.append({
            "user": user_text,
            "assistant": assistant_text,
        })

        # Persistir el metadata actualizado
        conv = self._persistence.get_conversation(conversation_id)
        if conv is None:
            raise AiMultiTurnError(
                f"Conversacion {conversation_id} no encontrada al guardar exchange"
            )

        new_meta = dict(conv.conv_metadata or {})
        new_meta["message_history"] = message_history
        self._persistence.update_conversation_metadata(conversation_id, new_meta)

    def get_max_exchanges(self, conversation: SmsConversation) -> int:
        """Lee max_exchanges de metadata o retorna el default (10)."""
        meta = conversation.conv_metadata or {}
        max_val = meta.get("max_exchanges")
        if isinstance(max_val, int) and max_val > 0:
            return max_val
        return DEFAULT_MAX_EXCHANGES

    # ------------------------------------------------------------------
    # Tool call logging
    # ------------------------------------------------------------------

    def log_tool_call(
        self,
        conversation_id: int,
        incoming_msg_id: int,
        tool_name: str,
        tool_args: dict,
        tool_result: dict,
        duration_ms: int,
    ) -> None:
        """Registra un tool_call en sms_ai_tool_log."""
        db: Session = self._db_session_factory()
        try:
            log_entry = SmsAiToolLog(
                conversation_id=conversation_id,
                incoming_msg_id=incoming_msg_id,
                tool_name=tool_name,
                tool_args=tool_args,
                tool_result=tool_result,
                duration_ms=duration_ms,
            )
            db.add(log_entry)
            db.commit()
            logger.debug(
                "Tool call registrado: conv=%s, msg=%s, tool=%s, duration=%sms",
                conversation_id, incoming_msg_id, tool_name, duration_ms,
            )
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Deteccion de despedida
    # ------------------------------------------------------------------

    def detect_farewell(self, text: str) -> bool:
        """Detecta si un texto contiene despedida.

        Realiza keyword matching contra FAREWELL_PATTERNS.
        NO usa LLM — solo comparacion de texto (minusculas, sin acentos).
        """
        import unicodedata

        normalized = unicodedata.normalize("NFKD", text.lower())
        normalized = "".join(c for c in normalized if not unicodedata.combining(c))

        for pattern in FAREWELL_PATTERNS:
            if pattern in normalized:
                return True
        return False

    # ------------------------------------------------------------------
    # Gestion del ciclo de vida de la conversacion
    # ------------------------------------------------------------------

    def complete_conversation(
        self, conversation_id: int,
    ) -> None:
        """Marca la conversacion como completed."""
        self._persistence.update_conversation_status(conversation_id, "completed")

    # ------------------------------------------------------------------
    # Archivado de conversaciones antiguas
    # ------------------------------------------------------------------

    def archive_old_conversations(self) -> int:
        """Archiva conversaciones ai_query completadas sin actividad por 90+ dias.

        Retorna el numero de conversaciones archivadas.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        db: Session = self._db_session_factory()
        count = 0
        try:
            old_convs = (
                db.query(SmsConversation)
                .filter(
                    SmsConversation.workflow_type == "ai_query",
                    SmsConversation.status == "completed",
                    SmsConversation.last_activity < cutoff,
                )
                .all()
            )
            for conv in old_convs:
                conv.status = "archived"
                count += 1
            if count > 0:
                db.commit()
                logger.info(
                    "Archivadas %d conversaciones AI completadas > 90 dias", count,
                )
        finally:
            db.close()
        return count
