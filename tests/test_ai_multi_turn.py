"""Tests for AiMultiTurnService: conversation management, history, tool logging.

Feature 28 — ai_multi_turn.
"""

import unittest
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.models import Base, SmsAiToolLog, SmsConversation, SmsMessage
from src.sms_persistence import SmsPersistenceService
from src.ai_multi_turn import (
    AiMultiTurnError,
    AiMultiTurnService,
    DEFAULT_MAX_EXCHANGES,
)


def _build_test_db_engine():
    """Crea un engine SQLite en memoria para tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


class TestAiMultiTurnService(unittest.TestCase):
    """Tests unitarios para AiMultiTurnService."""

    def setUp(self):
        """Configura engine, persistence, y servicio por test."""
        self.engine = _build_test_db_engine()
        self.Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.persistence = SmsPersistenceService(db_session_factory=self.Session)
        self.svc = AiMultiTurnService(
            db_session_factory=self.Session,
            persistence=self.persistence,
        )

    def _create_conversation(
        self, peer="+573001234567", workflow_type="ai_query",
        status="active", metadata=None,
    ) -> SmsConversation:
        return self.persistence.create_conversation(
            peer_number=peer,
            workflow_type=workflow_type,
            status=status,
            metadata=metadata,
        )

    def _create_message(
        self, conversation_id, direction="received",
        peer="+573001234567", body="test", status="received",
    ) -> SmsMessage:
        return self.persistence.create_message(
            conversation_id=conversation_id,
            direction=direction,
            peer_number=peer,
            body=body,
            status=status,
        )

    # ==================================================================
    # get_or_create_ai_conversation
    # ==================================================================

    def test_get_or_create_ai_conversation_new(self):
        """R1, R7: Crea conversacion si no existe."""
        conv = self.svc.get_or_create_ai_conversation("+573001234567")
        self.assertIsNotNone(conv.id)
        self.assertEqual(conv.peer_number, "+573001234567")
        self.assertEqual(conv.workflow_type, "ai_query")
        self.assertEqual(conv.status, "active")

    def test_get_or_create_ai_conversation_existing(self):
        """R7: Reutiliza conversacion activa existente."""
        existing = self._create_conversation(
            peer="+573001234567", workflow_type="ai_query", status="active",
        )
        conv = self.svc.get_or_create_ai_conversation("+573001234567")
        self.assertEqual(conv.id, existing.id)
        self.assertEqual(conv.status, "active")

    def test_get_or_create_ai_conversation_upgrades_unknown(self):
        """R1, R7: Actualiza workflow_type='unknown' a 'ai_query' en lugar de duplicar."""
        # Simular conversacion creada por el dispatcher como 'unknown'
        unknown_conv = self._create_conversation(
            peer="+573001234567", workflow_type="unknown", status="active",
        )
        conv = self.svc.get_or_create_ai_conversation(
            "+573001234567", conversation_id=unknown_conv.id,
        )
        self.assertEqual(conv.id, unknown_conv.id)
        self.assertEqual(conv.workflow_type, "ai_query")
        self.assertEqual(conv.status, "active")

    def test_get_or_create_ai_conversation_non_active_creates_new(self):
        """Si existe conversacion no activa, crea una nueva."""
        completed_conv = self._create_conversation(
            peer="+573001234567", workflow_type="ai_query", status="completed",
        )
        conv = self.svc.get_or_create_ai_conversation(
            "+573001234567", conversation_id=completed_conv.id,
        )
        self.assertNotEqual(conv.id, completed_conv.id)
        self.assertEqual(conv.status, "active")

    # ==================================================================
    # get_message_history
    # ==================================================================

    def test_get_message_history_empty(self):
        """R2: Historial vacio cuando no hay metadata."""
        conv = self._create_conversation()
        history = self.svc.get_message_history(conv)
        self.assertEqual(history, [])

    def test_get_message_history_with_data(self):
        """R2: Recupera historial existente."""
        conv = self._create_conversation(metadata={
            "message_history": [
                {"user": "hola", "assistant": "Hola, en que puedo ayudarte?"},
            ],
        })
        history = self.svc.get_message_history(conv)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["user"], "hola")
        self.assertEqual(history[0]["assistant"], "Hola, en que puedo ayudarte?")

    # ==================================================================
    # append_exchange
    # ==================================================================

    def test_append_exchange_first(self):
        """R2: Agrega primer exchange y persiste en metadata."""
        conv = self._create_conversation()
        history = self.svc.get_message_history(conv)
        self.assertEqual(len(history), 0)

        self.svc.append_exchange(
            conv.id, history, "hola", "Hola!",
        )

        # Verificar que se persistio en BD
        updated = self.persistence.get_conversation(conv.id)
        new_history = self.svc.get_message_history(updated)
        self.assertEqual(len(new_history), 1)
        self.assertEqual(new_history[0]["user"], "hola")
        self.assertEqual(new_history[0]["assistant"], "Hola!")

    def test_append_exchange_fifo(self):
        """R3: Al llegar al limite, elimina el mas antiguo."""
        conv = self._create_conversation()
        history: list[dict] = []

        # Agregar 10 exchanges (limite default)
        for i in range(10):
            self.svc.append_exchange(
                conv.id, history, f"msg{i}", f"resp{i}", max_exchanges=10,
            )
            # Re-cargar historia desde BD
            updated = self.persistence.get_conversation(conv.id)
            history = self.svc.get_message_history(updated)

        self.assertEqual(len(history), 10)
        self.assertEqual(history[0]["user"], "msg0")

        # Agregar un exchange mas — debe eliminar el mas antiguo
        self.svc.append_exchange(
            conv.id, history, "msg10", "resp10", max_exchanges=10,
        )
        updated = self.persistence.get_conversation(conv.id)
        history = self.svc.get_message_history(updated)
        self.assertEqual(len(history), 10)
        self.assertEqual(history[0]["user"], "msg1")
        self.assertEqual(history[-1]["user"], "msg10")

    def test_append_exchange_configurable_limit(self):
        """R10: Respeta max_exchanges desde metadata con valor personalizado."""
        conv = self._create_conversation(metadata={"max_exchanges": 3})
        history: list[dict] = []

        for i in range(3):
            self.svc.append_exchange(
                conv.id, history, f"msg{i}", f"resp{i}", max_exchanges=3,
            )
            updated = self.persistence.get_conversation(conv.id)
            history = self.svc.get_message_history(updated)

        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]["user"], "msg0")

        # Agregar cuarto — debe FIFO
        self.svc.append_exchange(
            conv.id, history, "msg3", "resp3", max_exchanges=3,
        )
        updated = self.persistence.get_conversation(conv.id)
        history = self.svc.get_message_history(updated)
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]["user"], "msg1")

    # ==================================================================
    # build_llm_messages
    # ==================================================================

    def test_build_llm_messages(self):
        """R4: Construye arreglo correcto con system + history + user."""
        history = [
            {"user": "hola", "assistant": "Hola!"},
            {"user": "cuantos pesajes hoy?", "assistant": "Hoy hubo 25 pesajes."},
        ]
        messages = self.svc.build_llm_messages(
            history, "y ayer?", "Eres un asistente.",
        )
        self.assertEqual(len(messages), 6)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"], "hola")
        self.assertEqual(messages[2]["role"], "assistant")
        self.assertEqual(messages[3]["role"], "user")
        self.assertEqual(messages[4]["role"], "assistant")
        self.assertEqual(messages[5]["role"], "user")
        self.assertEqual(messages[5]["content"], "y ayer?")

    def test_build_llm_messages_empty_history(self):
        """R4: Construccion con historial vacio."""
        messages = self.svc.build_llm_messages(
            [], "consulta nueva", "Eres un asistente.",
        )
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")

    def test_build_llm_messages_missing_assistant(self):
        """R4: Exchange con solo user sin assistant no rompe."""
        history = [{"user": "hola"}]
        messages = self.svc.build_llm_messages(
            history, "nuevo mensaje", "System prompt",
        )
        self.assertEqual(len(messages), 3)

    # ==================================================================
    # log_tool_call
    # ==================================================================

    def test_log_tool_call(self):
        """R6: Registra tool_call en sms_ai_tool_log con todos los campos."""
        conv = self._create_conversation()
        msg = self._create_message(conv.id)

        self.svc.log_tool_call(
            conversation_id=conv.id,
            incoming_msg_id=msg.id,
            tool_name="get_basic_stats",
            tool_args={"fecha_inicio": "2026-06-01", "fecha_fin": "2026-06-15"},
            tool_result={"count": 42, "avg": 107.5},
            duration_ms=350,
        )

        # Verificar en BD
        db = self.Session()
        try:
            log = db.query(SmsAiToolLog).filter(
                SmsAiToolLog.conversation_id == conv.id,
            ).first()
            self.assertIsNotNone(log)
            self.assertEqual(log.tool_name, "get_basic_stats")
            self.assertEqual(log.tool_args, {"fecha_inicio": "2026-06-01", "fecha_fin": "2026-06-15"})
            self.assertEqual(log.tool_result, {"count": 42, "avg": 107.5})
            self.assertEqual(log.duration_ms, 350)
            self.assertEqual(log.incoming_msg_id, msg.id)
        finally:
            db.close()

    # ==================================================================
    # detect_farewell
    # ==================================================================

    def test_detect_farewell_true(self):
        """R8: Detecta despedidas comunes."""
        self.assertTrue(self.svc.detect_farewell("gracias"))
        self.assertTrue(self.svc.detect_farewell("Muchas GRACIAS!"))
        self.assertTrue(self.svc.detect_farewell("bye"))
        self.assertTrue(self.svc.detect_farewell("Eso es todo"))
        self.assertTrue(self.svc.detect_farewell("ok gracias"))
        self.assertTrue(self.svc.detect_farewell("nada mas, gracias"))
        self.assertTrue(self.svc.detect_farewell("terminamos por hoy"))
        self.assertTrue(self.svc.detect_farewell("suficiente informacion"))

    def test_detect_farewell_false(self):
        """R8: No detecta despedida en consulta normal."""
        self.assertFalse(self.svc.detect_farewell("cuantos pesajes hoy?"))
        self.assertFalse(self.svc.detect_farewell("dame el promedio de junio"))
        self.assertFalse(self.svc.detect_farewell(""))
        self.assertFalse(self.svc.detect_farewell("hola"))

    def test_detect_farewell_with_accents(self):
        """R8: Maneja acentos correctamente."""
        self.assertTrue(self.svc.detect_farewell("adiós"))
        self.assertTrue(self.svc.detect_farewell("adiÓs"))
        self.assertTrue(self.svc.detect_farewell("chao"))

    # ==================================================================
    # complete_conversation
    # ==================================================================

    def test_complete_conversation(self):
        """R8: Marca conversacion como completed."""
        conv = self._create_conversation(status="active")
        self.svc.complete_conversation(conv.id)

        updated = self.persistence.get_conversation(conv.id)
        self.assertEqual(updated.status, "completed")

    # ==================================================================
    # archive_old_conversations
    # ==================================================================

    def test_archive_old_conversations(self):
        """R9: Archiva conversaciones completadas > 90 dias."""
        # Crear conversacion completada hace 100 dias
        conv = self._create_conversation(status="completed")

        # Simular last_activity viejo directamente en BD
        old_date = datetime.now(timezone.utc) - timedelta(days=100)
        db = self.Session()
        try:
            db_conv = db.query(SmsConversation).filter(
                SmsConversation.id == conv.id,
            ).first()
            db_conv.last_activity = old_date
            db.commit()
        finally:
            db.close()

        count = self.svc.archive_old_conversations()
        self.assertGreaterEqual(count, 1)

        updated = self.persistence.get_conversation(conv.id)
        self.assertEqual(updated.status, "archived")

    def test_archive_old_conversations_skips_active(self):
        """R9: No archiva conversaciones activas."""
        conv = self._create_conversation(status="active")

        # last_activity viejo pero status=active
        old_date = datetime.now(timezone.utc) - timedelta(days=100)
        db = self.Session()
        try:
            db_conv = db.query(SmsConversation).filter(
                SmsConversation.id == conv.id,
            ).first()
            db_conv.last_activity = old_date
            db.commit()
        finally:
            db.close()

        count = self.svc.archive_old_conversations()
        self.assertEqual(count, 0)

        updated = self.persistence.get_conversation(conv.id)
        self.assertEqual(updated.status, "active")

    def test_archive_old_conversations_skips_recent(self):
        """R9: No archiva conversaciones recientemente completadas."""
        conv = self._create_conversation(status="completed")
        # last_activity reciente (default ahora) — no debe archivar
        count = self.svc.archive_old_conversations()
        self.assertEqual(count, 0)

    # ==================================================================
    # get_max_exchanges
    # ==================================================================

    def test_get_max_exchanges_default(self):
        """R10: Retorna 10 si no hay clave en metadata."""
        conv = self._create_conversation()
        self.assertEqual(self.svc.get_max_exchanges(conv), DEFAULT_MAX_EXCHANGES)

    def test_get_max_exchanges_from_metadata(self):
        """R10: Retorna valor de metadata si existe."""
        conv = self._create_conversation(metadata={"max_exchanges": 5})
        self.assertEqual(self.svc.get_max_exchanges(conv), 5)

    def test_get_max_exchanges_zero_returns_default(self):
        """R10: max_exchanges=0 retorna default."""
        conv = self._create_conversation(metadata={"max_exchanges": 0})
        self.assertEqual(self.svc.get_max_exchanges(conv), DEFAULT_MAX_EXCHANGES)

    def test_get_max_exchanges_negative_returns_default(self):
        """R10: max_exchanges negativo retorna default."""
        conv = self._create_conversation(metadata={"max_exchanges": -5})
        self.assertEqual(self.svc.get_max_exchanges(conv), DEFAULT_MAX_EXCHANGES)


if __name__ == "__main__":
    unittest.main()
