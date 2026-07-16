"""Tests for IncomingSmsDispatcherV2: persistence before dispatch,
unknown SMS help response, carrier SMS handling, and conversation creation.

Feature 27 — sms_persistence.
"""

import asyncio
import subprocess
import unittest
from unittest import mock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.models import Base, SmsConversation, SmsMessage, User
from src.sms_persistence import SmsPersistenceService
from src.sms_dispatcher_v2 import IncomingSmsDispatcherV2


def _build_test_db_engine():
    """Crea un engine SQLite en memoria para tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


class TestSmsDispatcherV2(unittest.TestCase):
    """Tests del dispatcher v2 con persistencia."""

    def setUp(self):
        """Configura persistence y dispatcher v2."""
        self.engine = _build_test_db_engine()
        self.Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.persistence = SmsPersistenceService(db_session_factory=self.Session)

        self.dispatcher = IncomingSmsDispatcherV2(
            modem_index=0,
            dev_mode=True,
            persistence=self.persistence,
        )

    # ==================================================================
    # R3: Persist before dispatch
    # ==================================================================

    def test_persist_before_dispatch(self):
        """R3: verificar que el SMS esta en BD antes de llamar al handler."""
        handler_called = []

        def my_handler(sender_phone, text):
            # Verificar que el SMS ya esta en BD
            db = self.Session()
            try:
                msgs = (
                    db.query(SmsMessage)
                    .filter(SmsMessage.peer_number == sender_phone)
                    .all()
                )
                handler_called.append(len(msgs))
                # Debe haber al menos un mensaje (el entrante)
                self.assertGreater(len(msgs), 0)
            finally:
                db.close()
            return True

        self.dispatcher.register_handler(my_handler, workflow_type="test")
        self.dispatcher._dispatch("+573001234567", "hello")

        # Verificar que el handler fue llamado
        self.assertEqual(len(handler_called), 1)
        self.assertGreater(handler_called[0], 0,
            "El SMS entrante deberia estar persistido ANTES de llamar al handler")

    def test_persist_before_dispatch_message_exists(self):
        """R3: El mensaje existe en BD con status='received' despues de dispatch."""
        handled = []
        self.dispatcher.register_handler(
            lambda p, t: handled.append(True) or True, workflow_type="test",
        )
        self.dispatcher._dispatch("+573001234567", "test message")

        db = self.Session()
        try:
            msgs = (
                db.query(SmsMessage)
                .filter(SmsMessage.peer_number == "+573001234567")
                .all()
            )
            self.assertEqual(len(msgs), 1, "Deberia haber 1 mensaje persistido")
            self.assertEqual(msgs[0].direction, "received")
            self.assertEqual(msgs[0].status, "received")
            self.assertEqual(msgs[0].body, "test message")
        finally:
            db.close()

    # ==================================================================
    # modem_sms_id for incoming SMS
    # ==================================================================

    def test_incoming_sms_stores_modem_sms_id(self):
        """Verificar que un SMS entrante almacena el modem_sms_id en BD."""
        self.dispatcher.register_handler(
            lambda p, t: True, workflow_type="test",
        )
        self.dispatcher._dispatch(
            "+573001234567", "test message", modem_sms_id="42",
        )

        db = self.Session()
        try:
            msgs = (
                db.query(SmsMessage)
                .filter(SmsMessage.peer_number == "+573001234567")
                .all()
            )
            self.assertEqual(len(msgs), 1, "Deberia haber 1 mensaje persistido")
            self.assertEqual(msgs[0].modem_sms_id, 42,
                "modem_sms_id debe almacenarse como entero")
            self.assertEqual(msgs[0].direction, "received")
            self.assertEqual(msgs[0].status, "received")
            self.assertEqual(msgs[0].body, "test message")
        finally:
            db.close()

    def test_incoming_sms_modem_sms_id_none_carrier(self):
        """Verificar que SMS de carrier tiene modem_sms_id=NULL."""
        self.dispatcher._dispatch("369", "Tigo: saldo")
        db = self.Session()
        try:
            msgs = (
                db.query(SmsMessage)
                .filter(SmsMessage.peer_number == "369")
                .all()
            )
            self.assertEqual(len(msgs), 1)
            self.assertIsNone(msgs[0].modem_sms_id,
                "SMS de carrier debe tener modem_sms_id=NULL")
        finally:
            db.close()

    # ==================================================================
    # R4: Conversation created on first message
    # ==================================================================

    def test_conversation_created_on_first_message(self):
        """R4: primer SMS crea conversacion."""
        self.dispatcher.register_handler(
            lambda p, t: True, workflow_type="test",
        )
        self.dispatcher._dispatch("+573009999999", "first message")

        db = self.Session()
        try:
            convs = (
                db.query(SmsConversation)
                .filter(SmsConversation.peer_number == "+573009999999")
                .all()
            )
            self.assertEqual(len(convs), 1, "Deberia crearse una conversacion")
            self.assertEqual(convs[0].status, "active")
        finally:
            db.close()

    # ==================================================================
    # R5: No catch-all AI handler
    # ==================================================================

    def test_no_catchall_ai_handler(self):
        """R5: verificar que NO hay handler catch-all de AI.

        Un SMS que no matchea ningun handler NO debe ser enviado al AI.
        En su lugar, debe recibir el texto de ayuda.
        """
        # Registrar un handler que siempre retorna False (no maneja)
        self.dispatcher.register_handler(
            lambda p, t: False, workflow_type="emergency",
        )
        self.dispatcher._dispatch("+573001234567", "cualquier cosa random")

        db = self.Session()
        try:
            msgs = (
                db.query(SmsMessage)
                .filter(SmsMessage.peer_number == "+573001234567")
                .order_by(SmsMessage.created_at.asc())
                .all()
            )
            # Debe haber 2 mensajes: el recibido y la respuesta de ayuda
            self.assertEqual(len(msgs), 2)
            # El segundo debe ser la respuesta de ayuda
            self.assertEqual(msgs[1].direction, "sent")
            self.assertIn("Comando no reconocido", msgs[1].body)
        finally:
            db.close()

    # ==================================================================
    # R6: Unknown SMS help response
    # ==================================================================

    def test_unknown_sms_help_response(self):
        """R6: SMS no reconocido recibe texto de ayuda."""
        # Sin handlers registrados — dispatch sin handlers
        self.dispatcher._dispatch("+573001234567", "cualquier mensaje no reconocido")

        db = self.Session()
        try:
            msgs = (
                db.query(SmsMessage)
                .filter(SmsMessage.peer_number == "+573001234567")
                .order_by(SmsMessage.created_at.asc())
                .all()
            )
            self.assertGreaterEqual(len(msgs), 2,
                "Debe haber al menos el SMS recibido y la respuesta de ayuda")

            # Buscar el mensaje de respuesta
            sent_msgs = [m for m in msgs if m.direction == "sent"]
            self.assertGreaterEqual(len(sent_msgs), 1,
                "Debe haber al menos un mensaje de respuesta")
            self.assertIn("Comando no reconocido", sent_msgs[0].body)
            self.assertIn("manual on", sent_msgs[0].body.lower())
            self.assertIn("manual off", sent_msgs[0].body.lower())
            self.assertIn("reset password", sent_msgs[0].body.lower())
        finally:
            db.close()

    def test_unknown_sms_conversation_completed(self):
        """R6: conversacion de SMS no reconocido se marca completed."""
        self.dispatcher._dispatch("+573001234567", "no reconocido")

        db = self.Session()
        try:
            conv = (
                db.query(SmsConversation)
                .filter(SmsConversation.peer_number == "+573001234567")
                .first()
            )
            self.assertIsNotNone(conv)
            self.assertEqual(conv.status, "completed",
                "Conversacion de SMS no reconocido debe marcarse completed")
        finally:
            db.close()

    # ==================================================================
    # Bug 26 regression: handler catch-all NO debe existir
    # ==================================================================

    def test_no_catchall_handler_bug26_regression(self):
        """Bug 26: handler que siempre retorna True (catch-all) no debe estar registrado.

        Escenario de reproduccion:
        1. Se registra handler_emergency que solo retorna True para 'manual on'
        2. Se registra handler_password_reset que solo retorna True para 'reset password'
        3. Se envia SMS 'hola' (no reconocido)
        4. Ningun handler retorna True → dispatcher debe responder con HELP_RESPONSE

        Con el bug, _build_ai_sms_handler retornaba True siempre,
        impidiendo que el dispatcher enviara la respuesta de ayuda.
        """
        def emergency_handler(sender_phone, text):
            if "manual on" in text.lower():
                return True
            return False

        def password_reset_handler(sender_phone, text):
            if "reset password" in text.lower():
                return True
            return False

        self.dispatcher.register_handler(emergency_handler, workflow_type="emergency")
        self.dispatcher.register_handler(password_reset_handler, workflow_type="password_reset")

        # Enviar SMS no reconocido (como 'hola' del Bug 26)
        self.dispatcher._dispatch("+573001111111", "hola")

        db = self.Session()
        try:
            msgs = (
                db.query(SmsMessage)
                .filter(SmsMessage.peer_number == "+573001111111")
                .order_by(SmsMessage.created_at.asc())
                .all()
            )
            # Debe haber 2 mensajes: el recibido y la respuesta de ayuda
            self.assertGreaterEqual(len(msgs), 2,
                "Debe haber SMS recibido + respuesta de ayuda")
            sent_msgs = [m for m in msgs if m.direction == "sent"]
            self.assertGreaterEqual(len(sent_msgs), 1,
                "Debe haber respuesta de ayuda para SMS no reconocido")
            self.assertIn("Comando no reconocido", sent_msgs[0].body,
                "Debe responder 'Comando no reconocido' en vez de mensaje del LLM")
        finally:
            db.close()

    # ==================================================================
    # R7: Carrier SMS no response
    # ==================================================================

    def test_carrier_sms_no_response(self):
        """R7: SMS de carrier se persiste sin respuesta."""
        # Numero corto (< 6 digitos) = carrier
        self.dispatcher._dispatch("369", "Tigo: Tienes $5000 de saldo")

        db = self.Session()
        try:
            msgs = (
                db.query(SmsMessage)
                .filter(SmsMessage.peer_number == "369")
                .all()
            )
            # Solo debe haber el SMS recibido, NO respuesta
            self.assertEqual(len(msgs), 1)
            self.assertEqual(msgs[0].direction, "received")
            self.assertEqual(msgs[0].handler, "carrier")

            conv = (
                db.query(SmsConversation)
                .filter(SmsConversation.peer_number == "369")
                .first()
            )
            self.assertIsNotNone(conv)
            self.assertEqual(conv.workflow_type, "unknown")
            self.assertEqual(conv.status, "completed")
        finally:
            db.close()

    def test_carrier_number_detection(self):
        """Verificar deteccion de numeros de carrier."""
        self.assertTrue(self.dispatcher._is_carrier_number("369"))
        self.assertTrue(self.dispatcher._is_carrier_number("888"))
        self.assertTrue(self.dispatcher._is_carrier_number("12345"))
        self.assertFalse(self.dispatcher._is_carrier_number("123456"))
        self.assertFalse(self.dispatcher._is_carrier_number("+573001234567"))

    # ==================================================================
    # Handler ordering
    # ==================================================================

    def test_handler_order_matters(self):
        """Verificar que los handlers se ejecutan en orden de registro."""
        execution_order = []

        def handler_a(p, t):
            execution_order.append("A")
            return False

        def handler_b(p, t):
            execution_order.append("B")
            return True

        def handler_c(p, t):
            execution_order.append("C")
            return True

        self.dispatcher.register_handler(handler_a, workflow_type="a")
        self.dispatcher.register_handler(handler_b, workflow_type="b")
        self.dispatcher.register_handler(handler_c, workflow_type="c")

        self.dispatcher._dispatch("+573001234567", "test")

        # handler_b retorno True, asi que handler_c no deberia ejecutarse
        self.assertEqual(execution_order, ["A", "B"])

    # ==================================================================
    # Rejected workflow: SMS de operadores/desconocidos se marca rejected
    # ==================================================================

    def test_operator_sms_marked_as_rejected(self):
        """SMS de operador/desconocido debe marcarse como workflow_type='rejected'.

        Cuando un SMS llega de un numero sin rol autorizado (admin/corresponsal),
        la conversacion debe marcarse con workflow_type='rejected' y status='completed'
        para trazabilidad, en vez de quedar como 'unknown'.
        """
        # SMS de un numero sin usuario registrado → role=None → rechazado
        self.dispatcher._dispatch("3001234567", "hola")

        db = self.Session()
        try:
            conv = (
                db.query(SmsConversation)
                .filter(SmsConversation.peer_number == "3001234567")
                .first()
            )
            self.assertIsNotNone(conv, "Debe existir la conversacion")
            self.assertEqual(
                conv.workflow_type, "rejected",
                f"SMS de operador debe marcarse 'rejected', no '{conv.workflow_type}'"
            )
            self.assertEqual(
                conv.status, "completed",
                "Conversacion rechazada debe marcarse completed"
            )
        finally:
            db.close()

    def test_operator_user_sms_marked_as_rejected(self):
        """SMS de usuario con role='operator' debe marcarse como 'rejected'."""
        # Crear usuario con role='operator'
        db = self.Session()
        try:
            user = User(
                username="operador1",
                password_hash="x",
                role="operator",
                phone="3009876543",
            )
            db.add(user)
            db.commit()
        finally:
            db.close()

        # Enviar SMS desde el numero del operador
        self.dispatcher._dispatch("3009876543", "mensaje de operador")

        db = self.Session()
        try:
            conv = (
                db.query(SmsConversation)
                .filter(SmsConversation.peer_number == "3009876543")
                .first()
            )
            self.assertIsNotNone(conv, "Debe existir conversacion para operador")
            self.assertEqual(
                conv.workflow_type, "rejected",
                "SMS de usuario operator debe marcarse 'rejected'"
            )
            self.assertEqual(conv.status, "completed")
        finally:
            db.close()


# ==================================================================
# B2: SMS con state=None se elimina (no se procesa como entrante)
# ==================================================================


class TestSmsDispatcherV2B2(unittest.TestCase):
    """B2: SMS huerfanos sin estado ('state' ausente) se eliminan del modem."""

    def setUp(self):
        self.engine = _build_test_db_engine()
        self.Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.persistence = SmsPersistenceService(db_session_factory=self.Session)

        self.dispatcher = IncomingSmsDispatcherV2(
            modem_index=0,
            dev_mode=False,
            persistence=self.persistence,
        )

    def test_sms_without_state_is_deleted_and_not_processed(self):
        """B2: SMS sin campo 'state' se elimina y no se agrega a messages."""
        call_log = []

        def fake_run(args, **_kwargs):
            call_log.append(args)
            if "--messaging-list-sms" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=0,
                    stdout="/org/freedesktop/ModemManager1/SMS/99\n",
                    stderr="",
                )
            if "-s" in args and "--messaging-delete-sms" not in " ".join(args) and "--send" not in args:
                # Read SMS: devuelve output SIN campo 'state' (simula SMS huerfano)
                return subprocess.CompletedProcess(
                    args=args, returncode=0,
                    stdout=(
                        "  SMS | /org/freedesktop/ModemManager1/SMS/99\n"
                        "    | number: +573009999999\n"
                        "    | text: hola\n"
                    ),
                    stderr="",
                )
            if "--messaging-delete-sms" in " ".join(args):
                return subprocess.CompletedProcess(
                    args=args, returncode=0, stdout="", stderr="",
                )
            return subprocess.CompletedProcess(
                args=args, returncode=0, stdout="", stderr="",
            )

        with mock.patch("subprocess.run", side_effect=fake_run):
            messages = asyncio.run(self.dispatcher._fetch_mmcli_sms())

        # Verificar que NO se devolvio ningun mensaje
        self.assertEqual(len(messages), 0,
            "SMS sin estado no debe ser devuelto como mensaje entrante")

        # Verificar que se llamo a delete-sms para el SMS huerfano
        delete_calls = [
            a for a in call_log
            if any("--messaging-delete-sms" in str(arg) for arg in a)
        ]
        self.assertGreaterEqual(len(delete_calls), 1,
            "Debe llamar a --messaging-delete-sms para el SMS huerfano")

    def test_sms_with_received_state_is_processed(self):
        """B2: SMS con state='received' se procesa normalmente."""
        call_log = []

        def fake_run(args, **_kwargs):
            call_log.append(args)
            if "--messaging-list-sms" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=0,
                    stdout="/org/freedesktop/ModemManager1/SMS/88\n",
                    stderr="",
                )
            if "-s" in args and "--messaging-delete-sms" not in " ".join(args) and "--send" not in args:
                # Read SMS: devuelve state='received' en formato pipe (mmcli real)
                return subprocess.CompletedProcess(
                    args=args, returncode=0,
                    stdout=(
                        "  SMS | /org/freedesktop/ModemManager1/SMS/88\n"
                        "    | state: received\n"
                        "    | number: +573001111111\n"
                        "    | text: test message\n"
                    ),
                    stderr="",
                )
            if "--messaging-delete-sms" in " ".join(args):
                return subprocess.CompletedProcess(
                    args=args, returncode=0, stdout="", stderr="",
                )
            return subprocess.CompletedProcess(
                args=args, returncode=0, stdout="", stderr="",
            )

        with mock.patch("subprocess.run", side_effect=fake_run):
            messages = asyncio.run(self.dispatcher._fetch_mmcli_sms())

        # Verificar que se devolvio el mensaje correctamente con modem_sms_id
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0][0], "+573001111111")
        self.assertEqual(messages[0][1], "test message")
        self.assertEqual(messages[0][2], "88")


# ==================================================================
# Fix 3: Filtrar SMS auto-generados por modem_sms_id
# ==================================================================


class TestSmsDispatcherV2Fix3(unittest.TestCase):
    """Fix 3: SMS con modem_sms_id existente se salta (anti-loop)."""

    def setUp(self):
        self.engine = _build_test_db_engine()
        self.Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.persistence = SmsPersistenceService(db_session_factory=self.Session)

        self.dispatcher = IncomingSmsDispatcherV2(
            modem_index=0,
            dev_mode=False,
            persistence=self.persistence,
        )

    def test_sms_with_existing_modem_id_is_skipped(self):
        """Fix 3: SMS cuyo modem_sms_id existe en BD se elimina y no se procesa."""
        # Pre-poblar BD con un mensaje que tiene modem_sms_id=42
        conv = self.persistence.create_conversation(
            peer_number="+573001234567", workflow_type="unknown",
        )
        msg = self.persistence.create_message(
            conversation_id=conv.id,
            direction="sent",
            peer_number="+573001234567",
            body="Auto-generated",
            status="pending",
        )
        self.persistence.update_message_status(
            msg.id, "sent", modem_sms_id=42,
        )

        call_log = []

        def fake_run(args, **_kwargs):
            call_log.append(args)
            if "--messaging-list-sms" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=0,
                    stdout="/org/freedesktop/ModemManager1/SMS/42\n",
                    stderr="",
                )
            if "-s" in args and "--messaging-delete-sms" not in " ".join(args) and "--send" not in args:
                # Read SMS with state='received' and modem_id=42 (self-generated)
                return subprocess.CompletedProcess(
                    args=args, returncode=0,
                    stdout=(
                        "  SMS | /org/freedesktop/ModemManager1/SMS/42\n"
                        "    | state: received\n"
                        "    | number: +573009999999\n"
                        "    | text: some response\n"
                    ),
                    stderr="",
                )
            if "--messaging-delete-sms" in " ".join(args):
                return subprocess.CompletedProcess(
                    args=args, returncode=0, stdout="", stderr="",
                )
            return subprocess.CompletedProcess(
                args=args, returncode=0, stdout="", stderr="",
            )

        with mock.patch("subprocess.run", side_effect=fake_run):
            messages = asyncio.run(self.dispatcher._fetch_mmcli_sms())

        # No se debe devolver ningun mensaje (es auto-generado)
        self.assertEqual(
            len(messages), 0,
            "SMS con modem_sms_id existente no debe devolverse como entrante",
        )

        # Verificar que se elimino del modem
        delete_calls = [
            a for a in call_log
            if any("--messaging-delete-sms" in str(arg) for arg in a)
        ]
        self.assertGreaterEqual(len(delete_calls), 1)

    def test_sms_without_existing_modem_id_is_processed(self):
        """Fix 3: SMS con modem_sms_id NO existente se procesa normalmente."""
        call_log = []

        def fake_run(args, **_kwargs):
            call_log.append(args)
            if "--messaging-list-sms" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=0,
                    stdout="/org/freedesktop/ModemManager1/SMS/99\n",
                    stderr="",
                )
            if "-s" in args and "--messaging-delete-sms" not in " ".join(args) and "--send" not in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=0,
                    stdout=(
                        "  SMS | /org/freedesktop/ModemManager1/SMS/99\n"
                        "    | state: received\n"
                        "    | number: +573001111111\n"
                        "    | text: hello world\n"
                    ),
                    stderr="",
                )
            if "--messaging-delete-sms" in " ".join(args):
                return subprocess.CompletedProcess(
                    args=args, returncode=0, stdout="", stderr="",
                )
            return subprocess.CompletedProcess(
                args=args, returncode=0, stdout="", stderr="",
            )

        with mock.patch("subprocess.run", side_effect=fake_run):
            messages = asyncio.run(self.dispatcher._fetch_mmcli_sms())

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0][0], "+573001111111")
        self.assertEqual(messages[0][1], "hello world")
        self.assertEqual(messages[0][2], "99")


if __name__ == "__main__":
    unittest.main()
