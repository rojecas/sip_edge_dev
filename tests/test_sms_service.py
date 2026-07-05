"""Tests for SMSService: dev mode, prod mode, error handling, empty phones,
scheduler behavior, and turn report generation."""

import asyncio
import logging
import os
import subprocess
import unittest
from datetime import datetime, timezone
from unittest import mock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.config import SmsConfig
from src.models import Base, Hacienda, Suerte, User, Weighing
from src.sms_persistence import SmsPersistenceService
from src.sms_service import SMSDeliveryError, SMSService


class TestSMSServiceDevMode(unittest.TestCase):
    """Verificar que en DEV_MODE=true se simula sin mmcli (R9)
    y que send_sms retorna True incluso en simulacion (R1)."""

    def setUp(self):
        self.config = SmsConfig(
            admin_phones=["+573001234567"],
            scheduled_reports=["06:00", "14:00", "22:00"],
        )
        self.svc = SMSService(config=self.config, modem_index=0, dev_mode=True)

    def test_send_sms_simulates_and_returns_true(self):
        """R1, R9: En dev mode, send_sms no ejecuta mmcli y retorna True."""
        with self.assertLogs("src.sms_service", level="INFO") as log_ctx:
            result = self.svc.send_sms("+573001234567", "Test message")
        self.assertTrue(result)
        self.assertTrue(
            any("[DEV_MODE] SMS simulado" in msg for msg in log_ctx.output),
            f"Expected DEV_MODE log, got: {log_ctx.output}",
        )

    def test_send_sms_empty_phone_returns_false(self):
        """R1: phone vacio retorna False."""
        result = self.svc.send_sms("", "message")
        self.assertFalse(result)

    def test_send_sms_empty_message_returns_false(self):
        """R1: message vacio retorna False."""
        result = self.svc.send_sms("+573001234567", "")
        self.assertFalse(result)

    def test_send_alert_to_admins_sends_to_all(self):
        """R1: send_alert_to_admins envia a todos los admin_phones."""
        with self.assertLogs("src.sms_service", level="INFO") as log_ctx:
            self.svc.send_alert_to_admins("Alerta!")
        self.assertTrue(
            any("[DEV_MODE] SMS simulado" in msg for msg in log_ctx.output),
            f"Expected DEV_MODE log, got: {log_ctx.output}",
        )


class TestSMSServiceProdMode(unittest.TestCase):
    """Verificar que en DEV_MODE=false se ejecuta mmcli con los
    argumentos correctos (R1)."""

    def setUp(self):
        self.config = SmsConfig(
            admin_phones=["+573001234567"],
            scheduled_reports=["06:00", "14:00", "22:00"],
        )
        self.svc = SMSService(config=self.config, modem_index=0, dev_mode=False)

    def test_send_sms_calls_mmcli_create_and_send(self):
        """R1: En prod, send_sms ejecuta mmcli --messaging-create-sms y --send."""
        create_stdout = (
            "Successfully created new SMS: "
            "/org/freedesktop/ModemManager1/SMS/3\n"
        )
        send_stdout = "successfully sent the SMS\n"

        def fake_run(args, **_kwargs):
            if "--messaging-create-sms" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=0, stdout=create_stdout, stderr=""
                )
            if "--send" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=0, stdout=send_stdout, stderr=""
                )
            return subprocess.CompletedProcess(
                args=args, returncode=1, stdout="", stderr="unknown subcommand"
            )

        with mock.patch("subprocess.run", side_effect=fake_run) as mock_run:
            with self.assertLogs("src.sms_service", level="INFO") as log_ctx:
                result = self.svc.send_sms("+573001234567", "Hola")
            self.assertTrue(result)
            self.assertTrue(
                any("SMS enviado correctamente" in msg for msg in log_ctx.output),
                f"Expected success log, got: {log_ctx.output}",
            )
            # Verifica que se llamo dos veces (crear + enviar)
            self.assertGreaterEqual(mock_run.call_count, 2)
            # Verifica que la primera llamada incluye --messaging-create-sms
            first_call_args = mock_run.call_args_list[0][0][0]
            self.assertIn("--messaging-create-sms", first_call_args)
            # Verifica que la segunda llamada incluye --send
            second_call_args = mock_run.call_args_list[1][0][0]
            self.assertIn("--send", second_call_args)


