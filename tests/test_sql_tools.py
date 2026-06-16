"""Tests for SqlTools: 12 herramientas SQL parametrizadas."""

import unittest
from datetime import date, datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.models import (
    AnomalyLog, Base, Hacienda, Suerte, User, Weighing,
)
from src.sql_tools import SqlTools, ToolExecutionError, TOOL_DEFINITIONS


class _SqlToolsTestBase(unittest.TestCase):
    """Base con DB SQLite en memoria y datos de prueba."""

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
            u1 = User(username="op1", password_hash="h", role="operator", full_name="Op Uno")
            u2 = User(username="op2", password_hash="h", role="operator", full_name="Op Dos")
            h1 = Hacienda(codigo="H001", nombre="Hacienda A")
            h2 = Hacienda(codigo="H002", nombre="Hacienda B")
            db.add_all([u1, u2, h1, h2])
            db.flush()

            s1 = Suerte(hacienda_id=h1.id, codigo_suerte="A1")
            s2 = Suerte(hacienda_id=h2.id, codigo_suerte="B1")
            db.add_all([s1, s2])
            db.flush()

            base_date = date(2026, 6, 15)
            weighings = []
            for i in range(10):
                w = Weighing(
                    fecha=base_date,
                    hora=datetime.strptime(f"{8+i//2:02d}:00", "%H:%M").time(),
                    tractomula=f"T{i}",
                    vagon=f"V{i}",
                    numero_guia=f"G{i}",
                    hacienda_id=h1.id if i < 5 else h2.id,
                    suerte_id=s1.id if i < 5 else s2.id,
                    peso_muestra=100.0 + i * 10,
                    peso_mineral=5.0 + i * 0.5,
                    peso_vegetal_extrano=2.0 + i * 0.2,
                    usuario_id=u1.id if i % 2 == 0 else u2.id,
                    created_at=datetime(2026, 6, 15, 8 + i // 2, 0, 0, tzinfo=timezone.utc),
                )
                weighings.append(w)
            db.add_all(weighings)

            # Anadir algunas anomalias para las tools de anomalias
            a1 = AnomalyLog(
                record_id=1, layer="zscore", z_score=4.5,
                metric_value=150.0, threshold=3.0,
            )
            a2 = AnomalyLog(
                record_id=3, layer="relacional", z_score=None,
                metric_value=0.8, threshold=0.5,
            )
            db.add_all([a1, a2])
            db.commit()
        finally:
            db.close()

        cls.tools = SqlTools(db_session_factory=cls.SessionLocal)


class TestSqlToolsBasicStats(_SqlToolsTestBase):
    """T28: Verificar count, avg, min, max, std."""

    def test_basic_stats_with_data(self):
        result = self.tools.get_basic_stats("2026-06-15", "2026-06-15")
        self.assertEqual(result["count"], 10)
        self.assertGreater(result["avg"], 0)
        self.assertGreater(result["max"], result["min"])
        self.assertGreaterEqual(result["std"], 0)

    def test_basic_stats_empty_range(self):
        result = self.tools.get_basic_stats("2026-01-01", "2026-01-02")
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["avg"], 0.0)
        self.assertEqual(result["min"], 0.0)
        self.assertEqual(result["max"], 0.0)
        self.assertEqual(result["std"], 0.0)

    def test_basic_stats_filtered_by_muestra(self):
        result = self.tools.get_basic_stats("2026-06-15", "2026-06-15", "muestra")
        self.assertEqual(result["count"], 10)
        self.assertGreater(result["avg"], 100)

    def test_percentiles_basic(self):
        result = self.tools.get_percentiles("2026-06-15", "2026-06-15", 50)
        self.assertEqual(result["count"], 10)
        self.assertGreater(result["valor"], 0)

    def test_percentiles_empty(self):
        result = self.tools.get_percentiles("2026-01-01", "2026-01-02", 50)
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["valor"], 0.0)

    def test_percentiles_invalid(self):
        with self.assertRaises(ToolExecutionError):
            self.tools.get_percentiles("2026-06-15", "2026-06-15", -1)

    def test_moving_average(self):
        result = self.tools.get_moving_average(5)
        self.assertEqual(result["count"], 5)
        self.assertGreater(result["moving_average"], 0)

    def test_moving_average_invalid_window(self):
        with self.assertRaises(ToolExecutionError):
            self.tools.get_moving_average(0)

    def test_trend_with_data(self):
        result = self.tools.get_trend("2026-06-15", "2026-06-15")
        self.assertEqual(result["count"], 10)
        self.assertIn(result["interpretacion"], ["creciente", "decreciente", "estable"])

    def test_trend_empty(self):
        result = self.tools.get_trend("2026-01-01", "2026-01-02")
        self.assertEqual(result["count"], 0)


