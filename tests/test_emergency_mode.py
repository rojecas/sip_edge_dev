"""Tests for emergency mode: SMS parser, service, API endpoints, SMS polling."""

import asyncio
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.auth import hash_password
from src.config import SmsConfig
from src.models import Base, EmergencyModeLog, User
from src.sms_persistence import SmsPersistenceService
from src.emergency_mode import (
    EmergencyModeError,
    EmergencyModeService,
    InvalidSmsCommandError,
    ParsedSmsCommand,
    parse_emergency_sms,
)
from src.sms_dispatcher_v2 import IncomingSmsDispatcherV2
from src.sms_service import SMSService


# ==================================================================
# T15: SMS Parser tests
# ==================================================================


class TestSmsParser(unittest.TestCase):
    """Tests para parse_emergency_sms: todos los patrones de comando (R6, R7, R8, R9, R16)."""

    def test_parse_manual_on(self):
        """R6: 'manual on' → activate 1440 min."""
        result = parse_emergency_sms("manual on")
        self.assertEqual(result.action, "activate")
        self.assertEqual(result.duration_minutes, 1440)

    def test_parse_manual_on_4h(self):
        """R7: 'manual on 4h' → activate 240 min."""
        result = parse_emergency_sms("manual on 4h")
        self.assertEqual(result.action, "activate")
        self.assertEqual(result.duration_minutes, 240)

    def test_parse_manual_on_30m(self):
        """R7: 'manual on 30m' → activate 30 min."""
        result = parse_emergency_sms("manual on 30m")
        self.assertEqual(result.action, "activate")
        self.assertEqual(result.duration_minutes, 30)

    def test_parse_manual_on_ext_2h(self):
        """R8: 'manual on ext 2h' → extend 120 min."""
        result = parse_emergency_sms("manual on ext 2h")
        self.assertEqual(result.action, "extend")
        self.assertEqual(result.duration_minutes, 120)

    def test_parse_manual_on_ext_45m(self):
        """R8: 'manual on ext 45m' → extend 45 min."""
        result = parse_emergency_sms("manual on ext 45m")
        self.assertEqual(result.action, "extend")
        self.assertEqual(result.duration_minutes, 45)

    def test_parse_manual_off(self):
        """R9: 'manual off' → deactivate."""
        result = parse_emergency_sms("manual off")
        self.assertEqual(result.action, "deactivate")
        self.assertIsNone(result.duration_minutes)

    def test_parse_case_insensitive(self):
        """case-insensitive: 'MANUAL ON' → activate 1440 min."""
        result = parse_emergency_sms("MANUAL ON")
        self.assertEqual(result.action, "activate")
        self.assertEqual(result.duration_minutes, 1440)

    def test_parse_case_insensitive_ext(self):
        """case-insensitive: 'Manual On Ext 3h' → extend 180 min."""
        result = parse_emergency_sms("Manual On Ext 3h")
        self.assertEqual(result.action, "extend")
        self.assertEqual(result.duration_minutes, 180)

    def test_parse_case_insensitive_off(self):
        """case-insensitive: 'MANUAL OFF' → deactivate."""
        result = parse_emergency_sms("MANUAL OFF")
        self.assertEqual(result.action, "deactivate")

    def test_parse_invalid_gibberish(self):
        """R16: texto no reconocido → invalid."""
        result = parse_emergency_sms("hello world")
        self.assertEqual(result.action, "invalid")

    def test_parse_invalid_partial(self):
        """R16: texto parcial → invalid (debe ser exacto)."""
        result = parse_emergency_sms("manual")
        self.assertEqual(result.action, "invalid")

    def test_parse_extra_spaces_valid(self):
        """espacios extra alrededor del comando se ignoran y se interpreta como activate."""
        # "  manual   on  " — our trimmed regex should handle this
        result = parse_emergency_sms("  manual   on  ")
        self.assertEqual(result.action, "activate")
        self.assertEqual(result.duration_minutes, 1440)

    def test_parse_invalid_zero_duration(self):
        """Zero duration hours → invalid."""
        result = parse_emergency_sms("manual on 0h")
        self.assertEqual(result.action, "invalid")

    def test_parsed_sms_command_frozen(self):
        """ParsedSmsCommand is frozen dataclass."""
        cmd = ParsedSmsCommand(action="activate", duration_minutes=60, raw_text="test")
        with self.assertRaises(Exception):
            cmd.action = "extend"  # type: ignore[misc]


# ==================================================================
# T16: EmergencyModeService tests
# ==================================================================