class TestSMSServiceErrorHandling(unittest.TestCase):
    """Verificar que si mmcli falla se loggea error y no se lanza
    excepcion fuera de SMSService (R8)."""

    def setUp(self):
        self.config = SmsConfig(
            admin_phones=["+573001234567"],
            scheduled_reports=["06:00"],
        )
        self.svc = SMSService(config=self.config, modem_index=0, dev_mode=False)

    def test_send_sms_returns_false_when_create_fails(self):
        """R8: Si mmcli falla al crear SMS, retorna False y loggea error."""

        def fake_run(args, **_kwargs):
            return subprocess.CompletedProcess(
                args=args, returncode=1, stdout="", stderr="No modem found"
            )

        with mock.patch("subprocess.run", side_effect=fake_run):
            with self.assertLogs("src.sms_service", level="ERROR") as log_ctx:
                result = self.svc.send_sms("+573001234567", "Test")
            self.assertFalse(result)
            self.assertTrue(
                any("mmcli fallo al crear SMS" in msg for msg in log_ctx.output),
                f"Expected error log, got: {log_ctx.output}",
            )

    def test_send_sms_returns_false_when_send_fails(self):
        """R8: Si mmcli falla al enviar SMS, retorna False y loggea error.
        B1: Verifica que se elimina el SMS huerfano del modem."""
        create_stdout = (
            "Successfully created new SMS: "
            "/org/freedesktop/ModemManager1/SMS/5\n"
        )

        call_log = []

        def fake_run(args, **_kwargs):
            call_log.append(args)
            if "--messaging-create-sms" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=0, stdout=create_stdout, stderr=""
                )
            if "--send" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=1, stdout="", stderr="Send failed"
                )
            if "--messaging-delete-sms" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=0, stdout="", stderr=""
                )
            return subprocess.CompletedProcess(
                args=args, returncode=1, stdout="", stderr="unknown subcommand"
            )

        with mock.patch("subprocess.run", side_effect=fake_run):
            with self.assertLogs("src.sms_service", level="ERROR") as log_ctx:
                result = self.svc.send_sms("+573001234567", "Test")
            self.assertFalse(result)
            self.assertTrue(
                any("mmcli fallo al enviar SMS" in msg for msg in log_ctx.output),
                f"Expected send error log, got: {log_ctx.output}",
            )
            # B1: Verificar que se llamo a --messaging-delete-sms con el indice correcto
            delete_calls = [
                a for a in call_log if any("--messaging-delete-sms" in str(arg) for arg in a)
            ]
            self.assertEqual(len(delete_calls), 1,
                "Debe llamar a mmcli --messaging-delete-sms exactamente una vez")
            self.assertTrue(
                any("=5" in str(arg) for arg in delete_calls[0]),
                "El indice del SMS a eliminar debe ser 5"
            )

    def test_send_sms_returns_false_when_no_sms_index_in_output(self):
        """R8: Si la salida de mmcli no contiene un indice SMS valido,
        retorna False y loggea error."""
        bad_output = "Some unexpected output without SMS path\n"

        with mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[], returncode=0, stdout=bad_output, stderr=""
            ),
        ):
            with self.assertLogs("src.sms_service", level="ERROR") as log_ctx:
                result = self.svc.send_sms("+573001234567", "Test")
            self.assertFalse(result)
            self.assertTrue(
                any("No se pudo extraer el indice del SMS" in msg for msg in log_ctx.output),
                f"Expected index error log, got: {log_ctx.output}",
            )

    def test_send_sms_handles_subprocess_timeout(self):
        """R8: Timeout en subprocess se maneja sin lanzar excepcion."""
        with mock.patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=[], timeout=30)):
            with self.assertLogs("src.sms_service", level="ERROR") as log_ctx:
                result = self.svc.send_sms("+573001234567", "Test")
            self.assertFalse(result)
            self.assertTrue(
                any("Timeout al crear SMS" in msg for msg in log_ctx.output),
                f"Expected timeout log, got: {log_ctx.output}",
            )

    def test_send_sms_handles_file_not_found(self):
        """R8: mmcli no encontrado se maneja sin lanzar excepcion."""
        with mock.patch("subprocess.run", side_effect=FileNotFoundError()):
            with self.assertLogs("src.sms_service", level="ERROR") as log_ctx:
                result = self.svc.send_sms("+573001234567", "Test")
            self.assertFalse(result)
            self.assertTrue(
                any("mmcli no encontrado" in msg for msg in log_ctx.output),
                f"Expected 'not found' log, got: {log_ctx.output}",
            )

    def test_send_to_admins_continues_after_individual_failure(self):
        """R8: Si falla un envio, se continua con los demas."""
        # Config con dos phones; el primero falla, el segundo funciona
        config = SmsConfig(
            admin_phones=["+57A", "+57B"],
            scheduled_reports=["06:00"],
        )
        svc = SMSService(config=config, modem_index=0, dev_mode=False)

        call_count = 0

        def fake_run(args, **_kwargs):
            nonlocal call_count
            call_count += 1
            # Primer intento falla, segundo funciona
            if call_count == 1:
                return subprocess.CompletedProcess(
                    args=args, returncode=1, stdout="", stderr="Fail"
                )
            create_stdout = (
                "Successfully created new SMS: "
                "/org/freedesktop/ModemManager1/SMS/7\n"
            )
            if "--send" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=0, stdout="sent", stderr=""
                )
            return subprocess.CompletedProcess(
                args=args, returncode=0, stdout=create_stdout, stderr=""
            )

        with mock.patch("subprocess.run", side_effect=fake_run):
            with self.assertLogs("src.sms_service", level="ERROR") as log_ctx:
                svc.send_alert_to_admins("Alerta")
            # Debe haber al menos un error y un exito
            self.assertTrue(
                any("mmcli fallo" in msg for msg in log_ctx.output),
                f"Expected error log for first phone, got: {log_ctx.output}",
            )


