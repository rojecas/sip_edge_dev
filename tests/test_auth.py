"""Tests for authentication, JWT, RBAC, and inactivity."""

import os
import tempfile
import time
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.auth import (
    JWT_SECRET_KEY,
    ALGORITHM,
    create_access_token,
    hash_password,
)
from src.models import Base, User
from jose import jwt


def _build_test_app():
    import src.database as _db

    _engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=_engine)
    _SessionLocal = sessionmaker(bind=_engine)

    db = _SessionLocal()
    try:
        admin = User(
            username="admin",
            password_hash=hash_password("adminpass"),
            role="admin",
            full_name="Administrador",
            is_active=True,
        )
        operator = User(
            username="operator",
            password_hash=hash_password("operatorpass"),
            role="operator",
            full_name="Operador",
            is_active=True,
        )
        corresponsal = User(
            username="corresponsal",
            password_hash=hash_password("corrpass"),
            role="corresponsal",
            full_name="Corresponsal",
            is_active=True,
        )
        db.add_all([admin, operator, corresponsal])
        db.commit()
    finally:
        db.close()

    import src.main as main_mod

    main_mod.app.dependency_overrides.clear()

    main_mod.CONFIG_PATH = os.path.join(tempfile.mkdtemp(), "config.yaml")

    from src.config import BackupConfig, SessionConfig, SystemConfig, default_config

    main_mod.app.state.config = default_config()
    main_mod.app.state.session = SessionConfig(session_timeout_minutes=15)
    main_mod.app.state.backup_config = BackupConfig("/mnt/backup_usb", "/home/bkmngr/backups", 30)

    from src.database import get_db as _original_get_db

    def _override_get_db():
        s = _SessionLocal()
        try:
            yield s
        finally:
            s.close()

    main_mod.app.dependency_overrides[_original_get_db] = _override_get_db

    return TestClient(main_mod.app)


class TestLoginEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = _build_test_app()

    def test_login_valid_admin_returns_token(self):
        response = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "adminpass"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["role"], "admin")

    def test_login_valid_operator_returns_token(self):
        response = self.client.post(
            "/api/auth/login",
            json={"username": "operator", "password": "operatorpass"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["role"], "operator")

    def test_login_invalid_password_returns_401(self):
        response = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrongpass"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid username or password")

    def test_login_nonexistent_user_returns_401(self):
        response = self.client.post(
            "/api/auth/login",
            json={"username": "noone", "password": "pass"},
        )
        self.assertEqual(response.status_code, 401)

    def test_login_corresponsal_returns_403(self):
        response = self.client.post(
            "/api/auth/login",
            json={"username": "corresponsal", "password": "corrpass"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["detail"],
            "Corresponsal role does not permit system login",
        )

    def test_login_missing_username_returns_422(self):
        response = self.client.post(
            "/api/auth/login",
            json={"password": "pass"},
        )
        self.assertEqual(response.status_code, 422)

    def test_login_empty_body_returns_422(self):
        response = self.client.post(
            "/api/auth/login",
            json={},
        )
        self.assertEqual(response.status_code, 422)

    def test_login_empty_username_returns_422(self):
        response = self.client.post(
            "/api/auth/login",
            json={"username": "", "password": "pass"},
        )
        self.assertEqual(response.status_code, 422)


class TestAuthDependencies(unittest.TestCase):
    def setUp(self):
        self.client = _build_test_app()

    def _get_token(self, username="admin", password="adminpass"):
        response = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
        )
        return response.json()["access_token"]

    def test_valid_token_extracts_user(self):
        token = self._get_token()
        response = self.client.get(
            "/api/config",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)

    def test_no_token_returns_401(self):
        response = self.client.get("/api/config")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Not authenticated")

    def test_invalid_token_signature_returns_401(self):
        response = self.client.get(
            "/api/config",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        self.assertEqual(response.status_code, 401)

    def test_malformed_token_returns_401(self):
        response = self.client.get(
            "/api/config",
            headers={"Authorization": "Bearer notajwt"},
        )
        self.assertEqual(response.status_code, 401)

    def test_token_missing_sub_claim_returns_401(self):
        bad_token = jwt.encode(
            {"role": "admin", "iat": int(time.time())},
            JWT_SECRET_KEY,
            algorithm=ALGORITHM,
        )
        response = self.client.get(
            "/api/config",
            headers={"Authorization": f"Bearer {bad_token}"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid token", response.json()["detail"])

    def test_token_missing_role_claim_returns_401(self):
        bad_token = jwt.encode(
            {"sub": "1", "iat": int(time.time())},
            JWT_SECRET_KEY,
            algorithm=ALGORITHM,
        )
        response = self.client.get(
            "/api/config",
            headers={"Authorization": f"Bearer {bad_token}"},
        )
        self.assertEqual(response.status_code, 401)

    def test_token_missing_iat_claim_returns_401(self):
        bad_token = jwt.encode(
            {"sub": "1", "role": "admin"},
            JWT_SECRET_KEY,
            algorithm=ALGORITHM,
        )
        response = self.client.get(
            "/api/config",
            headers={"Authorization": f"Bearer {bad_token}"},
        )
        self.assertEqual(response.status_code, 401)

    def test_bearer_prefix_without_token_returns_401(self):
        response = self.client.get(
            "/api/config",
            headers={"Authorization": "Bearer "},
        )
        self.assertEqual(response.status_code, 401)


class TestRBAC(unittest.TestCase):
    def setUp(self):
        self.client = _build_test_app()

    def _login(self, username, password):
        response = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
        )
        return response.json()["access_token"]

    def test_admin_can_access_config(self):
        token = self._login("admin", "adminpass")
        response = self.client.get(
            "/api/config",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_setup_session(self):
        token = self._login("admin", "adminpass")
        response = self.client.put(
            "/api/setup/session",
            json={"session_timeout_minutes": 30},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)

    def test_operator_denied_access_to_config(self):
        token = self._login("operator", "operatorpass")
        response = self.client.get(
            "/api/config",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Insufficient permissions")

    def test_operator_denied_access_to_setup_session(self):
        token = self._login("operator", "operatorpass")
        response = self.client.put(
            "/api/setup/session",
            json={"session_timeout_minutes": 30},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)


class TestInactivity(unittest.TestCase):
    def setUp(self):
        self.client = _build_test_app()

    def test_fresh_token_passes_inactivity_check(self):
        token = create_access_token(1, "admin")
        response = self.client.get(
            "/api/config",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)

    def test_old_token_fails_inactivity_check(self):
        old_iat = int(time.time()) - 3600
        old_token = jwt.encode(
            {"sub": "1", "role": "admin", "iat": old_iat},
            JWT_SECRET_KEY,
            algorithm=ALGORITHM,
        )
        response = self.client.get(
            "/api/config",
            headers={"Authorization": f"Bearer {old_token}"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json()["detail"], "Session expired due to inactivity"
        )

    def test_public_endpoint_does_not_require_token(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)


class TestSessionEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = _build_test_app()

    def _get_admin_token(self):
        response = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "adminpass"},
        )
        return response.json()["access_token"]

    def _get_operator_token(self):
        response = self.client.post(
            "/api/auth/login",
            json={"username": "operator", "password": "operatorpass"},
        )
        return response.json()["access_token"]

    def test_admin_updates_session_timeout(self):
        token = self._get_admin_token()
        response = self.client.put(
            "/api/setup/session",
            json={"session_timeout_minutes": 30},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["session_timeout_minutes"], 30)

    def test_session_timeout_zero_returns_422(self):
        token = self._get_admin_token()
        response = self.client.put(
            "/api/setup/session",
            json={"session_timeout_minutes": 0},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 422)

    def test_session_timeout_negative_returns_422(self):
        token = self._get_admin_token()
        response = self.client.put(
            "/api/setup/session",
            json={"session_timeout_minutes": -5},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 422)

    def test_session_timeout_non_integer_returns_422(self):
        token = self._get_admin_token()
        response = self.client.put(
            "/api/setup/session",
            json={"session_timeout_minutes": "abc"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 422)

    def test_session_without_token_returns_401(self):
        response = self.client.put(
            "/api/setup/session",
            json={"session_timeout_minutes": 30},
        )
        self.assertEqual(response.status_code, 401)

    def test_session_with_operator_returns_403(self):
        token = self._get_operator_token()
        response = self.client.put(
            "/api/setup/session",
            json={"session_timeout_minutes": 30},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)


class TestTokenStructure(unittest.TestCase):
    def test_token_contains_correct_claims(self):
        token = create_access_token(42, "admin")
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        self.assertEqual(payload["sub"], "42")
        self.assertEqual(payload["role"], "admin")
        self.assertIn("iat", payload)
        self.assertIsInstance(payload["iat"], int)
        self.assertIn("session_timeout_minutes", payload)
        self.assertIsInstance(payload["session_timeout_minutes"], int)

    def test_token_contains_custom_timeout(self):
        token = create_access_token(1, "operator", session_timeout_minutes=60)
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        self.assertEqual(payload["session_timeout_minutes"], 60)


class TestRefreshToken(unittest.TestCase):
    def setUp(self):
        self.client = _build_test_app()

    def _get_admin_token(self):
        response = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "adminpass"},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_refresh_token_returns_new_jwt(self):
        """POST /api/auth/refresh returns a new JWT with fresh iat."""
        import time as _time

        data = self._get_admin_token()
        old_token = data["access_token"]
        old_payload = jwt.decode(old_token, JWT_SECRET_KEY, algorithms=[ALGORITHM])

        # Wait 1s so the new token gets a different iat
        _time.sleep(1)

        response = self.client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {old_token}"},
        )
        self.assertEqual(response.status_code, 200)
        new_data = response.json()
        self.assertIn("access_token", new_data)
        self.assertEqual(new_data["token_type"], "bearer")
        self.assertEqual(new_data["role"], "admin")

        # New token string is different from old token
        self.assertNotEqual(new_data["access_token"], old_token)

        new_payload = jwt.decode(
            new_data["access_token"], JWT_SECRET_KEY, algorithms=[ALGORITHM]
        )
        # New token has greater iat
        self.assertGreater(new_payload["iat"], old_payload["iat"])
        # Same user and role
        self.assertEqual(new_payload["sub"], old_payload["sub"])
        self.assertEqual(new_payload["role"], old_payload["role"])
        # New token has session_timeout_minutes
        self.assertIn("session_timeout_minutes", new_payload)

    def test_refresh_token_requires_auth(self):
        """POST /api/auth/refresh without token returns 401."""
        response = self.client.post("/api/auth/refresh")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Not authenticated")


def _build_test_app_with_sms_mock():
    """Construye TestClient con un SMSService mockeado en app.state."""
    import src.database as _db
    from unittest import mock as umock

    _engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=_engine)
    _SessionLocal = sessionmaker(bind=_engine)

    db = _SessionLocal()
    try:
        admin = User(
            username="admin",
            password_hash=hash_password("adminpass"),
            role="admin",
            full_name="Administrador",
            is_active=True,
        )
        operator = User(
            username="operator",
            password_hash=hash_password("operatorpass"),
            role="operator",
            full_name="Operador",
            is_active=True,
        )
        db.add_all([admin, operator])
        db.commit()
    finally:
        db.close()

    import src.main as main_mod
    from src.config import BackupConfig, ScaleConfig, SessionConfig, SmsConfig, default_config

    main_mod.app.dependency_overrides.clear()
    main_mod.CONFIG_PATH = os.path.join(tempfile.mkdtemp(), "config.yaml")

    main_mod.app.state.config = default_config()
    main_mod.app.state.session = SessionConfig(session_timeout_minutes=15)
    main_mod.app.state.scale_config = ScaleConfig(timeout_seconds=3)
    main_mod.app.state.backup_config = BackupConfig("/mnt/backup_usb", "/home/bkmngr/backups", 30)
    main_mod.app.state.sms_config = SmsConfig(
        admin_phones=["+573001234567"],
        scheduled_reports=["06:00", "14:00", "22:00"],
    )

    sms_mock = umock.MagicMock()
    main_mod.app.state.sms_service = sms_mock

    from src.database import get_db as _original_get_db

    def _override_get_db():
        s = _SessionLocal()
        try:
            yield s
        finally:
            s.close()

    main_mod.app.dependency_overrides[_original_get_db] = _override_get_db

    return TestClient(main_mod.app), sms_mock, _SessionLocal


class TestLoginFailedAttempts(unittest.TestCase):
    def setUp(self):
        self.client, self.sms_mock, self.SessionLocal = _build_test_app_with_sms_mock()

    def _count_failed_attempts(self, username):
        """Obtiene el contador de intentos fallidos desde la BD."""
        s = self.SessionLocal()
        try:
            user = s.query(User).filter(User.username == username).first()
            return user.failed_login_attempts if user else None
        finally:
            s.close()

    def test_login_failed_increments_counter(self):
        """R3: 1 login fallido incrementa el contador a 1."""
        self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrongpass"},
        )
        self.assertEqual(self._count_failed_attempts("admin"), 1)

    def test_login_failed_does_not_alert_before_3(self):
        """R2: Con 1 o 2 fallos NO se envia alerta."""
        # 1 fallo
        self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrongpass"},
        )
        self.sms_mock.send_alert_to_admins.assert_not_called()
        self.assertEqual(self._count_failed_attempts("admin"), 1)

        # 2 fallos
        self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrongpass"},
        )
        self.sms_mock.send_alert_to_admins.assert_not_called()
        self.assertEqual(self._count_failed_attempts("admin"), 2)

    def test_login_failed_triggers_alert_at_3(self):
        """R2: En el 3er fallo se llama a send_alert_to_admins."""
        for _ in range(2):
            self.client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "wrongpass"},
            )
        self.sms_mock.send_alert_to_admins.assert_not_called()

        # 3er fallo
        self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrongpass"},
        )
        self.sms_mock.send_alert_to_admins.assert_called_once()
        alert_arg = self.sms_mock.send_alert_to_admins.call_args[0][0]
        self.assertIn("admin", alert_arg)
        self.assertIn("3", alert_arg)

    def test_login_failed_resets_after_alert(self):
        """R4: Tras la alerta el contador vuelve a 0."""
        for _ in range(3):
            self.client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "wrongpass"},
            )
        self.assertEqual(self._count_failed_attempts("admin"), 0)

    def test_login_success_resets_counter(self):
        """R3: Login exitoso pone el contador a 0."""
        # Primero provocar algunos intentos fallidos
        self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrongpass"},
        )
        self.assertEqual(self._count_failed_attempts("admin"), 1)

        # Luego login exitoso
        self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "adminpass"},
        )
        self.assertEqual(self._count_failed_attempts("admin"), 0)

    def test_login_failed_counter_increments_separately_per_user(self):
        """R3: Cada usuario tiene su propio contador independiente."""
        # Admin falla una vez
        self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrongpass"},
        )
        self.assertEqual(self._count_failed_attempts("admin"), 1)

        # Operator falla una vez
        self.client.post(
            "/api/auth/login",
            json={"username": "operator", "password": "wrongpass"},
        )
        self.assertEqual(self._count_failed_attempts("operator"), 1)

        # Admin sigue teniendo 1
        self.assertEqual(self._count_failed_attempts("admin"), 1)

    def test_login_failed_triggers_alert_only_once_per_batch(self):
        """R4: Alertas no repetidas sin nuevos intentos tras el reset."""
        for _ in range(3):
            self.client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "wrongpass"},
            )
        # La primera rafaga de 3 dispara la alerta y resetea
        self.assertEqual(self.sms_mock.send_alert_to_admins.call_count, 1)
        self.assertEqual(self._count_failed_attempts("admin"), 0)

        # Una segunda rafaga de 3 fallos debe disparar otra alerta
        for _ in range(3):
            self.client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "wrongpass"},
            )
        self.assertEqual(self.sms_mock.send_alert_to_admins.call_count, 2)