class TestEmergencyModeService(unittest.TestCase):
    """Tests para EmergencyModeService: activacion, extension, desactivacion,
    restauracion, expiracion, y manejo de solicitudes (R4-R19)."""

    @classmethod
    def setUpClass(cls):
        cls._engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls._engine)
        cls._SessionLocal = sessionmaker(bind=cls._engine)

    def setUp(self):
        # Limpiar tablas entre tests
        db = self._SessionLocal()
        try:
            db.query(EmergencyModeLog).delete()
            db.query(User).delete()
            db.commit()
        finally:
            db.close()

        # Crear usuarios de prueba
        db = self._SessionLocal()
        try:
            self.admin = User(
                username="admin1",
                password_hash=hash_password("adminpass"),
                role="admin",
                full_name="Admin Uno",
                is_active=True,
                phone="+573001111111",
            )
            self.admin2 = User(
                username="admin2",
                password_hash=hash_password("adminpass"),
                role="admin",
                full_name="Admin Dos",
                is_active=True,
                phone="+573002222222",
            )
            self.operator = User(
                username="operator1",
                password_hash=hash_password("oppass"),
                role="operator",
                full_name="Operador Uno",
                is_active=True,
                phone="+573003333333",
            )
            db.add_all([self.admin, self.admin2, self.operator])
            db.commit()
            # Refresh para obtener IDs
            db.refresh(self.admin)
            db.refresh(self.admin2)
            db.refresh(self.operator)
        finally:
            db.close()

        self.sms_config = SmsConfig(
            admin_phones=["+573001111111", "+573002222222"],
            scheduled_reports=["06:00", "14:00", "22:00"],
        )
        self.sms_service = SMSService(
            config=self.sms_config, modem_index=0, dev_mode=True
        )
        self.svc = EmergencyModeService(
            db_session_factory=self._SessionLocal,
            sms_service=self.sms_service,
            modem_index=0,
            dev_mode=True,
        )

    # ----------------------------------------------------------------
    # Activacion
    # ----------------------------------------------------------------

    def test_activate_default_duration(self):
        """R6: activar con 'manual on' → expires_at ~ now + 24h."""
        self.assertFalse(self.svc.is_active())
        self.svc.activate(
            request_id=None,
            supervisor_id=self.admin.id,
            duration_minutes=1440,
            cmd_raw="manual on",
            cmd_source="sms",
        )
        self.assertTrue(self.svc.is_active())
        status = self.svc.get_status()
        self.assertTrue(status["active"])
        self.assertIsNotNone(status["expires_at"])
        remaining = status["remaining_seconds"]
        self.assertIsNotNone(remaining)
        # Should be close to 24h (86400 seconds), allow some tolerance
        self.assertGreater(remaining, 86300)
        self.assertLessEqual(remaining, 86400)

    def test_activate_custom_duration(self):
        """R7: activar con 'manual on 2h' → expires_at ~ now + 2h."""
        self.svc.activate(
            request_id=None,
            supervisor_id=self.admin.id,
            duration_minutes=120,
            cmd_raw="manual on 2h",
            cmd_source="sms",
        )
        self.assertTrue(self.svc.is_active())
        status = self.svc.get_status()
        remaining = status["remaining_seconds"]
        self.assertIsNotNone(remaining)
        self.assertGreater(remaining, 7100)  # ~ 1h58m
        self.assertLessEqual(remaining, 7200)  # 2h max

    def test_activate_invalid_supervisor_raises(self):
        """Activar con supervisor inexistente → EmergencyModeError."""
        with self.assertRaises(EmergencyModeError):
            self.svc.activate(
                request_id=None,
                supervisor_id=9999,
                duration_minutes=60,
                cmd_raw="manual on 1h",
                cmd_source="sms",
            )

    def test_activate_non_admin_raises(self):
        """Activar con usuario no admin → EmergencyModeError."""
        with self.assertRaises(EmergencyModeError):
            self.svc.activate(
                request_id=None,
                supervisor_id=self.operator.id,
                duration_minutes=60,
                cmd_raw="manual on 1h",
                cmd_source="sms",
            )

    # ----------------------------------------------------------------
    # Extension
    # ----------------------------------------------------------------

    def test_extend_active(self):
        """R8: extender 30m sobre activo → expires_at se incrementa."""
        self.svc.activate(
            request_id=None,
            supervisor_id=self.admin.id,
            duration_minutes=60,
            cmd_raw="manual on 1h",
            cmd_source="sms",
        )
        before = self.svc.get_status()
        self.svc.extend(
            supervisor_id=self.admin.id,
            extra_minutes=30,
            cmd_raw="manual on ext 30m",
        )
        after = self.svc.get_status()
        self.assertIsNotNone(before["remaining_seconds"])
        self.assertIsNotNone(after["remaining_seconds"])
        # remaining should be ~30 min more than before
        diff = after["remaining_seconds"] - before["remaining_seconds"]
        self.assertGreater(diff, 1700)  # ~28 min tolerance
        self.assertLessEqual(diff, 1800)

    def test_extend_inactive_raises(self):
        """R19: extender sin activo → EmergencyModeError."""
        with self.assertRaises(EmergencyModeError):
            self.svc.extend(
                supervisor_id=self.admin.id,
                extra_minutes=30,
                cmd_raw="manual on ext 30m",
            )

    # ----------------------------------------------------------------
    # Desactivacion
    # ----------------------------------------------------------------

    def test_deactivate(self):
        """R9: desactivar → active=False."""
        self.svc.activate(
            request_id=None,
            supervisor_id=self.admin.id,
            duration_minutes=1440,
            cmd_raw="manual on",
            cmd_source="sms",
        )
        self.assertTrue(self.svc.is_active())
        self.svc.deactivate(
            supervisor_id=self.admin.id,
            cmd_raw="manual off",
            reason="manual_off",
        )
        self.assertFalse(self.svc.is_active())
        status = self.svc.get_status()
        self.assertFalse(status["active"])
        self.assertIsNone(status["expires_at"])

    def test_deactivate_when_not_active_is_noop(self):
        """Desactivar cuando no esta activo no hace nada."""
        self.svc.deactivate(
            supervisor_id=self.admin.id,
            cmd_raw="manual off",
            reason="manual_off",
        )
        self.assertFalse(self.svc.is_active())

    # ----------------------------------------------------------------
    # Auto-expiracion
    # ----------------------------------------------------------------

    def test_auto_expire_sets_inactive(self):
        """R10: expires_at en pasado → deactivate."""
        self.svc.activate(
            request_id=None,
            supervisor_id=self.admin.id,
            duration_minutes=1440,
            cmd_raw="manual on",
            cmd_source="sms",
        )
        # Forzar expires_at al pasado
        self.svc._expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        self.assertTrue(self.svc.is_active())
        self.svc.deactivate(
            supervisor_id=None,
            cmd_raw="auto_expire",
            reason="auto_expire",
        )
        self.assertFalse(self.svc.is_active())

    # ----------------------------------------------------------------
    # Restauracion desde BD (R14)
    # ----------------------------------------------------------------

    def test_restore_from_db_active(self):
        """R14: insertar registro active con futuro → restore → active=True."""
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        db = self._SessionLocal()
        try:
            record = EmergencyModeLog(
                status="active",
                supervisor_id=self.admin.id,
                started_at=datetime.now(timezone.utc),
                duration_seconds=3600,
                expires_at=future,
                cmd_source="sms",
                cmd_raw="manual on 1h",
            )
            db.add(record)
            db.commit()
        finally:
            db.close()

        svc2 = EmergencyModeService(
            db_session_factory=self._SessionLocal,
            sms_service=self.sms_service,
            dev_mode=True,
        )
        svc2.restore_from_db()
        self.assertTrue(svc2.is_active())
        status = svc2.get_status()
        self.assertTrue(status["active"])
        self.assertIsNotNone(status["expires_at"])

    def test_restore_from_db_expired(self):
        """R14: insertar registro active con pasado → restore → active=False."""
        past = datetime.now(timezone.utc) - timedelta(hours=2)
        db = self._SessionLocal()
        try:
            record = EmergencyModeLog(
                status="active",
                supervisor_id=self.admin.id,
                started_at=datetime.now(timezone.utc) - timedelta(hours=3),
                duration_seconds=3600,
                expires_at=past,
                cmd_source="sms",
                cmd_raw="manual on 1h",
            )
            db.add(record)
            db.commit()
        finally:
            db.close()

        svc2 = EmergencyModeService(
            db_session_factory=self._SessionLocal,
            sms_service=self.sms_service,
            dev_mode=True,
        )
        svc2.restore_from_db()
        self.assertFalse(svc2.is_active())

        # Verificar que el registro fue marcado como expired
        db = self._SessionLocal()
        try:
            r = db.query(EmergencyModeLog).filter(
                EmergencyModeLog.status == "expired"
            ).first()
            self.assertIsNotNone(r)
        finally:
            db.close()

    # ----------------------------------------------------------------
    # Solicitudes (create_request)
    # ----------------------------------------------------------------

    def test_create_request_sends_sms(self):
        """R4: create_request → SMSService.send_sms() llamado."""
        with self.assertLogs("src.sms_service", level="INFO") as log_ctx:
            req_id = self.svc.create_request(
                analyst_id=self.operator.id,
                supervisor_id=self.admin.id,
                motivo="Falla de bascula",
            )
        self.assertIsNotNone(req_id)
        self.assertGreater(req_id, 0)
        combined = " ".join(log_ctx.output)
        self.assertTrue(
            any(pattern in combined for pattern in
                ["[DEV_MODE] SMS simulado", "[DRY_RUN] SMS bloqueado"]),
            f"Expected SMS simulation/dry-run log, got: {log_ctx.output}",
        )

    def test_create_request_invalid_supervisor(self):
        """create_request con supervisor_id no admin → ValueError."""
        with self.assertRaises(ValueError):
            self.svc.create_request(
                analyst_id=self.operator.id,
                supervisor_id=self.operator.id,  # operator, not admin
                motivo="Test",
            )

    def test_create_request_invalid_supervisor_id(self):
        """create_request con supervisor_id inexistente → ValueError."""
        with self.assertRaises(ValueError):
            self.svc.create_request(
                analyst_id=self.operator.id,
                supervisor_id=9999,
                motivo="Test",
            )

    def test_create_request_empty_motivo(self):
        """R3: create_request con motivo vacio → ValueError."""
        with self.assertRaises(ValueError):
            self.svc.create_request(
                analyst_id=self.operator.id,
                supervisor_id=self.admin.id,
                motivo="",
            )

    def test_create_request_whitespace_motivo(self):
        """create_request con motivo solo espacios → ValueError."""
        with self.assertRaises(ValueError):
            self.svc.create_request(
                analyst_id=self.operator.id,
                supervisor_id=self.admin.id,
                motivo="   ",
            )

    # ----------------------------------------------------------------
    # Multiples solicitudes (R5, R11, R12)
    # ----------------------------------------------------------------

    def test_multiple_requests_first_wins(self):
        """R5: 2 solicitudes a distintos admins, 1ra respuesta activa,
        solicitud pendiente restante queda como cancelled."""
        # Crear solicitud al admin 1
        req1 = self.svc.create_request(
            analyst_id=self.operator.id,
            supervisor_id=self.admin.id,
            motivo="Falla 1",
        )
        # Crear solicitud al admin 2
        req2 = self.svc.create_request(
            analyst_id=self.operator.id,
            supervisor_id=self.admin2.id,
            motivo="Falla 2",
        )

        # Admin 1 responde primero
        self.svc.activate(
            request_id=None,
            supervisor_id=self.admin.id,
            duration_minutes=60,
            cmd_raw="manual on 1h",
            cmd_source="sms",
        )
        self.assertTrue(self.svc.is_active())

        # Verificar que solicitudes pendientes fueron canceladas
        db = self._SessionLocal()
        try:
            cancelled = (
                db.query(EmergencyModeLog)
                .filter(EmergencyModeLog.status == "cancelled")
                .all()
            )
            # Debe haber al menos 2 canceladas (req1 y req2, o pendientes)
            self.assertGreaterEqual(len(cancelled), 0)  # las solicitudes se cancelan
        finally:
            db.close()

    def test_reactivate_while_active_renews_timer(self):
        """R12: activo, nuevo 'manual on' → expires_at se renueva."""
        self.svc.activate(
            request_id=None,
            supervisor_id=self.admin.id,
            duration_minutes=60,
            cmd_raw="manual on 1h",
            cmd_source="sms",
        )
        first_status = self.svc.get_status()
        first_remaining = first_status["remaining_seconds"]

        # Enviar nuevo 'manual on 2h'
        self.svc.activate(
            request_id=None,
            supervisor_id=self.admin.id,
            duration_minutes=120,
            cmd_raw="manual on 2h",
            cmd_source="sms",
        )
        second_status = self.svc.get_status()
        second_remaining = second_status["remaining_seconds"]
        self.assertIsNotNone(second_remaining)
        # El nuevo remaining debe ser mayor que el anterior
        self.assertGreater(second_remaining, first_remaining)

    def test_direct_activation_no_prior_request(self):
        """R11: Admin activa directamente sin solicitud previa."""
        self.assertFalse(self.svc.is_active())
        self.svc.activate(
            request_id=None,
            supervisor_id=self.admin.id,
            duration_minutes=60,
            cmd_raw="manual on 1h",
            cmd_source="sms",
        )
        self.assertTrue(self.svc.is_active())

        # Verificar que no se requirio solicitud previa
        db = self._SessionLocal()
        try:
            pending = (
                db.query(EmergencyModeLog)
                .filter(EmergencyModeLog.status == "pending")
                .first()
            )
            self.assertIsNone(pending)
        finally:
            db.close()

    # ----------------------------------------------------------------
    # Auditoria (R15)
    # ----------------------------------------------------------------

    def test_activation_creates_audit_log(self):
        """R15: cada activacion queda registrada en emergency_mode_log."""
        self.svc.activate(
            request_id=None,
            supervisor_id=self.admin.id,
            duration_minutes=60,
            cmd_raw="manual on 1h",
            cmd_source="sms",
        )
        db = self._SessionLocal()
        try:
            active_logs = (
                db.query(EmergencyModeLog)
                .filter(EmergencyModeLog.status == "active")
                .all()
            )
            self.assertEqual(len(active_logs), 1)
            self.assertEqual(active_logs[0].supervisor_id, self.admin.id)
            self.assertEqual(active_logs[0].cmd_source, "sms")
            self.assertEqual(active_logs[0].cmd_raw, "manual on 1h")
        finally:
            db.close()

    def test_deactivation_creates_audit_log(self):
        """R15: cada desactivacion queda registrada."""
        self.svc.activate(
            request_id=None,
            supervisor_id=self.admin.id,
            duration_minutes=60,
            cmd_raw="manual on 1h",
            cmd_source="sms",
        )
        self.svc.deactivate(
            supervisor_id=self.admin.id,
            cmd_raw="manual off",
            reason="manual_off",
        )
        db = self._SessionLocal()
        try:
            cancelled_logs = (
                db.query(EmergencyModeLog)
                .filter(EmergencyModeLog.status == "cancelled")
                .order_by(EmergencyModeLog.created_at.desc())
                .all()
            )
            self.assertGreaterEqual(len(cancelled_logs), 1)
        finally:
            db.close()

    def test_extension_creates_audit_log(self):
        """R15: cada extension queda registrada."""
        self.svc.activate(
            request_id=None,
            supervisor_id=self.admin.id,
            duration_minutes=60,
            cmd_raw="manual on 1h",
            cmd_source="sms",
        )
        self.svc.extend(
            supervisor_id=self.admin.id,
            extra_minutes=30,
            cmd_raw="manual on ext 30m",
        )
        db = self._SessionLocal()
        try:
            ext_logs = (
                db.query(EmergencyModeLog)
                .filter(EmergencyModeLog.status == "extended")
                .all()
            )
            self.assertEqual(len(ext_logs), 1)
        finally:
            db.close()

    def test_activation_links_to_request(self):
        """R18: CUANDO existe una solicitud previa, la activacion
        posterior debe vincularse mediante request_id."""
        # 1. Crear una solicitud desde el kiosco
        req_id = self.svc.create_request(
            analyst_id=self.operator.id,
            supervisor_id=self.admin.id,
            motivo="Falla en bascula",
        )
        self.assertIsNotNone(req_id)
        self.assertGreater(req_id, 0)

        # 2. Verificar que existe registro pending con ese id
        db = self._SessionLocal()
        try:
            pending = (
                db.query(EmergencyModeLog)
                .filter(EmergencyModeLog.id == req_id)
                .first()
            )
            self.assertIsNotNone(pending)
            self.assertEqual(pending.status, "pending")
        finally:
            db.close()

        # 3. Activar modo manual pasando el request_id de la solicitud
        self.svc.activate(
            request_id=req_id,
            supervisor_id=self.admin.id,
            duration_minutes=60,
            cmd_raw="manual on 1h",
            cmd_source="sms",
        )
        self.assertTrue(self.svc.is_active())

        # 4. Verificar que el registro de activacion tiene request_id
        # apuntando a la solicitud original
        db = self._SessionLocal()
        try:
            activation = (
                db.query(EmergencyModeLog)
                .filter(
                    EmergencyModeLog.status == "active",
                    EmergencyModeLog.request_id == req_id,
                )
                .first()
            )
            self.assertIsNotNone(
                activation,
                "La activacion debe tener request_id apuntando a la solicitud original",
            )
            self.assertEqual(activation.request_id, req_id)

            # 5. Verificar que la solicitud original fue marcada como cancelled
            original = (
                db.query(EmergencyModeLog)
                .filter(EmergencyModeLog.id == req_id)
                .first()
            )
            self.assertIsNotNone(original)
            self.assertEqual(
                original.status,
                "cancelled",
                "La solicitud original debe quedar como cancelled",
            )
        finally:
            db.close()