class TestSMSServiceEmptyPhones(unittest.TestCase):
    """Verificar que con admin_phones vacio no se intenta enviar (R7)."""

    def setUp(self):
        self.config = SmsConfig(
            admin_phones=[],
            scheduled_reports=["06:00"],
        )
        self.svc = SMSService(config=self.config, modem_index=0, dev_mode=False)

    def test_send_alert_does_nothing_with_empty_phones(self):
        """R7: Con admin_phones vacio, no se intenta enviar SMS."""
        with mock.patch("subprocess.run") as mock_run:
            self.svc.send_alert_to_admins("Alerta")
            mock_run.assert_not_called()

    def test_send_scheduled_report_does_nothing_with_empty_phones(self):
        """R7: Con admin_phones vacio, no se intenta enviar reporte."""
        with mock.patch("subprocess.run") as mock_run:
            self.svc.send_scheduled_report("Reporte de turno")
            mock_run.assert_not_called()


class TestSmsDeliveryError(unittest.TestCase):
    """Verificar que SMSDeliveryError es una excepcion usable."""

    def test_exception_can_be_raised_and_caught(self):
        with self.assertRaises(SMSDeliveryError):
            raise SMSDeliveryError("Test error")

    def test_exception_message_is_accessible(self):
        try:
            raise SMSDeliveryError("Modem offline")
        except SMSDeliveryError as exc:
            self.assertEqual(str(exc), "Modem offline")


