"""Tests for SmsPersistenceService: CRUD operations for sms_conversations
and sms_messages.

Feature 27 — sms_persistence.
"""

import unittest
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.models import Base, SmsConversation, SmsMessage
from src.sms_persistence import SmsPersistenceError, SmsPersistenceService


def _build_test_db_engine():
    """Crea un engine SQLite en memoria para tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


class TestSmsPersistence(unittest.TestCase):
    """Tests CRUD para conversaciones y mensajes SMS."""

    def setUp(self):
        """Configura engine y servicio por test."""
        self.engine = _build_test_db_engine()
        self.Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.svc = SmsPersistenceService(db_session_factory=self.Session)

    # ==================================================================
    # Conversaciones
    # ==================================================================

    def test_create_conversation(self):
        """R1: crear y leer conversacion."""
        conv = self.svc.create_conversation(
            peer_number="+573001234567",
            workflow_type="emergency",
            status="active",
        )
        self.assertIsNotNone(conv.id)
        self.assertEqual(conv.peer_number, "+573001234567")
        self.assertEqual(conv.workflow_type, "emergency")
        self.assertEqual(conv.status, "active")
        self.assertIsNotNone(conv.started_at)
        self.assertIsNotNone(conv.last_activity)

    def test_create_conversation_invalid_workflow_type(self):
        """Crear conversacion con workflow_type invalido lanza error."""
        with self.assertRaises(SmsPersistenceError):
            self.svc.create_conversation(
                peer_number="+57", workflow_type="invalid_type",
            )

    def test_create_conversation_invalid_status(self):
        """Crear conversacion con status invalido lanza error."""
        with self.assertRaises(SmsPersistenceError):
            self.svc.create_conversation(
                peer_number="+57", workflow_type="emergency",
                status="bogus_status",
            )

    def test_get_active_conversation(self):
        """R4: get_or_create_active_conversation recupera conversacion activa."""
        self.svc.create_conversation(
            peer_number="+573001234567",
            workflow_type="emergency",
        )
        conv = self.svc.get_or_create_active_conversation(
            peer_number="+573001234567",
            workflow_type="emergency",
        )
        self.assertIsNotNone(conv)
        self.assertEqual(conv.peer_number, "+573001234567")
        self.assertEqual(conv.workflow_type, "emergency")
        self.assertEqual(conv.status, "active")

    def test_get_active_conversation_creates_if_not_exists(self):
        """get_or_create_active_conversation crea nueva si no existe."""
        conv = self.svc.get_or_create_active_conversation(
            peer_number="+573009999999",
            workflow_type="ai_query",
        )
        self.assertIsNotNone(conv.id)
        self.assertEqual(conv.peer_number, "+573009999999")
        self.assertEqual(conv.workflow_type, "ai_query")
        self.assertEqual(conv.status, "active")

    def test_update_conversation_status(self):
        """Actualizar status de conversacion."""
        conv = self.svc.create_conversation(
            peer_number="+57123", workflow_type="password_reset",
        )
        self.svc.update_conversation_status(conv.id, "completed")
        # Verificar
        db = self.Session()
        try:
            updated = db.query(SmsConversation).filter(
                SmsConversation.id == conv.id
            ).first()
            self.assertEqual(updated.status, "completed")
        finally:
            db.close()

    def test_update_conversation_status_not_found(self):
        """Actualizar conversacion inexistente lanza error."""
        with self.assertRaises(SmsPersistenceError):
            self.svc.update_conversation_status(99999, "completed")

    # ==================================================================
    # Mensajes
    # ==================================================================

    def test_create_message(self):
        """R2: crear y leer mensaje."""
        conv = self.svc.create_conversation(
            peer_number="+573001234567",
            workflow_type="emergency",
        )
        msg = self.svc.create_message(
            conversation_id=conv.id,
            direction="sent",
            peer_number="+573001234567",
            body="Test SMS message",
            handler="emergency",
            status="pending",
        )
        self.assertIsNotNone(msg.id)
        self.assertEqual(msg.conversation_id, conv.id)
        self.assertEqual(msg.direction, "sent")
        self.assertEqual(msg.peer_number, "+573001234567")
        self.assertEqual(msg.body, "Test SMS message")
        self.assertEqual(msg.handler, "emergency")
        self.assertEqual(msg.status, "pending")

    def test_create_message_invalid_direction(self):
        """Crear mensaje con direction invalida lanza error."""
        conv = self.svc.create_conversation(
            peer_number="+57", workflow_type="unknown",
        )
        with self.assertRaises(SmsPersistenceError):
            self.svc.create_message(
                conversation_id=conv.id,
                direction="bogus_dir",
                peer_number="+57",
                body="test",
            )

    def test_update_message_status(self):
        """R18: actualizar status y error_message de un mensaje."""
        conv = self.svc.create_conversation(
            peer_number="+573001234567",
            workflow_type="emergency",
        )
        msg = self.svc.create_message(
            conversation_id=conv.id,
            direction="sent",
            peer_number="+573001234567",
            body="Test SMS",
        )
        self.svc.update_message_status(msg.id, "sent", modem_sms_id=42)
        # Verificar
        db = self.Session()
        try:
            updated = db.query(SmsMessage).filter(SmsMessage.id == msg.id).first()
            self.assertEqual(updated.status, "sent")
            self.assertEqual(updated.modem_sms_id, 42)
            self.assertIsNone(updated.error_message)
        finally:
            db.close()

    def test_update_message_status_with_error(self):
        """Actualizar status a failed con error_message."""
        conv = self.svc.create_conversation(
            peer_number="+57", workflow_type="unknown",
        )
        msg = self.svc.create_message(
            conversation_id=conv.id,
            direction="sent",
            peer_number="+57",
            body="Failing SMS",
        )
        self.svc.update_message_status(
            msg.id, "failed", error_message="Network timeout",
        )
        db = self.Session()
        try:
            updated = db.query(SmsMessage).filter(SmsMessage.id == msg.id).first()
            self.assertEqual(updated.status, "failed")
            self.assertEqual(updated.error_message, "Network timeout")
        finally:
            db.close()

    def test_get_pending_messages(self):
        """R9: recuperar mensajes pendientes de envio."""
        conv = self.svc.create_conversation(
            peer_number="+57", workflow_type="emergency",
        )
        # Crear 3 pendientes y 1 ya enviado
        for i in range(3):
            self.svc.create_message(
                conversation_id=conv.id,
                direction="sent",
                peer_number="+57",
                body=f"Pending {i}",
                status="pending",
            )
        msg_sent = self.svc.create_message(
            conversation_id=conv.id,
            direction="sent",
            peer_number="+57",
            body="Already sent",
            status="sent",
        )

        pending = self.svc.get_pending_outgoing_messages(limit=10)
        self.assertEqual(len(pending), 3)
        for m in pending:
            self.assertEqual(m.status, "pending")
            self.assertEqual(m.direction, "sent")

    def test_message_creation_updates_conversation_activity(self):
        """Crear mensaje actualiza last_activity de la conversacion."""
        conv = self.svc.create_conversation(
            peer_number="+57", workflow_type="ai_query",
        )
        old_activity = conv.last_activity

        self.svc.create_message(
            conversation_id=conv.id,
            direction="received",
            peer_number="+57",
            body="Hello",
            status="received",
        )

        db = self.Session()
        try:
            updated = db.query(SmsConversation).filter(
                SmsConversation.id == conv.id
            ).first()
            self.assertIsNotNone(updated.last_activity)
            # La actividad deberia haberse actualizado
            self.assertGreaterEqual(
                updated.last_activity.replace(tzinfo=timezone.utc),
                old_activity.replace(tzinfo=timezone.utc)
                if old_activity.tzinfo is None
                else old_activity,
            )
        finally:
            db.close()

    # ==================================================================
    # Message exists by modem_sms_id (Fix 3)
    # ==================================================================

    def test_message_exists_by_modem_id_returns_true_when_exists(self):
        """message_exists_by_modem_id retorna True si el modem_sms_id existe."""
        conv = self.svc.create_conversation(
            peer_number="+573001234567", workflow_type="emergency",
        )
        msg = self.svc.create_message(
            conversation_id=conv.id,
            direction="sent",
            peer_number="+573001234567",
            body="Test",
            status="sent",
        )
        # Asignar modem_sms_id manualmente
        self.svc.update_message_status(msg.id, "sent", modem_sms_id=42)

        result = self.svc.message_exists_by_modem_id(42)
        self.assertTrue(result)

    def test_message_exists_by_modem_id_returns_false_when_not_exists(self):
        """message_exists_by_modem_id retorna False si el modem_sms_id no existe."""
        result = self.svc.message_exists_by_modem_id(999)
        self.assertFalse(result)

    def test_message_exists_by_modem_id_ignores_other_ids(self):
        """message_exists_by_modem_id solo encuentra el ID exacto."""
        conv = self.svc.create_conversation(
            peer_number="+573001234567", workflow_type="emergency",
        )
        msg = self.svc.create_message(
            conversation_id=conv.id,
            direction="sent",
            peer_number="+573001234567",
            body="Test",
            status="sent",
        )
        self.svc.update_message_status(msg.id, "sent", modem_sms_id=100)

        self.assertTrue(self.svc.message_exists_by_modem_id(100))
        self.assertFalse(self.svc.message_exists_by_modem_id(101))

    def test_get_message_by_id(self):
        """Recuperar mensaje por ID."""
        conv = self.svc.create_conversation(
            peer_number="+57", workflow_type="unknown",
        )
        msg = self.svc.create_message(
            conversation_id=conv.id,
            direction="received",
            peer_number="+57",
            body="Hello",
            status="received",
        )
        retrieved = self.svc.get_message(msg.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, msg.id)
        self.assertEqual(retrieved.body, "Hello")


if __name__ == "__main__":
    unittest.main()