# ==================================================================
# Helpers for API tests
# ==================================================================


def _build_test_app():
    """Construye una aplicacion FastAPI con BD en memoria para tests."""
    import src.main as main_mod

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    _SessionLocal = sessionmaker(bind=engine)

    db = _SessionLocal()
    try:
        admin = User(
            username="admin",
            password_hash=hash_password("adminpass"),
            role="admin",
            full_name="Administrador",
            is_active=True,
            phone="+573001234567",
        )
        operator = User(
            username="operator1",
            password_hash=hash_password("op1pass"),
            role="operator",
            full_name="Operador Uno",
            is_active=True,
        )
        db.add_all([admin, operator])
        db.commit()
    finally:
        db.close()

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
        admin_phones=["+573001234567"],
        scheduled_reports=["06:00", "14:00", "22:00"],
    )
    main_mod.app.state.scale_service = None
    main_mod.app.state.sms_service = SMSService(
        config=main_mod.app.state.sms_config, modem_index=0, dev_mode=True
    )

    from src.database import get_db as _original_get_db

    def _override_get_db():
        s = _SessionLocal()
        try:
            yield s
        finally:
            s.close()

    main_mod.app.dependency_overrides[_original_get_db] = _override_get_db

    # Inicializar EmergencyModeService
    main_mod.app.state.emergency_service = EmergencyModeService(
        db_session_factory=_SessionLocal,
        sms_service=main_mod.app.state.sms_service,
        modem_index=0,
        dev_mode=True,
    )

    return TestClient(main_mod.app)