class TestSchedulerBehavior(unittest.TestCase):
    """Tests para el planificador asincrono: R5 (reporte en horario),
    R12 (no duplicados)."""

    def setUp(self):
        self.config = SmsConfig(
            admin_phones=["+573001234567"],
            scheduled_reports=["06:00", "14:00", "22:00"],
        )
        self.svc = SMSService(config=self.config, modem_index=0, dev_mode=True)
        self.fixed_now = datetime(2026, 6, 15, 14, 0, 0, tzinfo=timezone.utc)

    def _patch_datetime(self):
        """Devuelve un context manager que parchea datetime.now en sms_service."""
        mock_dt = mock.MagicMock()
        mock_dt.now.return_value = self.fixed_now
        mock_dt.timezone = timezone
        return mock.patch("src.sms_service.datetime", mock_dt)

    def test_scheduler_sends_report_at_scheduled_time(self):
        """R5: Cuando la hora coincide con un horario configurado,
        se invoca _do_send_report con el time_slot correcto."""
        with mock.patch.object(self.svc, "_do_send_report") as mock_do:
            with self._patch_datetime():
                asyncio.run(self.svc._check_and_send_reports())
            mock_do.assert_called_once_with("14:00")

    def test_scheduler_does_not_send_when_no_match(self):
        """R5: Si la hora no coincide con ningun horario,
        no se invoca _do_send_report."""
        no_match_dt = datetime(2026, 6, 15, 15, 30, 0, tzinfo=timezone.utc)
        mock_dt = mock.MagicMock()
        mock_dt.now.return_value = no_match_dt
        mock_dt.timezone = timezone

        with mock.patch.object(self.svc, "_do_send_report") as mock_do:
            with mock.patch("src.sms_service.datetime", mock_dt):
                asyncio.run(self.svc._check_and_send_reports())
            mock_do.assert_not_called()

    def test_scheduler_does_not_duplicate_report_same_slot(self):
        """R12: Dos llamadas consecutivas en el mismo horario solo
        generan un reporte (mecanismo _sent_today)."""
        with mock.patch.object(self.svc, "_do_send_report") as mock_do:
            with self._patch_datetime():
                asyncio.run(self.svc._check_and_send_reports())
                asyncio.run(self.svc._check_and_send_reports())
            mock_do.assert_called_once_with("14:00")

    def test_scheduler_resets_sent_today_on_new_day(self):
        """R12: Al cambiar de dia, el set _sent_today se limpia y
        se vuelve a enviar el reporte del mismo horario."""
        day1 = datetime(2026, 6, 15, 14, 0, 0, tzinfo=timezone.utc)
        day2 = datetime(2026, 6, 16, 14, 0, 0, tzinfo=timezone.utc)

        with mock.patch.object(self.svc, "_do_send_report") as mock_do:
            # Dia 1: envia reporte de 14:00
            mock_dt1 = mock.MagicMock()
            mock_dt1.now.return_value = day1
            mock_dt1.timezone = timezone
            with mock.patch("src.sms_service.datetime", mock_dt1):
                asyncio.run(self.svc._check_and_send_reports())
            self.assertEqual(mock_do.call_count, 1)

            # Dia 2: mismo horario, nuevo dia => debe enviar otra vez
            mock_dt2 = mock.MagicMock()
            mock_dt2.now.return_value = day2
            mock_dt2.timezone = timezone
            with mock.patch("src.sms_service.datetime", mock_dt2):
                asyncio.run(self.svc._check_and_send_reports())
            # Total de llamadas: 2 (una por dia)
            self.assertEqual(mock_do.call_count, 2)
            mock_do.assert_called_with("14:00")


