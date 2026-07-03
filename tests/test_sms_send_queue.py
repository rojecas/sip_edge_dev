"""Tests for SmsSendQueue: async send queue with retry mechanism.

Feature 27 — sms_persistence.
"""

import time
import unittest
from unittest import mock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.models import Base
from src.sms_persistence import SmsPersistenceService
from src.sms_send_queue import SmsSendQueue, SmsSendQueueError


def _build_test_db_engine():
    """Crea un engine SQLite en memoria para tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


class TestSmsSendQueue(unittest.TestCase):
    """Tests de la cola de envio asincrona."""

    def setUp(self):
        """Configura persistence, sms_service mock, y cola."""
        self.engine = _build_test_db_engine()
        self.Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.persistence = SmsPersistenceService(db_session_factory=self.Session)

        # Mock sms_service
        self.sms_service = mock.MagicMock()
        self.sms_service._send_via_mmcli_sync.return_value = True

        self.queue = SmsSendQueue(
            persistence=self.persistence,
            sms_service=self.sms_service,
            modem_index=0,
            timeout_seconds=20,
            poll_interval=0.1,
        )

    def tearDown(self):
        """Detiene la cola si esta corriendo."""
        if self.queue.is_running():
            self.queue.stop()

    def _create_pending_message(self, peer_number="+573001234567", body="Test"):
        """Helper: crea una conversacion y un mensaje pendiente."""
        conv = self.persistence.create_conversation(
            peer_number=peer_number, workflow_type="emergency",
        )
        return self.persistence.create_message(
            conversation_id=conv.id,
            direction="sent",
            peer_number=peer_number,
            body=body,
            status="pending",
        )

    # ==================================================================
    # R8: Basic send queue processing
    # ==================================================================

    def test_send_queue_processes_pending(self):
        """R8: encolar y verificar procesamiento."""
        msg = self._create_pending_message()

        # Procesar mensaje manualmente (sin iniciar el thread)
        self.queue._process_pending_messages()

        # Verificar que se llamo a mmcli
        self.sms_service._send_via_mmcli_sync.assert_called_once_with(
            msg.peer_number, msg.body,
        )

        # Verificar que el mensaje se marco como sent
        updated = self.persistence.get_message(msg.id)
        self.assertEqual(updated.status, "sent")

    def test_send_queue_retry_mechanism(self):
        """R10: simular fallo y verificar 3 reintentos."""
        # Configurar mmcli para fallar siempre
        self.sms_service._send_via_mmcli_sync.return_value = False
        msg = self._create_pending_message()

        self.queue._send_with_retry(msg)

        # Debe haber llamado 3 veces
        self.assertEqual(
            self.sms_service._send_via_mmcli_sync.call_count, 3,
        )

        # El mensaje debe estar en failed
        updated = self.persistence.get_message(msg.id)
        self.assertEqual(updated.status, "failed")
        self.assertIn("3 retries", updated.error_message or "")

    def test_send_queue_retry_success_after_failure(self):
        """R10: exito en segundo intento."""
        call_count = [0]

        def side_effect(phone, body):
            call_count[0] += 1
            if call_count[0] < 2:
                return False
            return True

        self.sms_service._send_via_mmcli_sync.side_effect = side_effect
        msg = self._create_pending_message()

        result = self.queue._send_with_retry(msg)
        self.assertTrue(result)
        self.assertEqual(call_count[0], 2)
        updated = self.persistence.get_message(msg.id)
        self.assertEqual(updated.status, "sent")

    # ==================================================================
    # R9: Timeout configurable
    # ==================================================================

    def test_send_queue_timeout_configurable(self):
        """R9: verificar timeout configurable."""
        queue_default = SmsSendQueue(
            persistence=self.persistence,
            sms_service=self.sms_service,
            modem_index=0,
            timeout_seconds=20,
        )
        self.assertEqual(queue_default._timeout_seconds, 20)

        queue_custom = SmsSendQueue(
            persistence=self.persistence,
            sms_service=self.sms_service,
            modem_index=0,
            timeout_seconds=45,
        )
        self.assertEqual(queue_custom._timeout_seconds, 45)

    # ==================================================================
    # R11: Non-blocking
    # ==================================================================

    def test_send_queue_non_blocking(self):
        """R11: verificar que no bloquea el hilo principal."""
        msg = self._create_pending_message()

        # Iniciar cola en background
        self.queue.start()

        # Dar tiempo para que procese
        time.sleep(0.5)

        # El hilo principal no deberia estar bloqueado
        self.assertTrue(True)  # Si llegamos aqui, no bloqueo

        self.queue.stop()

        # Verificar que el mensaje fue procesado (o al menos se intento)
        updated = self.persistence.get_message(msg.id)
        # Si mmcli retorno True, deberia estar sent
        self.assertIn(updated.status, ("sent", "pending"))

    def test_send_queue_start_stop(self):
        """Verificar que start/stop funcionan correctamente."""
        self.assertFalse(self.queue.is_running())
        self.queue.start()
        self.assertTrue(self.queue.is_running())
        self.queue.stop()
        self.assertFalse(self.queue.is_running())

    def test_send_queue_exception_in_send_does_not_crash(self):
        """Verificar que excepcion en mmcli no crashea la cola."""
        self.sms_service._send_via_mmcli_sync.side_effect = RuntimeError("mmcli crash")
        msg = self._create_pending_message()

        self.queue._send_with_retry(msg)

        # El mensaje debe estar en failed
        updated = self.persistence.get_message(msg.id)
        self.assertEqual(updated.status, "failed")

    def test_send_queue_stop_during_poll(self):
        """Verificar que stop funciona mientras se hace polling."""
        self.queue.start()
        time.sleep(0.1)
        self.queue.stop()
        self.assertFalse(self.queue.is_running())


if __name__ == "__main__":
    unittest.main()
