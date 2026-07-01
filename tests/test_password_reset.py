"""Tests for password reset via SMS: parser, service, endpoints, dispatcher."""

import os
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.auth import hash_password, verify_password
from src.models import Base, User
from src.password_reset import (
    PasswordResetError,
    InvalidPinError,
    PasswordResetService,
    VerifyResetPinRequest,
    CompleteResetRequest,
    _parse_reset_command,
)
from src.sms_incoming import IncomingSmsDispatcher


# ==================================================================
# Common test setup
# ==================================================================


def _build_test_db_engine():
    """Crea un engine SQLite en memoria."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


def _create_test_users(db):
    """Crea usuarios de prueba en la BD."""
    admin = User(
        username="admin",
        password_hash=hash_password("adminpass"),
        role="admin",
        full_name="Administrador",
        is_active=True,
        phone="+573001111111",
    )
    operator = User(
        username="operator1",
        password_hash=hash_password("oppass"),
        role="operator",
        full_name="Operador Uno",
        is_active=True,
        phone="+573002222222",
    )
    no_phone = User(
        username="nophone",
        password_hash=hash_password("nopass"),
        role="operator",
        full_name="Sin Telefono",
        is_active=True,
        phone=None,
    )
    db.add_all([admin, operator, no_phone])
    db.commit()
    db.refresh(admin)
    db.refresh(operator)
    db.refresh(no_phone)
    return admin, operator, no_phone


# ==================================================================
# T15: Parser tests
# ==================================================================


class TestParseResetCommand(unittest.TestCase):
    """Tests para _parse_reset_command (R1)."""

    def test_parse_reset_command_basic(self):
        """'reset password juan' -> 'juan'."""
        result = _parse_reset_command("reset password juan")
        self.assertEqual(result, "juan")

    def test_parse_reset_command_case_insensitive(self):
        """'RESET PASSWORD ANA' -> 'ANA' (case-insensitive)."""
        result = _parse_reset_command("RESET PASSWORD ANA")
        self.assertEqual(result, "ANA")

    def test_parse_reset_command_mixed_case(self):
        """'Reset Password Pedro' -> 'Pedro'."""
        result = _parse_reset_command("Reset Password Pedro")
        self.assertEqual(result, "Pedro")

    def test_parse_reset_command_extra_spaces(self):
        """Espacios extra al inicio/final se toleran."""
        result = _parse_reset_command("  reset password  luis  ")
        self.assertEqual(result, "luis")

    def test_parse_reset_command_not_matching(self):
        """'hello world' -> None."""
        result = _parse_reset_command("hello world")
        self.assertIsNone(result)

    def test_parse_reset_command_partial_no_username(self):
        """'reset password' sin username -> None."""
        result = _parse_reset_command("reset password")
        self.assertIsNone(result)

    def test_parse_reset_command_manual_on_not_matching(self):
        """'manual on' -> None (no es comando de reset)."""
        result = _parse_reset_command("manual on")
        self.assertIsNone(result)

    def test_parse_reset_command_multiple_spaces(self):
        """Multiples espacios entre palabras se toleran."""
        result = _parse_reset_command("reset   password    user1")
        self.assertEqual(result, "user1")

    def test_parse_reset_command_username_with_special_chars(self):
        """Username con caracteres especiales funciona."""
        result = _parse_reset_command("reset password user.name_123")
        self.assertEqual(result, "user.name_123")


# ==================================================================
# T14: PasswordResetService unit tests
# ==================================================================


class TestGenerateAndSendPin(unittest.TestCase):
    """Tests para generate_and_send_pin (R2, R3, R4, R5, R6)."""

    @classmethod
    def setUpClass(cls):
        cls._engine = _build_test_db_engine()
        cls._SessionLocal = sessionmaker(bind=cls._engine)

    def setUp(self):
        db = self._SessionLocal()
        try:
            db.query(User).delete()
            db.commit()
        finally:
            db.close()

        db = self._SessionLocal()
        try:
            self.admin, self.operator, self.no_phone = _create_test_users(db)
        finally:
            db.close()

        self.sms_mock = mock.MagicMock()
        self.sms_mock.send_sms.return_value = True
        self.svc = PasswordResetService(
            db_session_factory=self._SessionLocal,
            sms_service=self.sms_mock,
        )

    def test_generate_pin_range(self):
        """R4: PIN generado esta en rango 1000-9999."""
        success = self.svc.generate_and_send_pin(
            "operator1", "+573001111111"
        )
        self.assertTrue(success)

        # Verificar que se envio SMS con PIN
        self.sms_mock.send_sms.assert_called()
        # El primer argumento es el phone del usuario
        call_args = self.sms_mock.send_sms.call_args
        self.assertEqual(call_args[0][0], "+573002222222")
        # El mensaje contiene un PIN de 4 digitos
        import re
        match = re.search(r"\b(\d{4})\b", call_args[0][1])
        self.assertIsNotNone(match, f"No PIN found in SMS text: {call_args[0][1]}")
        pin = int(match.group(1))
        self.assertGreaterEqual(pin, 1000)
        self.assertLessEqual(pin, 9999)

    def test_generate_pin_hash_stored(self):
        """R5: reset_pin almacena hash bcrypt, NO texto plano."""
        self.svc.generate_and_send_pin("operator1", "+573001111111")

        db = self._SessionLocal()
        try:
            user = db.query(User).filter(User.username == "operator1").first()
            self.assertIsNotNone(user.reset_pin)
            self.assertNotEqual(user.reset_pin, "")
            # Debe ser un hash bcrypt (empieza con $2b$ o $2a$)
            self.assertTrue(
                user.reset_pin.startswith("$2"),
                f"reset_pin should be bcrypt hash, got: {user.reset_pin[:20]}",
            )
            # El hash NO debe ser el PIN en texto plano
            import re as _re
            # Extract PIN from SMS text
            call_args = self.sms_mock.send_sms.call_args
            pin_match = _re.search(r"\b(\d{4})\b", call_args[0][1])
            pin_text = pin_match.group(1)
            self.assertNotEqual(user.reset_pin, pin_text)
        finally:
            db.close()

    def test_generate_pin_expires_at(self):
        """R5: reset_pin_expires_at ≈ now + 1h (±5 seg tolerance)."""
        before = datetime.now(timezone.utc)
        self.svc.generate_and_send_pin("operator1", "+573001111111")
        after = datetime.now(timezone.utc)

        db = self._SessionLocal()
        try:
            user = db.query(User).filter(User.username == "operator1").first()
            self.assertIsNotNone(user.reset_pin_expires_at)
            expires = user.reset_pin_expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)

            expected = before + timedelta(hours=1)
            # Should be close to now + 1h
            delta = abs((expires - expected).total_seconds())
            self.assertLess(delta, 10, f"Expires {expires} not within 10s of {expected}")
        finally:
            db.close()

    def test_generate_pin_force_password_change(self):
        """R5: force_password_change = True tras generar PIN."""
        self.svc.generate_and_send_pin("operator1", "+573001111111")

        db = self._SessionLocal()
        try:
            user = db.query(User).filter(User.username == "operator1").first()
            self.assertTrue(user.force_password_change)
        finally:
            db.close()

    def test_generate_pin_no_user(self):
        """R2: Usuario no existe -> False + SMS de error."""
        success = self.svc.generate_and_send_pin(
            "noexiste", "+573001111111"
        )
        self.assertFalse(success)
        # Debe enviar SMS de error al remitente
        self.sms_mock.send_sms.assert_called_once()
        call_args = self.sms_mock.send_sms.call_args
        self.assertEqual(call_args[0][0], "+573001111111")
        self.assertIn("no encontrado", call_args[0][1].lower())

    def test_generate_pin_no_phone(self):
        """R3: Usuario sin telefono -> False + SMS de error."""
        success = self.svc.generate_and_send_pin(
            "nophone", "+573001111111"
        )
        self.assertFalse(success)
        self.sms_mock.send_sms.assert_called_once()
        call_args = self.sms_mock.send_sms.call_args
        self.assertEqual(call_args[0][0], "+573001111111")
        self.assertIn("telefono", call_args[0][1].lower())

    def test_generate_pin_case_insensitive_username(self):
        """Username case-insensitive funciona."""
        success = self.svc.generate_and_send_pin(
            "OPERATOR1", "+573001111111"
        )
        self.assertTrue(success)
        self.sms_mock.send_sms.assert_called()

    def test_generate_pin_multiple_generations_invalidate_previous(self):
        """Llamadas multiples generan nuevos PINs (cada uno reemplaza al anterior)."""
        self.svc.generate_and_send_pin("operator1", "+573001111111")
        db = self._SessionLocal()
        try:
            user1 = db.query(User).filter(User.username == "operator1").first()
            first_hash = user1.reset_pin
            first_expires = user1.reset_pin_expires_at
        finally:
            db.close()

        # Esperar 1 segundo para garantizar diferente expires_at
        import time as _time
        _time.sleep(1.1)

        self.svc.generate_and_send_pin("operator1", "+573001111111")
        db = self._SessionLocal()
        try:
            user2 = db.query(User).filter(User.username == "operator1").first()
            second_hash = user2.reset_pin
            second_expires = user2.reset_pin_expires_at
        finally:
            db.close()

        # Los hashes deberian ser diferentes (PINs diferentes)
        self.assertNotEqual(first_hash, second_hash)
        # Expira mas tarde la segunda vez
        self.assertGreater(second_expires, first_expires)


# ==================================================================
# T16, T17: Integration tests for API endpoints
# ==================================================================


def _build_test_app():
    """Construye una aplicacion FastAPI con BD en memoria para tests."""
    import src.database as _db

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    _db.engine = engine
    _db.SessionLocal = sessionmaker(bind=engine)

    db = _db.SessionLocal()
    try:
        admin, operator, no_phone = _create_test_users(db)
        self_admin_id = admin.id
        self_operator_id = operator.id
    finally:
        db.close()

    import src.main as main_mod

    main_mod.app.dependency_overrides.clear()

    main_mod.CONFIG_PATH = os.path.join(tempfile.mkdtemp(), "config.yaml")

    from src.config import (
        BackupConfig,
        ScaleConfig,
        SessionConfig,
        SmsConfig,
        default_config,
    )

    main_mod.app.state.config = default_config()
    main_mod.app.state.session = SessionConfig(session_timeout_minutes=15)
    main_mod.app.state.scale_config = ScaleConfig(timeout_seconds=3)
    main_mod.app.state.backup_config = BackupConfig(
        "/mnt/backup_usb", "/home/bkmngr/backups", 30
    )
    main_mod.app.state.sms_config = SmsConfig(
        admin_phones=["+573001111111"],
        scheduled_reports=["06:00", "14:00", "22:00"],
    )
    main_mod.app.state.scale_service = None
    main_mod.app.state.sms_service = mock.MagicMock()
    main_mod.app.state.emergency_service = mock.MagicMock()

    from src.database import get_db as _original_get_db

    def _override_get_db():
        s = _db.SessionLocal()
        try:
            yield s
        finally:
            s.close()

    main_mod.app.dependency_overrides[_original_get_db] = _override_get_db

    return TestClient(main_mod.app), self_operator_id


class TestVerifyResetPinAPI(unittest.TestCase):
    """Tests de integracion para POST /api/auth/verify-reset-pin (R7, R8, R9)."""

    @classmethod
    def setUpClass(cls):
        cls.client, cls.operator_id = _build_test_app()

    def setUp(self):
        # Cleanup reset fields
        import src.database as _db
        db = _db.SessionLocal()
        try:
            db.query(User).update({
                "reset_pin": None,
                "reset_pin_expires_at": None,
                "force_password_change": False,
            })
            db.commit()
        finally:
            db.close()

    def _setup_pin(self, username="operator1", pin="1234", expires_delta_hours=1):
        """Configura un PIN valido para el usuario dado."""
        import src.database as _db
        db = _db.SessionLocal()
        try:
            user = db.query(User).filter(User.username == username).first()
            self.assertIsNotNone(user, f"User {username} not found")
            user.reset_pin = hash_password(pin)
            user.reset_pin_expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_delta_hours)
            user.force_password_change = True
            db.commit()
        finally:
            db.close()

    def test_verify_pin_success(self):
        """R7, R8: PIN correcto -> reset_token emitido + campos limpiados."""
        self._setup_pin("operator1", "1234")

        resp = self.client.post(
            "/api/auth/verify-reset-pin",
            json={"username": "operator1", "pin": "1234"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("reset_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertGreater(len(data["reset_token"]), 10)

        # Verificar que reset_pin fue limpiado (single-use)
        import src.database as _db
        db = _db.SessionLocal()
        try:
            user = db.query(User).filter(User.username == "operator1").first()
            self.assertIsNone(user.reset_pin)
            self.assertIsNone(user.reset_pin_expires_at)
        finally:
            db.close()

    def test_verify_pin_wrong(self):
        """R9: PIN incorrecto -> 401."""
        self._setup_pin("operator1", "1234")

        resp = self.client.post(
            "/api/auth/verify-reset-pin",
            json={"username": "operator1", "pin": "9999"},
        )
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()["detail"], "Invalid username or PIN")

    def test_verify_pin_no_user(self):
        """R9: Username no existe -> 401."""
        resp = self.client.post(
            "/api/auth/verify-reset-pin",
            json={"username": "noexiste", "pin": "1234"},
        )
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()["detail"], "Invalid username or PIN")

    def test_verify_pin_no_pin_set(self):
        """R9: reset_pin es NULL -> 401."""
        resp = self.client.post(
            "/api/auth/verify-reset-pin",
            json={"username": "operator1", "pin": "1234"},
        )
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()["detail"], "Invalid username or PIN")

    def test_verify_pin_expired(self):
        """R9: PIN expirado -> 401."""
        self._setup_pin("operator1", "1234", expires_delta_hours=-1)

        resp = self.client.post(
            "/api/auth/verify-reset-pin",
            json={"username": "operator1", "pin": "1234"},
        )
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()["detail"], "Invalid username or PIN")

    def test_verify_pin_already_used(self):
        """R9: PIN ya usado (reset_pin=NULL tras primer uso) -> 401."""
        self._setup_pin("operator1", "1234")

        # Primer intento: OK
        resp1 = self.client.post(
            "/api/auth/verify-reset-pin",
            json={"username": "operator1", "pin": "1234"},
        )
        self.assertEqual(resp1.status_code, 200)

        # Segundo intento: PIN ya invalidado
        resp2 = self.client.post(
            "/api/auth/verify-reset-pin",
            json={"username": "operator1", "pin": "1234"},
        )
        self.assertEqual(resp2.status_code, 401)
        self.assertEqual(resp2.json()["detail"], "Invalid username or PIN")

    def test_verify_pin_case_insensitive_username(self):
        """Username case-insensitive en verificacion."""
        self._setup_pin("operator1", "5678")

        resp = self.client.post(
            "/api/auth/verify-reset-pin",
            json={"username": "OPERATOR1", "pin": "5678"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("reset_token", resp.json())

    def test_verify_pin_short_pin(self):
        """PIN de menos de 4 digitos -> 422."""
        resp = self.client.post(
            "/api/auth/verify-reset-pin",
            json={"username": "operator1", "pin": "12"},
        )
        self.assertEqual(resp.status_code, 422)

    def test_verify_pin_long_pin(self):
        """PIN de mas de 4 digitos -> 422."""
        resp = self.client.post(
            "/api/auth/verify-reset-pin",
            json={"username": "operator1", "pin": "12345"},
        )
        self.assertEqual(resp.status_code, 422)


class TestCompleteResetAPI(unittest.TestCase):
    """Tests de integracion para POST /api/auth/complete-reset (R10, R11, R12)."""

    @classmethod
    def setUpClass(cls):
        cls.client, cls.operator_id = _build_test_app()

    def setUp(self):
        import src.database as _db
        db = _db.SessionLocal()
        try:
            db.query(User).update({
                "reset_pin": None,
                "reset_pin_expires_at": None,
                "force_password_change": False,
            })
            db.commit()
        finally:
            db.close()

    def _get_reset_token(self, username="operator1", pin="1234"):
        """Obtiene un reset_token valido configurando un PIN primero."""
        import src.database as _db
        db = _db.SessionLocal()
        try:
            user = db.query(User).filter(User.username == username).first()
            user.reset_pin = hash_password(pin)
            user.reset_pin_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            user.force_password_change = True
            db.commit()
        finally:
            db.close()

        resp = self.client.post(
            "/api/auth/verify-reset-pin",
            json={"username": username, "pin": pin},
        )
        self.assertEqual(resp.status_code, 200)
        return resp.json()["reset_token"]

    def test_complete_reset_success(self):
        """R10, R11: Cambio de contrasena exitoso."""
        token = self._get_reset_token("operator1")

        resp = self.client.post(
            "/api/auth/complete-reset",
            json={
                "reset_token": token,
                "new_password": "newsecret",
                "confirm_password": "newsecret",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["message"], "Password updated successfully")

        # Verificar que la contrasena se actualizo
        import src.database as _db
        db = _db.SessionLocal()
        try:
            user = db.query(User).filter(User.username == "operator1").first()
            self.assertTrue(verify_password("newsecret", user.password_hash))
            self.assertFalse(user.force_password_change)
            self.assertIsNone(user.reset_pin)
            self.assertIsNone(user.reset_pin_expires_at)
        finally:
            db.close()

    def test_complete_reset_clears_force_password_change(self):
        """R11: force_password_change pasa a False tras completar."""
        token = self._get_reset_token("operator1")

        resp = self.client.post(
            "/api/auth/complete-reset",
            json={
                "reset_token": token,
                "new_password": "anotherpass",
                "confirm_password": "anotherpass",
            },
        )
        self.assertEqual(resp.status_code, 200)

        import src.database as _db
        db = _db.SessionLocal()
        try:
            user = db.query(User).filter(User.username == "operator1").first()
            self.assertFalse(user.force_password_change)
        finally:
            db.close()

    def test_complete_reset_invalid_token(self):
        """R12: Token invalido -> 401."""
        resp = self.client.post(
            "/api/auth/complete-reset",
            json={
                "reset_token": "invalid.token.here",
                "new_password": "newpass",
                "confirm_password": "newpass",
            },
        )
        self.assertEqual(resp.status_code, 401)
        self.assertIn("Invalid or expired reset token", resp.json()["detail"])

    def test_complete_reset_expired_token(self):
        """R12: Token expirado -> 401."""
        from jose import jwt as jose_jwt
        import src.auth as auth_mod

        old_token = jose_jwt.encode(
            {
                "sub": str(self.operator_id),
                "purpose": "password_reset",
                "iat": int(time.time()) - 600,
                "exp": int(time.time()) - 300,  # expirado
            },
            auth_mod.JWT_SECRET_KEY,
            algorithm=auth_mod.ALGORITHM,
        )

        resp = self.client.post(
            "/api/auth/complete-reset",
            json={
                "reset_token": old_token,
                "new_password": "newpass",
                "confirm_password": "newpass",
            },
        )
        self.assertEqual(resp.status_code, 401)

    def test_complete_reset_mismatch(self):
        """R12: Contrasenas no coinciden -> 422."""
        token = self._get_reset_token("operator1")

        resp = self.client.post(
            "/api/auth/complete-reset",
            json={
                "reset_token": token,
                "new_password": "pass1",
                "confirm_password": "pass2",
            },
        )
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["detail"], "Passwords do not match")

    def test_complete_reset_clears_reset_fields(self):
        """R11: reset_pin y reset_pin_expires_at son NULL tras completar."""
        token = self._get_reset_token("operator1")

        resp = self.client.post(
            "/api/auth/complete-reset",
            json={
                "reset_token": token,
                "new_password": "clearpass",
                "confirm_password": "clearpass",
            },
        )
        self.assertEqual(resp.status_code, 200)

        import src.database as _db
        db = _db.SessionLocal()
        try:
            user = db.query(User).filter(User.username == "operator1").first()
            self.assertIsNone(user.reset_pin)
            self.assertIsNone(user.reset_pin_expires_at)
        finally:
            db.close()

    def test_complete_reset_empty_password(self):
        """Empty new_password -> 422 (min_length=1)."""
        token = self._get_reset_token("operator1")

        resp = self.client.post(
            "/api/auth/complete-reset",
            json={
                "reset_token": token,
                "new_password": "",
                "confirm_password": "",
            },
        )
        self.assertEqual(resp.status_code, 422)

    def test_complete_reset_prevents_login_with_old_password(self):
        """La vieja contrasena ya no funciona tras el reset."""
        token = self._get_reset_token("operator1")

        resp = self.client.post(
            "/api/auth/complete-reset",
            json={
                "reset_token": token,
                "new_password": "completelynew",
                "confirm_password": "completelynew",
            },
        )
        self.assertEqual(resp.status_code, 200)

        # Intentar login con contrasena antigua debe fallar
        login_resp = self.client.post(
            "/api/auth/login",
            json={"username": "operator1", "password": "oppass"},
        )
        self.assertEqual(login_resp.status_code, 401)

        # Login con nueva contrasena debe funcionar
        login_resp2 = self.client.post(
            "/api/auth/login",
            json={"username": "operator1", "password": "completelynew"},
        )
        self.assertEqual(login_resp2.status_code, 200)


# ==================================================================
# T18: IncomingSmsDispatcher tests
# ==================================================================


class TestIncomingSmsDispatcher(unittest.TestCase):
    """Tests para IncomingSmsDispatcher (R1 infraestructura)."""

    def setUp(self):
        self.dispatcher = IncomingSmsDispatcher(modem_index=0, dev_mode=True)

    def test_register_and_dispatch(self):
        """Handler registrado recibe SMS."""
        received: list[tuple[str, str]] = []

        def handler(phone: str, text: str) -> bool:
            received.append((phone, text))
            return True

        self.dispatcher.register_handler(handler)
        self.dispatcher.enqueue_incoming_sms("+573001111111", "reset password juan")

        # Ejecutar un ciclo de polling sincrono
        import asyncio
        async def run_one_cycle():
            # Acceder al metodo interno directamente
            await self.dispatcher._check_incoming_sms()

        asyncio.get_event_loop().run_until_complete(run_one_cycle())

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], ("+573001111111", "reset password juan"))

    def test_handler_returns_true_stops_chain(self):
        """Si el primer handler retorna True, el segundo no se ejecuta."""
        first_called = []
        second_called = []

        def handler1(phone, text):
            first_called.append(text)
            return True

        def handler2(phone, text):
            second_called.append(text)
            return True

        self.dispatcher.register_handler(handler1)
        self.dispatcher.register_handler(handler2)
        self.dispatcher.enqueue_incoming_sms("+57", "test")

        import asyncio
        async def run():
            await self.dispatcher._check_incoming_sms()

        asyncio.get_event_loop().run_until_complete(run())

        self.assertEqual(len(first_called), 1)
        self.assertEqual(len(second_called), 0)

    def test_handler_returns_false_continues_chain(self):
        """Si el primer handler retorna False, el segundo se ejecuta."""
        first_called = []
        second_called = []

        def handler1(phone, text):
            first_called.append(text)
            return False

        def handler2(phone, text):
            second_called.append(text)
            return True

        self.dispatcher.register_handler(handler1)
        self.dispatcher.register_handler(handler2)
        self.dispatcher.enqueue_incoming_sms("+57", "test")

        import asyncio
        async def run():
            await self.dispatcher._check_incoming_sms()

        asyncio.get_event_loop().run_until_complete(run())

        self.assertEqual(len(first_called), 1)
        self.assertEqual(len(second_called), 1)

    def test_dev_mode_queue(self):
        """Dev mode: enqueue_incoming_sms funciona con la cola interna."""
        received = []

        def handler(phone, text):
            received.append(text)
            return True

        self.dispatcher.register_handler(handler)

        # Encolar multiples mensajes
        self.dispatcher.enqueue_incoming_sms("+57", "msg1")
        self.dispatcher.enqueue_incoming_sms("+57", "msg2")
        self.dispatcher.enqueue_incoming_sms("+57", "msg3")

        import asyncio
        async def run():
            await self.dispatcher._check_incoming_sms()

        asyncio.get_event_loop().run_until_complete(run())

        self.assertEqual(len(received), 3)
        self.assertEqual(received, ["msg1", "msg2", "msg3"])

    def test_handler_exception_does_not_crash_dispatcher(self):
        """Si un handler lanza excepcion, el dispatcher continua."""
        def bad_handler(phone, text):
            raise RuntimeError("Handler error")

        second_called = []
        def good_handler(phone, text):
            second_called.append(text)
            return True

        self.dispatcher.register_handler(bad_handler)
        self.dispatcher.register_handler(good_handler)
        self.dispatcher.enqueue_incoming_sms("+57", "test")

        import asyncio
        async def run():
            await self.dispatcher._check_incoming_sms()

        # No debe lanzar excepcion
        asyncio.get_event_loop().run_until_complete(run())
        self.assertEqual(len(second_called), 1)


# ==================================================================
# T19: UserResponse hides reset fields
# ==================================================================


class TestUserResponseHidesResetFields(unittest.TestCase):
    """Tests para UserResponse exclusion de campos sensibles (R14)."""

    @classmethod
    def setUpClass(cls):
        cls.client, cls.operator_id = _build_test_app()

    def _login_admin(self):
        resp = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "adminpass"},
        )
        return resp.json()["access_token"]

    def setUp(self):
        # Set up reset fields on a user
        import src.database as _db
        db = _db.SessionLocal()
        try:
            user = db.query(User).filter(User.username == "operator1").first()
            user.reset_pin = hash_password("1234")
            user.reset_pin_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            user.force_password_change = True
            db.commit()
        finally:
            db.close()

    def test_user_list_hides_reset_pin(self):
        """GET /api/users no incluye reset_pin."""
        token = self._login_admin()
        resp = self.client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        for user in data["items"]:
            self.assertNotIn("reset_pin", user)
            self.assertNotIn("reset_pin_expires_at", user)

    def test_user_get_hides_reset_fields(self):
        """GET /api/users/{id} no incluye reset_pin ni reset_pin_expires_at."""
        token = self._login_admin()
        resp = self.client.get(
            f"/api/users/{self.operator_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertNotIn("reset_pin", data)
        self.assertNotIn("reset_pin_expires_at", data)

    def test_user_response_includes_force_password_change(self):
        """GET /api/users incluye force_password_change."""
        token = self._login_admin()
        resp = self.client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        operator_user = [u for u in data["items"] if u["username"] == "operator1"]
        self.assertEqual(len(operator_user), 1)
        self.assertTrue(operator_user[0]["force_password_change"])


# ==================================================================
# Test models for validation
# ==================================================================


class TestPasswordResetModels(unittest.TestCase):
    """Tests para schemas Pydantic."""

    def test_verify_reset_pin_request_valid(self):
        req = VerifyResetPinRequest(username="juan", pin="1234")
        self.assertEqual(req.username, "juan")
        self.assertEqual(req.pin, "1234")

    def test_verify_reset_pin_request_empty_username(self):
        with self.assertRaises(Exception):
            VerifyResetPinRequest(username="", pin="1234")

    def test_verify_reset_pin_request_short_pin(self):
        with self.assertRaises(Exception):
            VerifyResetPinRequest(username="juan", pin="12")

    def test_verify_reset_pin_request_long_pin(self):
        with self.assertRaises(Exception):
            VerifyResetPinRequest(username="juan", pin="12345")

    def test_complete_reset_request_valid(self):
        req = CompleteResetRequest(
            reset_token="jwt.token.here",
            new_password="newpass",
            confirm_password="newpass",
        )
        self.assertEqual(req.new_password, "newpass")

    def test_complete_reset_request_empty_token(self):
        with self.assertRaises(Exception):
            CompleteResetRequest(
                reset_token="",
                new_password="pass",
                confirm_password="pass",
            )

    def test_complete_reset_request_empty_password(self):
        with self.assertRaises(Exception):
            CompleteResetRequest(
                reset_token="token",
                new_password="",
                confirm_password="",
            )


# ==================================================================
# T20: Login page HTML tests (R15, R16)
# ==================================================================


if __name__ == "__main__":
    unittest.main()