class TestGenerateTurnReport(unittest.TestCase):
    """R11: Contenido y formato del reporte de turno."""

    def setUp(self):
        self.config = SmsConfig(
            admin_phones=["+573001234567"],
            scheduled_reports=["06:00", "14:00", "22:00"],
        )
        self.svc = SMSService(config=self.config, modem_index=0, dev_mode=True)

        # Base de datos SQLite en memoria con datos de prueba
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        db = self.SessionLocal()
        try:
            user = User(
                username="testuser",
                password_hash="hash",
                role="operator",
                full_name="Test User",
            )
            hacienda = Hacienda(codigo="H001", nombre="Test Hacienda")
            db.add_all([user, hacienda])
            db.flush()

            suerte = Suerte(hacienda_id=hacienda.id, codigo_suerte="S01")
            db.add(suerte)
            db.flush()

            # Tres pesajes el 2026-06-15 entre 00:00 y 14:00
            base = datetime(2026, 6, 15, tzinfo=timezone.utc)
            w1 = Weighing(
                fecha=base.date(),
                hora=datetime.strptime("08:00", "%H:%M").time(),
                tractomula="TRUCK1",
                vagon="V1",
                numero_guia="G001",
                hacienda_id=hacienda.id,
                suerte_id=suerte.id,
                peso_muestra=100.0,
                peso_mineral=5.0,
                peso_vegetal_extrano=2.0,
                usuario_id=user.id,
                created_at=base.replace(hour=8, minute=0),
            )
            w2 = Weighing(
                fecha=base.date(),
                hora=datetime.strptime("10:00", "%H:%M").time(),
                tractomula="TRUCK2",
                vagon="V2",
                numero_guia="G002",
                hacienda_id=hacienda.id,
                suerte_id=suerte.id,
                peso_muestra=200.0,
                peso_mineral=10.0,
                peso_vegetal_extrano=3.0,
                usuario_id=user.id,
                created_at=base.replace(hour=10, minute=0),
            )
            w3 = Weighing(
                fecha=base.date(),
                hora=datetime.strptime("12:00", "%H:%M").time(),
                tractomula="TRUCK3",
                vagon="V3",
                numero_guia="G003",
                hacienda_id=hacienda.id,
                suerte_id=suerte.id,
                peso_muestra=300.0,
                peso_mineral=15.0,
                peso_vegetal_extrano=4.0,
                usuario_id=user.id,
                created_at=base.replace(hour=12, minute=0),
            )
            # Un pesaje FUERA del rango (despues de 14:00) -> no debe contar
            w_out = Weighing(
                fecha=base.date(),
                hora=datetime.strptime("15:00", "%H:%M").time(),
                tractomula="TRUCK4",
                vagon="V4",
                numero_guia="G004",
                hacienda_id=hacienda.id,
                suerte_id=suerte.id,
                peso_muestra=999.0,
                peso_mineral=99.0,
                peso_vegetal_extrano=9.0,
                usuario_id=user.id,
                created_at=base.replace(hour=15, minute=0),
            )
            db.add_all([w1, w2, w3, w_out])
            db.commit()
        finally:
            db.close()

        self.fixed_now = datetime(2026, 6, 15, 14, 0, 0, tzinfo=timezone.utc)

    def _patch_datetime_for_report(self):
        """Parchea datetime.now para que generate_turn_report use fecha fija."""
        mock_dt = mock.MagicMock()
        mock_dt.now.return_value = self.fixed_now
        mock_dt.timezone = timezone
        return mock.patch("src.sms_service.datetime", mock_dt)

    def test_generate_turn_report_includes_period_count_and_weight(self):
        """R11: El reporte incluye periodo del turno, conteo de pesajes
        y suma de pesos por tipo de material."""
        db = self.SessionLocal()
        try:
            with self._patch_datetime_for_report():
                report = self.svc.generate_turn_report(db, "00:00", "14:00")
        finally:
            db.close()

        self.assertIn("Reporte de turno [00:00 - 14:00]", report)
        self.assertIn("3 pesajes realizados", report)
        # Peso total: (100+5+2) + (200+10+3) + (300+15+4) = 639.00
        self.assertIn("639.00", report)
        self.assertIn("kg", report)

    def test_generate_turn_report_empty_range_returns_zero(self):
        """R11: Si no hay pesajes en el rango, el reporte indica 0 pesajes
        y peso 0.00 kg."""
        db = self.SessionLocal()
        try:
            with self._patch_datetime_for_report():
                report = self.svc.generate_turn_report(db, "20:00", "22:00")
        finally:
            db.close()

        self.assertIn("0 pesajes realizados", report)
        self.assertIn("0.00 kg", report)

    def test_generate_turn_report_period_is_configurable(self):
        """R11: El periodo del turno en el reporte refleja los argumentos
        turn_start y turn_end proporcionados."""
        db = self.SessionLocal()
        try:
            with self._patch_datetime_for_report():
                report = self.svc.generate_turn_report(db, "06:00", "14:00")
        finally:
            db.close()

        self.assertIn("[06:00 - 14:00]", report)
        # Solo pesajes de 08:00, 10:00, 12:00 deben contar (3 pesajes)
        self.assertIn("3 pesajes realizados", report)