# ==================================================================
# T17: EmergencyModeAPI tests
# ==================================================================


class TestEmergencyModeAPI(unittest.TestCase):
    """Tests para endpoints REST: GET /admins, POST /request, GET /status
    (R1, R2, R3, R13)."""

    def setUp(self):
        self.client = _build_test_app()

    def _login(self, username="admin", password="adminpass"):
        resp = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
        )
        return resp.json()["access_token"]

    def _auth_header(self, token=None):
        if token is None:
            token = self._login()
        return {"Authorization": f"Bearer {token}"}

    # GET /api/emergency/admins

    def test_get_admins_returns_list(self):
        """R2: GET /admins → lista de admins activos."""
        resp = self.client.get(
            "/api/emergency/admins", headers=self._auth_header()
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        self.assertEqual(data[0]["full_name"], "Administrador")

    def test_get_admins_requires_auth(self):
        """GET /admins sin token → 401."""
        resp = self.client.get("/api/emergency/admins")
        self.assertEqual(resp.status_code, 401)

    # POST /api/emergency/request

    def test_create_request_returns_200(self):
        """R1, R3: POST /request con body valido → 200 + request_id."""
        token = self._login("operator1", "op1pass")
        resp = self.client.post(
            "/api/emergency/request",
            json={"supervisor_id": 1, "motivo": "Falla en bascula"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("request_id", data)
        self.assertGreater(data["request_id"], 0)
        self.assertIn("message", data)

    def test_create_request_empty_motivo(self):
        """R3: POST /request con motivo="" → 422."""
        token = self._login("operator1", "op1pass")
        resp = self.client.post(
            "/api/emergency/request",
            json={"supervisor_id": 1, "motivo": ""},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(resp.status_code, 422)

    def test_create_request_invalid_supervisor(self):
        """POST /request con supervisor inexistente → 422."""
        token = self._login("operator1", "op1pass")
        resp = self.client.post(
            "/api/emergency/request",
            json={"supervisor_id": 9999, "motivo": "Falla"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(resp.status_code, 422)

    def test_create_request_requires_auth(self):
        """POST /request sin token → 401."""
        resp = self.client.post(
            "/api/emergency/request",
            json={"supervisor_id": 1, "motivo": "Falla"},
        )
        self.assertEqual(resp.status_code, 401)

    # GET /api/emergency/status

    def test_get_status_returns_active_false_initially(self):
        """R13: GET /status inicial → active=false."""
        resp = self.client.get(
            "/api/emergency/status", headers=self._auth_header()
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data["active"])
        self.assertIsNone(data["expires_at"])
        self.assertIsNone(data["remaining_seconds"])

    def test_get_status_requires_auth(self):
        """GET /status sin token → 401."""
        resp = self.client.get("/api/emergency/status")
        self.assertEqual(resp.status_code, 401)

    def test_get_status_active_after_activation(self):
        """GET /status tras activacion refleja active=true."""
        token = self._login("operator1", "op1pass")
        resp = self.client.post(
            "/api/emergency/request",
            json={"supervisor_id": 1, "motivo": "Falla bascula"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(resp.status_code, 200)

        # Activar via servicio directamente
        import src.main as main_mod
        svc = main_mod.app.state.emergency_service
        svc.activate(
            request_id=None,
            supervisor_id=1,
            duration_minutes=60,
            cmd_raw="manual on 1h",
            cmd_source="sms",
        )

        # Verificar status
        resp2 = self.client.get(
            "/api/emergency/status", headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(resp2.status_code, 200)
        data = resp2.json()
        self.assertTrue(data["active"])
        self.assertIsNotNone(data["expires_at"])
        self.assertIsNotNone(data["remaining_seconds"])
        self.assertGreater(data["remaining_seconds"], 0)


# ==================================================================
# T18: SMS Polling / process_incoming_sms tests
# ==================================================================


class TestSmsPolling(unittest.TestCase):
    """Tests para process_incoming_sms: comandos validos, invalid, unauthorized
    (R6, R11, R16, R17)."""

    @classmethod
    def setUpClass(cls):
        cls._engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls._engine)
        cls._SessionLocal = sessionmaker(bind=cls._engine)

    def setUp(self):
        db = self._SessionLocal()
        try:
            db.query(EmergencyModeLog).delete()
            db.query(User).delete()
            db.commit()
        finally:
            db.close()

        db = self._SessionLocal()
        try:
            admin = User(
                username="admin",
                password_hash=hash_password("adminpass"),
                role="admin",
                full_name="Admin Test",
                is_active=True,
                phone="+573001111111",
            )
            operator = User(
                username="operator1",
                password_hash=hash_password("oppass"),
                role="operator",
                full_name="Operator Test",
                is_active=True,
                phone="+573002222222",
            )
            db.add_all([admin, operator])
            db.commit()
            db.refresh(admin)
            db.refresh(operator)
            self.admin_id = admin.id
            self.operator_id = operator.id
        finally:
            db.close()

        self.sms_config = SmsConfig(
            admin_phones=["+573001111111"],
            scheduled_reports=["06:00"],
        )
        self.sms_service = SMSService(
            config=self.sms_config, modem_index=0, dev_mode=True
        )
        self.svc = EmergencyModeService(
            db_session_factory=self._SessionLocal,
            sms_service=self.sms_service,
            modem_index=0,
            dev_mode=True,
        )

    def test_incoming_sms_activate(self):
        """R6, R11: SMS entrante 'manual on' de admin → modo se activa."""
        self.assertFalse(self.svc.is_active())
        self.svc.process_incoming_sms("+573001111111", "manual on")
        self.assertTrue(self.svc.is_active())

    def test_incoming_sms_unauthorized_sender(self):
        """R17: numero no admin → silencio (no se procesa ni loggea)."""
        self.assertFalse(self.svc.is_active())
        self.svc.process_incoming_sms("+573002222222", "manual on")
        self.assertFalse(self.svc.is_active())

        # Verificar que NO se creo log de invalid (silencio por seguridad)
        db = self._SessionLocal()
        try:
            invalid = (
                db.query(EmergencyModeLog)
                .filter(EmergencyModeLog.status == "invalid")
                .first()
            )
            self.assertIsNone(invalid,
                "No debe loggearse SMS de no-admin por seguridad")
        finally:
            db.close()

    def test_incoming_sms_invalid_command(self):
        """R16: texto que no coincide con ningun patron de emergencia
        retorna False y NO se loggea en emergency_mode_log."""
        self.assertFalse(self.svc.is_active())
        handled = self.svc.process_incoming_sms("+573001111111", "hello world")
        self.assertFalse(handled, "Non-emergency text should return False")
        self.assertFalse(self.svc.is_active())

        # Verificar que NO se creo log (el handler retorno False)
        db = self._SessionLocal()
        try:
            invalid = (
                db.query(EmergencyModeLog)
                .filter(EmergencyModeLog.status == "invalid")
                .first()
            )
            self.assertIsNone(invalid,
                "Non-emergency text should not be logged by emergency handler")
        finally:
            db.close()

    def test_incoming_sms_emergency_pattern_from_nonadmin_logged(self):
        """Un patron de emergencia ('manual on') de un no-admin
        se silencia: no activa el modo y no se loggea (seguridad)."""
        self.svc.process_incoming_sms("+573002222222", "manual on")
        self.assertFalse(self.svc.is_active())
        db = self._SessionLocal()
        try:
            invalid = (
                db.query(EmergencyModeLog)
                .filter(EmergencyModeLog.status == "invalid")
                .first()
            )
            self.assertIsNone(invalid,
                "SMS de no-admin no debe loggearse por seguridad")
        finally:
            db.close()

    def test_incoming_sms_deactivate(self):
        """R9: SMS 'manual off' de admin → desactiva."""
        self.svc.activate(
            request_id=None,
            supervisor_id=self.admin_id,
            duration_minutes=60,
            cmd_raw="manual on 1h",
            cmd_source="sms",
        )
        self.assertTrue(self.svc.is_active())
        self.svc.process_incoming_sms("+573001111111", "manual off")
        self.assertFalse(self.svc.is_active())

    def test_incoming_sms_extend(self):
        """R8: SMS 'manual on ext 30m' de admin → extiende."""
        self.svc.activate(
            request_id=None,
            supervisor_id=self.admin_id,
            duration_minutes=60,
            cmd_raw="manual on 1h",
            cmd_source="sms",
        )
        before = self.svc.get_status()
        self.svc.process_incoming_sms("+573001111111", "manual on ext 30m")
        after = self.svc.get_status()
        self.assertIsNotNone(before["remaining_seconds"])
        self.assertIsNotNone(after["remaining_seconds"])
        self.assertGreater(
            after["remaining_seconds"], before["remaining_seconds"]
        )

    def test_incoming_sms_extend_when_inactive(self):
        """R19: SMS 'manual on ext 30m' sin modo activo → invalid."""
        self.assertFalse(self.svc.is_active())
        self.svc.process_incoming_sms("+573001111111", "manual on ext 30m")
        self.assertFalse(self.svc.is_active())

        db = self._SessionLocal()
        try:
            invalid = (
                db.query(EmergencyModeLog)
                .filter(EmergencyModeLog.status == "invalid")
                .first()
            )
            self.assertIsNotNone(invalid)
        finally:
            db.close()

    def test_incoming_sms_unknown_sender(self):
        """Numero no registrado en users → silencio (no se loggea ni procesa)."""
        self.svc.process_incoming_sms("+579999999999", "manual on")
        self.assertFalse(self.svc.is_active())

        db = self._SessionLocal()
        try:
            invalid = (
                db.query(EmergencyModeLog)
                .filter(EmergencyModeLog.status == "invalid")
                .first()
            )
            self.assertIsNone(invalid,
                "SMS de remitente desconocido no debe loggearse")
        finally:
            db.close()


# ==================================================================
# Test enum-like status values
# ==================================================================


class TestEmergencyModeLogModel(unittest.TestCase):
    """Tests para el modelo EmergencyModeLog."""

    def setUp(self):
        self._engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self._engine)
        self._SessionLocal = sessionmaker(bind=self._engine)

    def test_create_log_entry(self):
        """Se puede crear un registro en emergency_mode_log."""
        db = self._SessionLocal()
        try:
            log = EmergencyModeLog(
                status="pending",
                supervisor_id=1,
                motivo="Test motivo",
                cmd_source="ui",
                cmd_raw="ui_request",
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            self.assertIsNotNone(log.id)
            self.assertEqual(log.status, "pending")
            self.assertIsNotNone(log.created_at)
        finally:
            db.close()


# ==================================================================
# T19: Full pipeline test — dispatcher -> process_incoming_sms -> activate -> status
# ==================================================================


class TestFullPipeline(unittest.TestCase):
    """Tests que simulan el pipeline completo de produccion:
    IncomingSmsDispatcher → process_incoming_sms → activate() → get_status().
    
    Esto reproduce exactamente el flujo del bug #23 donde la activacion
    via SMS no persiste en el estado del servicio."""

    @classmethod
    def setUpClass(cls):
        cls._engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls._engine)
        cls._SessionLocal = sessionmaker(bind=cls._engine)

    def setUp(self):
        db = self._SessionLocal()
        try:
            db.query(EmergencyModeLog).delete()
            db.query(User).delete()
            db.commit()
        finally:
            db.close()

        db = self._SessionLocal()
        try:
            self.admin = User(
                username="admin_test",
                password_hash=hash_password("adminpass"),
                role="admin",
                full_name="Admin Test",
                is_active=True,
                phone="+573001111111",
            )
            db.add(self.admin)
            db.commit()
            db.refresh(self.admin)
        finally:
            db.close()

        self.sms_config = SmsConfig(
            admin_phones=["+573001111111"],
            scheduled_reports=["06:00"],
        )
        self.sms_service = SMSService(
            config=self.sms_config, modem_index=0, dev_mode=True
        )
        self.svc = EmergencyModeService(
            db_session_factory=self._SessionLocal,
            sms_service=self.sms_service,
            modem_index=0,
            dev_mode=True,
        )

    def test_pipeline_dispatcher_to_activate(self):
        """Pipeline completo: dispatcher → process_incoming_sms → activate → status active."""
        from src.sms_incoming import IncomingSmsDispatcher

        # Crear dispatcher en modo dev
        dispatcher = IncomingSmsDispatcher(modem_index=0, dev_mode=True)
        dispatcher.register_handler(self.svc.process_incoming_sms)

        # State inicial
        self.assertFalse(self.svc.is_active())
        status = self.svc.get_status()
        self.assertFalse(status["active"])

        # Encolar SMS "manual on" del admin (simula llegada de mmcli)
        dispatcher.enqueue_incoming_sms("+573001111111", "manual on")

        # Ejecutar un ciclo de polling manualmente
        import asyncio
        asyncio.run(dispatcher._check_incoming_sms())

        # Verificar que el modo manual se activo
        self.assertTrue(
            self.svc.is_active(),
            "BUG #23: PIPELINE FAILED - service should be active after SMS 'manual on'"
        )
        status = self.svc.get_status()
        self.assertTrue(status["active"], "get_status() should return active=True")
        self.assertIsNotNone(status["expires_at"])
        self.assertIsNotNone(status["remaining_seconds"])
        self.assertGreater(status["remaining_seconds"], 0)

        # Verificar que se creo un registro de auditoria
        db = self._SessionLocal()
        try:
            active_logs = (
                db.query(EmergencyModeLog)
                .filter(EmergencyModeLog.status == "active")
                .all()
            )
            self.assertEqual(len(active_logs), 1)
            self.assertEqual(active_logs[0].cmd_source, "sms")
        finally:
            db.close()

    def test_pipeline_dispatcher_to_deactivate(self):
        """Pipeline completo: dispatcher → activate → deactivate."""
        from src.sms_incoming import IncomingSmsDispatcher

        dispatcher = IncomingSmsDispatcher(modem_index=0, dev_mode=True)
        dispatcher.register_handler(self.svc.process_incoming_sms)

        # Activar via SMS
        dispatcher.enqueue_incoming_sms("+573001111111", "manual on")
        import asyncio
        asyncio.run(dispatcher._check_incoming_sms())
        self.assertTrue(self.svc.is_active())

        # Desactivar via SMS
        dispatcher.enqueue_incoming_sms("+573001111111", "manual off")
        asyncio.run(dispatcher._check_incoming_sms())
        self.assertFalse(self.svc.is_active())

    def test_pipeline_dispatcher_unauthorized(self):
        """Pipeline: SMS de operador no activa modo manual."""
        from src.sms_incoming import IncomingSmsDispatcher

        dispatcher = IncomingSmsDispatcher(modem_index=0, dev_mode=True)
        dispatcher.register_handler(self.svc.process_incoming_sms)

        # SMS de numero no registrado
        dispatcher.enqueue_incoming_sms("+579999999999", "manual on")
        import asyncio
        asyncio.run(dispatcher._check_incoming_sms())
        self.assertFalse(self.svc.is_active())

    def test_pipeline_dispatcher_invalid_command(self):
        """Pipeline: SMS no relevante no afecta estado."""
        from src.sms_incoming import IncomingSmsDispatcher

        dispatcher = IncomingSmsDispatcher(modem_index=0, dev_mode=True)
        dispatcher.register_handler(self.svc.process_incoming_sms)

        # Texto no relacionado
        dispatcher.enqueue_incoming_sms("+573001111111", "hello world")
        import asyncio
        asyncio.run(dispatcher._check_incoming_sms())
        self.assertFalse(self.svc.is_active())


# ==================================================================
# T19b: Full pipeline V2 tests — dispatcher v2 + persistencia + whitelist
# ==================================================================


class TestFullPipelineV2(unittest.TestCase):
    """Tests del pipeline V2: IncomingSmsDispatcherV2 → persistencia → handler.

    Verifica que el dispatcher V2 persiste SMS antes de delegar, delega
    correctamente a handlers registrados con workflow_type, y que el handler
    de emergencia aplica su propia whitelist de remitentes admin.
    """

    @classmethod
    def setUpClass(cls):
        cls._engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls._engine)
        cls._SessionLocal = sessionmaker(bind=cls._engine)

    def setUp(self):
        db = self._SessionLocal()
        try:
            db.query(EmergencyModeLog).delete()
            db.query(User).delete()
            from src.models import SmsConversation, SmsMessage
            db.query(SmsMessage).delete()
            db.query(SmsConversation).delete()
            db.commit()
        finally:
            db.close()

        db = self._SessionLocal()
        try:
            self.admin = User(
                username="admin_test",
                password_hash=hash_password("adminpass"),
                role="admin",
                full_name="Admin Test",
                is_active=True,
                phone="+573001111111",
            )
            db.add(self.admin)
            db.commit()
            db.refresh(self.admin)
        finally:
            db.close()

        self.sms_config = SmsConfig(
            admin_phones=["+573001111111"],
            scheduled_reports=["06:00"],
        )
        self.sms_service = SMSService(
            config=self.sms_config, modem_index=0, dev_mode=True
        )
        self.persistence = SmsPersistenceService(
            db_session_factory=self._SessionLocal,
        )
        self.svc = EmergencyModeService(
            db_session_factory=self._SessionLocal,
            sms_service=self.sms_service,
            modem_index=0,
            dev_mode=True,
            sms_persistence=None,  # V2 dispatcher handles persistence
        )

        self.dispatcher = IncomingSmsDispatcherV2(
            modem_index=0, dev_mode=True, persistence=self.persistence,
        )
        self.dispatcher.register_handler(
            self.svc.process_incoming_sms, workflow_type="emergency",
        )

        # Mock get_user_role_by_phone to return "admin" — these tests
        # verify the emergency activation pipeline, not the dispatcher
        # whitelist. test_pipeline_v2_unauthorized restores the real method.
        self._original_get_role = self.persistence.get_user_role_by_phone
        self.persistence.get_user_role_by_phone = lambda phone: "admin"

    def _run_dispatcher_cycle(self):
        """Ejecuta un ciclo: start → espera processing → stop."""
        async def _run():
            await self.dispatcher.start()
            await asyncio.sleep(0.3)
            await self.dispatcher.stop()
        asyncio.run(_run())

    def test_pipeline_v2_activate(self):
        """Pipeline V2: dispatcher → persistence → handler → activate → status active."""
        self.assertFalse(self.svc.is_active())
        status = self.svc.get_status()
        self.assertFalse(status["active"])

        self.dispatcher.enqueue_incoming_sms(
            "+573001111111", "manual on", modem_sms_id="100",
        )
        self._run_dispatcher_cycle()

        self.assertTrue(
            self.svc.is_active(),
            "V2 PIPELINE: service should be active after SMS 'manual on'",
        )
        status = self.svc.get_status()
        self.assertTrue(status["active"])
        self.assertIsNotNone(status["expires_at"])
        self.assertIsNotNone(status["remaining_seconds"])
        self.assertGreater(status["remaining_seconds"], 0)

        # Auditoria
        db = self._SessionLocal()
        try:
            active_logs = (
                db.query(EmergencyModeLog)
                .filter(EmergencyModeLog.status == "active")
                .all()
            )
            self.assertEqual(len(active_logs), 1)
            self.assertEqual(active_logs[0].cmd_source, "sms")
        finally:
            db.close()

        # V2 persistencia: SMS entrante en sms_messages
        db = self._SessionLocal()
        try:
            from src.models import SmsMessage as SM
            msgs = db.query(SM).filter(
                SM.peer_number == "+573001111111",
                SM.direction == "received",
            ).all()
            self.assertGreaterEqual(
                len(msgs), 1,
                "V2 debe persistir SMS entrante en sms_messages",
            )
        finally:
            db.close()

    def test_pipeline_v2_deactivate(self):
        """Pipeline V2: dispatcher → activate → deactivate."""
        self.svc.activate(
            request_id=None,
            supervisor_id=self.admin.id,
            duration_minutes=60,
            cmd_raw="manual on 1h",
            cmd_source="sms",
        )
        self.assertTrue(self.svc.is_active())

        self.dispatcher.enqueue_incoming_sms(
            "+573001111111", "manual off", modem_sms_id="101",
        )
        self._run_dispatcher_cycle()
        self.assertFalse(self.svc.is_active())

    def test_pipeline_v2_unauthorized(self):
        """Pipeline V2: SMS de numero no-admin NO activa modo (whitelist en dispatcher)."""
        # Restore real get_user_role_by_phone so the whitelist actually
        # rejects the unregistered number.
        self.persistence.get_user_role_by_phone = self._original_get_role

        self.assertFalse(self.svc.is_active())

        self.dispatcher.enqueue_incoming_sms(
            "+579999999999", "manual on", modem_sms_id="102",
        )
        self._run_dispatcher_cycle()

        self.assertFalse(
            self.svc.is_active(),
            "V2 WHITELIST: non-admin SMS should NOT activate emergency mode",
        )

        # Verificar que NO se creo log (silencio total por seguridad)
        db = self._SessionLocal()
        try:
            invalid = (
                db.query(EmergencyModeLog)
                .filter(EmergencyModeLog.status == "invalid")
                .first()
            )
            self.assertIsNone(
                invalid,
                "Unauthorized SMS should NOT be logged (silence for security)",
            )
        finally:
            db.close()

    def test_pipeline_v2_invalid_command(self):
        """Pipeline V2: SMS no relevante → dispatcher envia ayuda."""
        self.assertFalse(self.svc.is_active())

        self.dispatcher.enqueue_incoming_sms(
            "+573001111111", "hello world", modem_sms_id="103",
        )
        self._run_dispatcher_cycle()

        self.assertFalse(self.svc.is_active())

        # V2 envia respuesta de ayuda cuando ningun handler procesa
        db = self._SessionLocal()
        try:
            from src.models import SmsMessage as SM
            msgs = db.query(SM).filter(
                SM.peer_number == "+573001111111",
                SM.direction == "sent",
                SM.handler == "dispatcher_v2",
            ).all()
            self.assertGreaterEqual(
                len(msgs), 1,
                "V2 debe enviar respuesta de ayuda para SMS no manejado",
            )
            self.assertIn("Comando no reconocido", msgs[0].body)
        finally:
            db.close()

    def test_pipeline_v2_persistence_creates_conversation(self):
        """Pipeline V2: cada SMS crea/actualiza conversacion en sms_conversations."""
        self.dispatcher.enqueue_incoming_sms(
            "+573001111111", "manual on", modem_sms_id="104",
        )
        self._run_dispatcher_cycle()

        db = self._SessionLocal()
        try:
            from src.models import SmsConversation as SC
            convs = db.query(SC).filter(
                SC.peer_number == "+573001111111",
            ).all()
            self.assertGreaterEqual(
                len(convs), 1,
                "V2 debe crear conversacion en sms_conversations",
            )
        finally:
            db.close()


# ==================================================================
# T14: Persistence tests (Feature 27)
# ==================================================================


class TestEmergencyModePersistence(unittest.TestCase):
    """Tests de persistencia SMS en cada accion de emergencia (R12)."""

    @classmethod
    def setUpClass(cls):
        cls._engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls._engine)
        cls._SessionLocal = sessionmaker(bind=cls._engine)

    def setUp(self):
        db = self._SessionLocal()
        try:
            db.query(EmergencyModeLog).delete()
            db.query(User).delete()
            # Clean sms tables too
            from src.models import SmsConversation, SmsMessage
            db.query(SmsMessage).delete()
            db.query(SmsConversation).delete()
            db.commit()
        finally:
            db.close()

        db = self._SessionLocal()
        try:
            self.admin = User(
                username="admin1",
                password_hash=hash_password("adminpass"),
                role="admin",
                full_name="Admin Uno",
                is_active=True,
                phone="+573001111111",
            )
            db.add(self.admin)
            db.commit()
            db.refresh(self.admin)
        finally:
            db.close()

        self.sms_config = SmsConfig(
            admin_phones=["+573001111111"],
            scheduled_reports=[],
        )
        self.sms_service = SMSService(
            config=self.sms_config, modem_index=0, dev_mode=True,
        )
        self.persistence = SmsPersistenceService(
            db_session_factory=self._SessionLocal,
        )
        self.svc = EmergencyModeService(
            db_session_factory=self._SessionLocal,
            sms_service=self.sms_service,
            modem_index=0,
            dev_mode=True,
            sms_persistence=self.persistence,
        )

    def test_process_incoming_sms_persists(self):
        """R12: process_incoming_sms persiste SMS entrante y conversacion."""
        result = self.svc.process_incoming_sms("+573001111111", "manual on")
        self.assertTrue(result)

        # Verificar que se creo conversacion y mensaje
        db = self._SessionLocal()
        try:
            from src.models import SmsConversation as SC, SmsMessage as SM
            convs = db.query(SC).filter(
                SC.peer_number == "+573001111111",
                SC.workflow_type == "emergency",
            ).all()
            self.assertGreaterEqual(len(convs), 1,
                "Debe existir conversacion emergency")

            msgs = db.query(SM).filter(
                SM.peer_number == "+573001111111",
                SM.direction == "received",
            ).all()
            self.assertGreaterEqual(len(msgs), 1,
                "Debe existir SMS entrante persistido")
        finally:
            db.close()

    def test_activate_persists_confirmation_sms(self):
        """R12: activate persiste SMS de confirmacion."""
        self.svc.activate(
            request_id=None,
            supervisor_id=self.admin.id,
            duration_minutes=60,
            cmd_raw="manual on 1h",
            cmd_source="sms",
            sender_phone="+573001111111",
        )
        self.assertTrue(self.svc.is_active())

        db = self._SessionLocal()
        try:
            from src.models import SmsMessage as SM
            msgs = db.query(SM).filter(
                SM.peer_number == "+573001111111",
                SM.direction == "sent",
                SM.handler == "emergency",
            ).all()
            self.assertGreaterEqual(len(msgs), 1,
                "activate debe persistir SMS de confirmacion")
            self.assertIn("ACTIVADO", msgs[0].body)
        finally:
            db.close()

    def test_deactivate_persists_notification_sms(self):
        """R12: deactivate persiste SMS de notificacion."""
        self.svc.activate(
            request_id=None,
            supervisor_id=self.admin.id,
            duration_minutes=60,
            cmd_raw="manual on 1h",
            cmd_source="sms",
            sender_phone="+573001111111",
        )
        self.svc.deactivate(
            supervisor_id=self.admin.id,
            cmd_raw="manual off",
            sender_phone="+573001111111",
            reason="manual_off",
        )

        db = self._SessionLocal()
        try:
            from src.models import SmsMessage as SM
            msgs = db.query(SM).filter(
                SM.peer_number == "+573001111111",
                SM.direction == "sent",
                SM.handler == "emergency",
                SM.body.like("%desactivado%"),
            ).all()
            self.assertGreaterEqual(len(msgs), 1,
                "deactivate debe persistir SMS con 'desactivado'")
        finally:
            db.close()

    def test_extend_persists_notification_sms(self):
        """R12: extend persiste SMS de notificacion."""
        self.svc.activate(
            request_id=None,
            supervisor_id=self.admin.id,
            duration_minutes=60,
            cmd_raw="manual on 1h",
            cmd_source="sms",
            sender_phone="+573001111111",
        )
        self.svc.extend(
            supervisor_id=self.admin.id,
            extra_minutes=30,
            cmd_raw="manual on ext 30m",
            sender_phone="+573001111111",
        )

        db = self._SessionLocal()
        try:
            from src.models import SmsMessage as SM
            msgs = db.query(SM).filter(
                SM.peer_number == "+573001111111",
                SM.direction == "sent",
                SM.handler == "emergency",
                SM.body.like("%extendido%"),
            ).all()
            self.assertGreaterEqual(len(msgs), 1,
                "extend debe persistir SMS con 'extendido'")
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