class TestSqlToolsBreakdown(_SqlToolsTestBase):
    """T28: Verificar desglose por hacienda y operador."""

    def test_breakdown_by_hacienda(self):
        result = self.tools.get_breakdown_by_hacienda("2026-06-15", "2026-06-15")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertIn("hacienda_id", result[0])
        self.assertIn("codigo", result[0])

    def test_breakdown_by_operator(self):
        result = self.tools.get_breakdown_by_operator("2026-06-15", "2026-06-15")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertIn("username", result[0])


class TestSqlToolsComposition(_SqlToolsTestBase):
    """T28: Verificar proporcion de materiales."""

    def test_material_composition(self):
        result = self.tools.get_material_composition("2026-06-15", "2026-06-15")
        self.assertGreater(result["total"], 0)
        self.assertGreater(result["pct_muestra"], 0)
        self.assertGreaterEqual(result["pct_mineral"], 0)
        self.assertGreaterEqual(result["pct_vegetal"], 0)

    def test_material_composition_empty(self):
        result = self.tools.get_material_composition("2026-01-01", "2026-01-02")
        self.assertEqual(result["total"], 0.0)

    def test_shift_summary(self):
        result = self.tools.get_shift_summary("2026-06-15", "tarde")
        self.assertEqual(result["fecha"], "2026-06-15")
        self.assertEqual(result["turno"], "tarde")
        self.assertIn("count", result)

    def test_shift_summary_invalid_turno(self):
        with self.assertRaises(ToolExecutionError):
            self.tools.get_shift_summary("2026-06-15", "invalido")

    def test_daily_summary(self):
        result = self.tools.get_daily_summary("2026-06-15")
        self.assertEqual(result["fecha"], "2026-06-15")
        self.assertEqual(result["count"], 10)

    def test_custom_period_summary(self):
        result = self.tools.get_custom_period_summary("2026-06-15", "2026-06-15")
        self.assertEqual(result["fecha_inicio"], "2026-06-15")
        self.assertEqual(result["count"], 10)

    def test_detect_anomalies(self):
        result = self.tools.detect_anomalies(10, 3.0)
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 1)

    def test_check_thresholds(self):
        result = self.tools.check_thresholds(10)
        self.assertIn("count", result)
        self.assertIn("violations", result)


class TestSqlToolsExecuteTool(_SqlToolsTestBase):
    """T28: Verificar dispatcher execute_tool()."""

    def test_execute_tool_valid(self):
        result = self.tools.execute_tool(
            "get_basic_stats",
            {"fecha_inicio": "2026-06-15", "fecha_fin": "2026-06-15"},
        )
        self.assertIn("count", result)

    def test_execute_tool_invalid_name(self):
        """R14: Tool inexistente debe lanzar ToolExecutionError."""
        with self.assertRaises(ToolExecutionError):
            self.tools.execute_tool("herramienta_inexistente", {})

    def test_execute_tool_invalid_params(self):
        """R14: Parametros invalidos deben lanzar ToolExecutionError."""
        with self.assertRaises(ToolExecutionError):
            self.tools.execute_tool("get_basic_stats", {})


class TestToolDefinitions(unittest.TestCase):
    """Verificar que TOOL_DEFINITIONS tiene las 12 herramientas."""

    def test_tool_definitions_count(self):
        self.assertEqual(len(TOOL_DEFINITIONS), 12)

    def test_tool_definitions_format(self):
        for td in TOOL_DEFINITIONS:
            self.assertEqual(td["type"], "function")
            self.assertIn("name", td["function"])
            self.assertIn("description", td["function"])
            self.assertIn("parameters", td["function"])


class TestSqlToolsInvalidTool(_SqlToolsTestBase):
    """T28: Verificar ToolExecutionError para tool inexistente."""

    def test_invalid_tool_raises(self):
        with self.assertRaises(ToolExecutionError):
            self.tools.execute_tool("tool_falsa", {})