# ==================================================================
# T12: Persistence integration tests (Feature 27)
# ==================================================================


class TestSMSServicePersistence(unittest.TestCase):
    """Verificar que send_sms persiste en sms_messages cuando SmsPersistenceService
    esta inyectado (R18)."""

    def setUp(self):
        self.config = SmsConfig(
            admin_phones=["+573001234567"],
            scheduled_reports=["06:00", "14:00", "22:00"],
        )
        self.svc = SMSService(config=self.config, modem_index=0, dev_mode=True)
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.persistence = SmsPersistenceService(db_session_factory=self.Session)
        self.svc.set_persistence_service(self.persistence)

    def test_send_sms_persists_in_dev_mode(self):
        """R18: En dev mode, send_sms persiste el mensaje como sent."""
        result = self.svc.send_sms("+573001234567", "Test persistence")
        self.assertTrue(result)

        db = self.Session()
        try:
            from src.models import SmsMessage as SM
            msgs = db.query(SM).filter(
                SM.peer_number == "+573001234567",
                SM.direction == "sent",
            ).all()
            self.assertEqual(len(msgs), 1)
            self.assertEqual(msgs[0].body, "Test persistence")
            self.assertEqual(msgs[0].status, "sent")
        finally:
            db.close()

    def test_send_sms_persists_before_mmcli(self):
        """R18: El mensaje se persiste ANTES de ejecutar mmcli.

        Verificamos que al llamar send_sms, el mensaje queda en BD aunque
        mmcli falle (simulado en dev mode ya persiste).
        """
        # En dev mode, siempre retorna True pero igual debe persistir
        result = self.svc.send_sms("+573001234567", "Before mmcli")
        self.assertTrue(result)

        # Verificar que el mensaje fue persistido
        db = self.Session()
        try:
            from src.models import SmsMessage as SM
            msgs = db.query(SM).filter(
                SM.peer_number == "+573001234567",
            ).all()
            self.assertGreaterEqual(len(msgs), 1,
                "El mensaje debe estar persistido en BD")
        finally:
            db.close()

    def test_send_sms_creates_conversation(self):
        """send_sms crea conversacion automaticamente."""
        self.svc.send_sms("+573009999999", "First message")

        db = self.Session()
        try:
            from src.models import SmsConversation as SC
            convs = db.query(SC).filter(
                SC.peer_number == "+573009999999",
            ).all()
            self.assertEqual(len(convs), 1)
            self.assertEqual(convs[0].workflow_type, "unknown")
            self.assertEqual(convs[0].status, "active")
        finally:
            db.close()

    def test_send_sms_sync_persists(self):
        """R18: send_sms_sync tambien persiste."""
        result = self.svc.send_sms_sync("+573001234567", "Sync persistence")
        self.assertTrue(result)

        db = self.Session()
        try:
            from src.models import SmsMessage as SM
            msgs = db.query(SM).filter(
                SM.peer_number == "+573001234567",
                SM.direction == "sent",
            ).all()
            self.assertEqual(len(msgs), 1)
            self.assertEqual(msgs[0].status, "sent")
        finally:
            db.close()

    def test_send_sms_without_persistence_still_works(self):
        """Sin persistencia inyectada, send_sms debe funcionar igual (legacy)."""
        svc_no_persist = SMSService(config=self.config, modem_index=0, dev_mode=True)
        result = svc_no_persist.send_sms("+573001234567", "No persist")
        self.assertTrue(result)
        # No hay excepcion, el envio simulado funciona


