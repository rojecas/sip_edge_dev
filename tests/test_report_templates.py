"""Tests for ReportTemplateService: CRUD, metrica handlers, y generacion de reportes."""

import json
import unittest
from datetime import date, datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.models import Base, Hacienda, ReportTemplate, ReportTemplateUser, Suerte, User, Weighing
from src.report_templates import (
    METRIC_HANDLERS, ReportTemplateService, TemplateNotFoundError,
)


class TestReportTemplateCrud(unittest.TestCase):
    """Tests de CRUD para ReportTemplateService (R1, R2, R3)."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

        # Datos minimos para que la BD tenga contexto
        db = cls.SessionLocal()
        try:
            u = User(username="crud_op", password_hash="h", role="operator", full_name="CRUD Op")
            h = Hacienda(codigo="CRUD", nombre="Hacienda CRUD")
            db.add_all([u, h])
            db.flush()
            s = Suerte(hacienda_id=h.id, codigo_suerte="S-CRUD")
            db.add(s)
            db.commit()
        finally:
            db.close()

        cls.service = ReportTemplateService(db_session_factory=cls.SessionLocal)

    def setUp(self):
        """Limpiar plantillas antes de cada test."""
        db = self.SessionLocal()
        try:
            db.query(ReportTemplate).delete()
            db.commit()
        finally:
            db.close()

    def test_create_template(self):
        """R1: Crear plantilla con metricas y user_ids."""
        data = {
            "name": "Reporte Diario",
            "schedule": ["08:00", "18:00"],
            "user_ids": [],
            "metrics": ["count", "avg", "min_max"],
            "is_active": True,
        }
        template = self.service.create(data)
        self.assertIsNotNone(template.id)
        self.assertEqual(template.name, "Reporte Diario")
        self.assertTrue(template.is_active)

        schedule = json.loads(template.schedule)
        self.assertEqual(schedule, ["08:00", "18:00"])
        metrics = json.loads(template.metrics)
        self.assertEqual(metrics, ["count", "avg", "min_max"])

    def test_update_template(self):
        """R2: Modificar plantilla existente."""
        data = {
            "name": "Original",
            "schedule": ["08:00"],
            "user_ids": [],
            "metrics": ["count"],
        }
        template = self.service.create(data)

        updated = self.service.update(template.id, {
            "name": "Modificado",
            "metrics": ["count", "avg", "trend"],
            "is_active": False,
        })
        self.assertEqual(updated.name, "Modificado")
        self.assertFalse(updated.is_active)
        metrics = json.loads(updated.metrics)
        self.assertEqual(metrics, ["count", "avg", "trend"])
        schedule = json.loads(updated.schedule)
        self.assertEqual(schedule, ["08:00"])

    def test_update_nonexistent_template(self):
        """R2: Actualizar plantilla inexistente lanza TemplateNotFoundError."""
        with self.assertRaises(TemplateNotFoundError):
            self.service.update(9999, {"name": "X"})

    def test_delete_template(self):
        """R3: Eliminar plantilla existente."""
        data = {
            "name": "Para Eliminar",
            "schedule": ["12:00"],
            "user_ids": [],
            "metrics": ["count"],
        }
        template = self.service.create(data)
        tid = template.id

        all_templates = self.service.get_all()
        ids = [t["id"] for t in all_templates]
        self.assertIn(tid, ids)

        self.service.delete(tid)

        all_after = self.service.get_all()
        ids_after = [t["id"] for t in all_after]
        self.assertNotIn(tid, ids_after)

    def test_delete_nonexistent_template(self):
        """R3: Eliminar plantilla inexistente lanza TemplateNotFoundError."""
        with self.assertRaises(TemplateNotFoundError):
            self.service.delete(9999)

    def test_get_all_templates(self):
        """R1: Listar todas las plantillas con destinatarios resueltos."""
        self.service.create({
            "name": "T1", "schedule": ["08:00"],
            "user_ids": [], "metrics": ["count"],
        })
        self.service.create({
            "name": "T2", "schedule": ["18:00"],
            "user_ids": [], "metrics": ["avg"],
        })

        templates = self.service.get_all()
        self.assertEqual(len(templates), 2)
        names = sorted([t["name"] for t in templates])
        self.assertEqual(names, ["T1", "T2"])

    def test_get_active_by_schedule(self):
        """R1: Filtrar plantillas activas por horario."""
        self.service.create({
            "name": "Matutino", "schedule": ["08:00", "12:00"],
            "user_ids": [], "metrics": ["count"], "is_active": True,
        })
        self.service.create({
            "name": "Vespertino", "schedule": ["18:00"],
            "user_ids": [], "metrics": ["avg"], "is_active": True,
        })
        self.service.create({
            "name": "Inactivo", "schedule": ["08:00"],
            "user_ids": [], "metrics": ["count"], "is_active": False,
        })

        morning = self.service.get_active_by_schedule("08:00")
        self.assertEqual(len(morning), 1)
        self.assertEqual(morning[0].name, "Matutino")

        evening = self.service.get_active_by_schedule("18:00")
        self.assertEqual(len(evening), 1)
        self.assertEqual(evening[0].name, "Vespertino")

        noche = self.service.get_active_by_schedule("22:00")
        self.assertEqual(len(noche), 0)


class TestMetricHandlers(unittest.TestCase):
    """Tests para METRIC_HANDLERS (R4)."""

    def test_metric_handlers_count(self):
        """R4: El diccionario METRIC_HANDLERS tiene al menos 9 entradas."""
        self.assertGreaterEqual(len(METRIC_HANDLERS), 9)

    def test_metric_handlers_names(self):
        """R4: Los nombres esperados estan presentes."""
        expected = {
            "count", "avg", "min_max", "breakdown_by_hacienda",
            "breakdown_by_operator", "composition", "anomaly_count", "trend",
            "std",
        }
        for name in expected:
            self.assertIn(name, METRIC_HANDLERS, f"Falta el handler '{name}'")


class TestGenerateReport(unittest.TestCase):
    """Tests para generate_report (R5)."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

        db = cls.SessionLocal()
        try:
            u = User(username="gen_op", password_hash="h", role="operator", full_name="Gen Op")
            h = Hacienda(codigo="GEN", nombre="Hacienda Gen")
            db.add_all([u, h])
            db.flush()
            s = Suerte(hacienda_id=h.id, codigo_suerte="S-GEN")
            db.add(s)
            db.flush()

            today = date.today()
            for i in range(5):
                w = Weighing(
                    fecha=today,
                    hora=datetime.strptime(f"{8+i:02d}:00", "%H:%M").time(),
                    tractomula=f"GT{i}",
                    vagon=f"GV{i}",
                    numero_guia=f"GG{i}",
                    hacienda_id=h.id,
                    suerte_id=s.id,
                    peso_muestra=100.0 + i * 10,
                    peso_mineral=5.0 + i,
                    peso_vegetal_extrano=2.0 + i * 0.5,
                    usuario_id=u.id,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(w)
            db.commit()
        finally:
            db.close()

        cls.service = ReportTemplateService(db_session_factory=cls.SessionLocal)

    def setUp(self):
        """Limpiar plantillas antes de cada test."""
        db = self.SessionLocal()
        try:
            db.query(ReportTemplate).delete()
            db.commit()
        finally:
            db.close()

    def test_generate_report_produces_text_without_llm(self):
        """R5: generate_report produce texto con metricas seleccionadas, sin LLM."""
        template = self.service.create({
            "name": "Test Report",
            "schedule": ["08:00"],
            "user_ids": [],
            "metrics": ["count", "avg", "composition"],
        })

        db = self.SessionLocal()
        try:
            report = self.service.generate_report(template, db)
        finally:
            db.close()

        self.assertIn("Reporte Test Report", report)
        self.assertIn("Total pesajes", report)
        self.assertIn("Peso promedio", report)
        self.assertIn("Composicion", report)
        # Verificar que NO contiene texto de LLM
        self.assertNotIn("llama", report.lower())

    def test_generate_report_filters_metrics(self):
        """R5: Solo se incluyen las metricas seleccionadas."""
        template = self.service.create({
            "name": "Selectivo",
            "schedule": ["12:00"],
            "user_ids": [],
            "metrics": ["count"],
        })

        db = self.SessionLocal()
        try:
            report = self.service.generate_report(template, db)
        finally:
            db.close()

        self.assertIn("Total pesajes", report)
        self.assertNotIn("Peso promedio", report)
        self.assertNotIn("Composicion", report)
        self.assertNotIn("Tendencia", report)

    def test_generate_report_unknown_metric_skipped(self):
        """R5: Metrica desconocida se salta sin error fatal."""
        template = self.service.create({
            "name": "Con Desconocida",
            "schedule": ["12:00"],
            "user_ids": [],
            "metrics": ["count", "metrica_inexistente"],
        })

        db = self.SessionLocal()
        try:
            report = self.service.generate_report(template, db)
        finally:
            db.close()

        self.assertIn("Total pesajes", report)
        self.assertNotIn("metrica_inexistente", report)

    def test_generate_report_empty_metrics(self):
        """R5: Plantilla sin metricas genera solo encabezado."""
        template = self.service.create({
            "name": "Vacia",
            "schedule": ["12:00"],
            "user_ids": [],
            "metrics": [],
        })

        db = self.SessionLocal()
        try:
            report = self.service.generate_report(template, db)
        finally:
            db.close()

        self.assertIn("Reporte Vacia", report)
        self.assertNotIn("Total pesajes", report)

    def test_generate_report_with_std_metric(self):
        """F33/R16: generate_report con metrica std produce texto."""
        template = self.service.create({
            "name": "Std Report",
            "schedule": ["12:00"],
            "user_ids": [],
            "metrics": ["std"],
        })

        db = self.SessionLocal()
        try:
            report = self.service.generate_report(template, db)
        finally:
            db.close()

        self.assertIn("Reporte Std Report", report)
        self.assertIn("Desviacion estandar", report)

    def test_std_handler_returns_formatted_text(self):
        """F33/R16: handler std retorna texto formateado."""
        from src.report_templates import METRIC_HANDLERS
        handler = METRIC_HANDLERS.get("std")
        self.assertIsNotNone(handler, "std handler debe estar registrado")

        db = self.SessionLocal()
        try:
            result = handler(db, date.today())
        finally:
            db.close()

        self.assertIn("Desviacion estandar", result)


class TestReportTemplatePivot(unittest.TestCase):
    """Tests para la tabla pivote report_template_users (R19, R20)."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

        db = cls.SessionLocal()
        try:
            # Crear usuarios con telefonos
            admin1 = User(
                username="admin_tpl", password_hash="h", role="admin",
                full_name="Admin TPL", phone="+573001111111", is_active=True,
            )
            admin2 = User(
                username="corr_tpl", password_hash="h", role="corresponsal",
                full_name="Corr TPL", phone="+573002222222", is_active=True,
            )
            op = User(
                username="op_tpl", password_hash="h", role="operator",
                full_name="Op TPL", phone="+573003333333", is_active=True,
            )
            h = Hacienda(codigo="PIV", nombre="Hacienda Pivot")
            db.add_all([admin1, admin2, op, h])
            db.flush()
            s = Suerte(hacienda_id=h.id, codigo_suerte="S-PIV")
            db.add(s)
            db.commit()
            cls.admin1_id = admin1.id
            cls.admin2_id = admin2.id
            cls.op_id = op.id
        finally:
            db.close()

        cls.service = ReportTemplateService(db_session_factory=cls.SessionLocal)

    def setUp(self):
        """Limpiar plantillas antes de cada test y restaurar telefonos."""
        db = self.SessionLocal()
        try:
            # Restaurar telefonos de usuarios a los valores originales
            db.query(User).filter(User.id == self.admin1_id).update({"phone": "+573001111111"})
            db.query(User).filter(User.id == self.admin2_id).update({"phone": "+573002222222"})
            db.query(ReportTemplateUser).delete()
            db.query(ReportTemplate).delete()
            db.commit()
        finally:
            db.close()

    # ─── T30: test_create_with_user_ids (R19) ──────────────────────
    def test_create_with_user_ids(self):
        """Crear plantilla con user_ids y verificar recipients resueltos."""
        template = self.service.create({
            "name": "Reporte Pivot",
            "schedule": ["08:00"],
            "user_ids": [self.admin1_id, self.admin2_id],
            "metrics": ["count"],
        })

        # Verificar que get_one() resuelve los telefonos
        result = self.service.get_one(template.id)
        self.assertEqual(result["name"], "Reporte Pivot")
        self.assertIn("+573001111111", result["recipients"])
        self.assertIn("+573002222222", result["recipients"])
        self.assertEqual(len(result["recipients"]), 2)
        self.assertEqual(set(result["recipient_ids"]), {self.admin1_id, self.admin2_id})

    # ─── T30: test_recipients_resolve_from_users (R19) ─────────────
    def test_get_all_resolves_recipients(self):
        """get_all() resuelve recipients desde la tabla pivote + users."""
        self.service.create({
            "name": "Tpl1",
            "schedule": ["06:00"],
            "user_ids": [self.admin1_id],
            "metrics": ["avg"],
        })
        self.service.create({
            "name": "Tpl2",
            "schedule": ["14:00"],
            "user_ids": [self.admin1_id, self.admin2_id],
            "metrics": ["count"],
        })

        templates = self.service.get_all()
        self.assertEqual(len(templates), 2)

        tpl1 = next(t for t in templates if t["name"] == "Tpl1")
        tpl2 = next(t for t in templates if t["name"] == "Tpl2")

        self.assertEqual(tpl1["recipients"], ["+573001111111"])
        self.assertEqual(tpl1["recipient_ids"], [self.admin1_id])
        self.assertEqual(
            set(tpl2["recipients"]),
            {"+573001111111", "+573002222222"},
        )

    # ─── T30: test_get_recipient_phones (R20) ──────────────────────
    def test_get_recipient_phones(self):
        """get_recipient_phones() retorna telefonos actualizados."""
        template = self.service.create({
            "name": "SMS Report",
            "schedule": ["22:00"],
            "user_ids": [self.admin1_id, self.admin2_id],
            "metrics": ["trend"],
        })

        phones = self.service.get_recipient_phones(template.id)
        self.assertEqual(set(phones), {"+573001111111", "+573002222222"})

    # ─── T30: test_phone_change_reflected (R20) ────────────────────
    def test_phone_change_reflected_in_template(self):
        """Al cambiar telefono de un usuario, el template refleja el nuevo telefono."""
        template = self.service.create({
            "name": "Dynamic Phone",
            "schedule": ["10:00"],
            "user_ids": [self.admin1_id],
            "metrics": ["count"],
        })

        result = self.service.get_one(template.id)
        self.assertEqual(result["recipients"], ["+573001111111"])

        # Cambiar el telefono del usuario en la BD
        db = self.SessionLocal()
        try:
            user = db.query(User).filter(User.id == self.admin1_id).first()
            user.phone = "+573009999999"
            db.commit()
        finally:
            db.close()

        # Verificar que el template ahora muestra el nuevo telefono
        result2 = self.service.get_one(template.id)
        self.assertEqual(result2["recipients"], ["+573009999999"])
        self.assertEqual(result2["recipient_ids"], [self.admin1_id])

    # ─── T30: test_update_replaces_user_ids (R19) ──────────────────
    def test_update_replaces_recipients(self):
        """Al actualizar user_ids, se reemplazan los destinatarios."""
        template = self.service.create({
            "name": "Swap",
            "schedule": ["12:00"],
            "user_ids": [self.admin1_id],
            "metrics": ["min_max"],
        })

        result = self.service.get_one(template.id)
        self.assertEqual(result["recipients"], ["+573001111111"])

        # Actualizar con nuevos user_ids
        self.service.update(template.id, {
            "user_ids": [self.admin2_id],
        })

        result2 = self.service.get_one(template.id)
        self.assertEqual(result2["recipients"], ["+573002222222"])
        self.assertEqual(result2["recipient_ids"], [self.admin2_id])

    # ─── T30: test_create_no_users (R19) ───────────────────────────
    def test_create_without_user_ids(self):
        """Crear plantilla sin user_ids no agrega destinatarios."""
        template = self.service.create({
            "name": "Empty Recipients",
            "schedule": ["18:00"],
            "user_ids": [],
            "metrics": ["composition"],
        })

        result = self.service.get_one(template.id)
        self.assertEqual(result["recipients"], [])
        self.assertEqual(result["recipient_ids"], [])