class TestSMSServiceDryRun(unittest.TestCase):
    """Verificar que SMS_DRY_RUN=true bloquea envios reales (B3)."""

    def setUp(self):
        self.config = SmsConfig(
            admin_phones=["+573001234567"],
            scheduled_reports=["06:00", "14:00", "22:00"],
        )
        self.svc = SMSService(config=self.config, modem_index=0, dev_mode=False)

    def test_send_sms_dry_run_logs_and_returns_true(self):
        """B3: Con SMS_DRY_RUN=true, send_sms loggea DRY_RUN y retorna True sin mmcli."""
        with mock.patch.dict(os.environ, {"SMS_DRY_RUN": "true"}):
            with mock.patch("subprocess.run") as mock_run:
                with self.assertLogs("src.sms_service", level="INFO") as log_ctx:
                    result = self.svc.send_sms("+573001234567", "Test dry run")
                self.assertTrue(result)
                mock_run.assert_not_called()
                self.assertTrue(
                    any("[DRY_RUN]" in msg for msg in log_ctx.output),
                    f"Expected DRY_RUN log, got: {log_ctx.output}",
                )

    def test_send_sms_dry_run_1_triggers(self):
        """B3: SMS_DRY_RUN=1 tambien activa el modo dry run."""
        with mock.patch.dict(os.environ, {"SMS_DRY_RUN": "1"}):
            with mock.patch("subprocess.run") as mock_run:
                result = self.svc.send_sms("+573001234567", "Test 1")
                self.assertTrue(result)
                mock_run.assert_not_called()

    def test_send_sms_dry_run_false_sends_normally(self):
        """B3: SMS_DRY_RUN=false no bloquea el envio."""
        create_stdout = (
            "Successfully created new SMS: "
            "/org/freedesktop/ModemManager1/SMS/3\n"
        )
        send_stdout = "successfully sent the SMS\n"
        call_log = []

        def fake_run(args, **_kwargs):
            call_log.append(args)
            if "--messaging-create-sms" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=0, stdout=create_stdout, stderr=""
                )
            if "--send" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=0, stdout=send_stdout, stderr=""
                )
            return subprocess.CompletedProcess(
                args=args, returncode=1, stdout="", stderr="unknown"
            )

        with mock.patch.dict(os.environ, {"SMS_DRY_RUN": "false"}):
            with mock.patch("subprocess.run", side_effect=fake_run):
                result = self.svc.send_sms("+573001234567", "Test real")
                self.assertTrue(result)
                # Debe haber llamado a mmcli al menos 2 veces (create + send)
                self.assertGreaterEqual(len(call_log), 2)

    def test_send_sms_sync_dry_run_logs_and_returns_true(self):
        """B3: send_sms_sync con SMS_DRY_RUN=true no ejecuta mmcli."""
        with mock.patch.dict(os.environ, {"SMS_DRY_RUN": "true"}):
            with mock.patch("subprocess.run") as mock_run:
                with self.assertLogs("src.sms_service", level="INFO") as log_ctx:
                    result = self.svc.send_sms_sync("+573001234567", "Sync dry run")
                self.assertTrue(result)
                mock_run.assert_not_called()
                self.assertTrue(
                    any("[DRY_RUN]" in msg for msg in log_ctx.output),
                    f"Expected DRY_RUN log, got: {log_ctx.output}",
                )

    def test_send_sms_dry_run_persists_message(self):
        """B3: En dry run, el mensaje se persiste en BD si hay persistencia."""
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        persistence = SmsPersistenceService(db_session_factory=Session)
        self.svc.set_persistence_service(persistence)

        with mock.patch.dict(os.environ, {"SMS_DRY_RUN": "true"}):
            result = self.svc.send_sms("+573001234567", "Dry run with persist")
            self.assertTrue(result)

        db = Session()
        try:
            from src.models import SmsMessage as SM
            msgs = db.query(SM).filter(
                SM.peer_number == "+573001234567",
                SM.direction == "sent",
            ).all()
            self.assertEqual(len(msgs), 1, "El dry run debe persistir el mensaje")
            self.assertEqual(msgs[0].body, "Dry run with persist")
        finally:
            db.close()


# ==================================================================
# Fix 2: modem_sms_id persistence in _send_via_mmcli_sync
# ==================================================================


class TestSMSServiceModemSmsId(unittest.TestCase):
    """Fix 2: Verificar que _send_via_mmcli_sync persiste modem_sms_id."""

    def setUp(self):
        self.config = SmsConfig(
            admin_phones=["+573001234567"],
            scheduled_reports=["06:00", "14:00", "22:00"],
        )
        self.svc = SMSService(config=self.config, modem_index=0, dev_mode=False)

        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.persistence = SmsPersistenceService(db_session_factory=self.Session)
        self.svc.set_persistence_service(self.persistence)

        # Crear conversacion y mensaje de prueba
        self.conv = self.persistence.create_conversation(
            peer_number="+573001234567", workflow_type="emergency",
        )
        self.msg = self.persistence.create_message(
            conversation_id=self.conv.id,
            direction="sent",
            peer_number="+573001234567",
            body="Test modem_sms_id",
            status="pending",
        )

    def test_modem_sms_id_saved_on_successful_send(self):
        """Fix 2: Con message_id, _send_via_mmcli_sync persiste modem_sms_id."""
        create_stdout = (
            "Successfully created new SMS: "
            "/org/freedesktop/ModemManager1/SMS/7\n"
        )
        send_stdout = "successfully sent the SMS\n"

        call_log = []

        def fake_run(args, **_kwargs):
            call_log.append(args)
            if "--messaging-create-sms" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=0, stdout=create_stdout, stderr="",
                )
            if "--send" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=0, stdout=send_stdout, stderr="",
                )
            return subprocess.CompletedProcess(
                args=args, returncode=1, stdout="", stderr="unknown",
            )

        with mock.patch("subprocess.run", side_effect=fake_run):
            result = self.svc._send_via_mmcli_sync(
                "+573001234567", "Test", message_id=self.msg.id,
            )

        self.assertTrue(result)

        # Verificar que modem_sms_id se persistio
        updated = self.persistence.get_message(self.msg.id)
        self.assertEqual(updated.modem_sms_id, 7)
        self.assertEqual(updated.status, "sent")

    def test_modem_sms_id_not_saved_without_message_id(self):
        """Fix 2: Sin message_id, no se persiste modem_sms_id (compatibilidad)."""
        create_stdout = (
            "Successfully created new SMS: "
            "/org/freedesktop/ModemManager1/SMS/5\n"
        )
        send_stdout = "successfully sent the SMS\n"

        def fake_run(args, **_kwargs):
            if "--messaging-create-sms" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=0, stdout=create_stdout, stderr="",
                )
            if "--send" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=0, stdout=send_stdout, stderr="",
                )
            return subprocess.CompletedProcess(
                args=args, returncode=1, stdout="", stderr="unknown",
            )

        with mock.patch("subprocess.run", side_effect=fake_run):
            result = self.svc._send_via_mmcli_sync(
                "+573001234567", "Test",
            )

        self.assertTrue(result)

        # El modem_sms_id NO se persistio (no se paso message_id)
        updated = self.persistence.get_message(self.msg.id)
        self.assertIsNone(updated.modem_sms_id)
        self.assertEqual(updated.status, "pending")  # No se actualizo

    def test_modem_sms_id_not_saved_on_send_failure(self):
        """Fix 2: Si el envio falla, NO se persiste modem_sms_id."""
        create_stdout = (
            "Successfully created new SMS: "
            "/org/freedesktop/ModemManager1/SMS/3\n"
        )

        def fake_run(args, **_kwargs):
            if "--messaging-create-sms" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=0, stdout=create_stdout, stderr="",
                )
            if "--send" in args:
                return subprocess.CompletedProcess(
                    args=args, returncode=1, stdout="", stderr="Send failed",
                )
            return subprocess.CompletedProcess(
                args=args, returncode=1, stdout="", stderr="unknown",
            )

        with mock.patch("subprocess.run", side_effect=fake_run):
            result = self.svc._send_via_mmcli_sync(
                "+573001234567", "Test", message_id=self.msg.id,
            )

        self.assertFalse(result)

        # modem_sms_id NO debe estar persistido
        updated = self.persistence.get_message(self.msg.id)
        self.assertIsNone(updated.modem_sms_id)
        self.assertEqual(updated.status, "pending")
