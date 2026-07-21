"""Tests for SqlTools: 17 herramientas SQL parametrizadas."""

import unittest
from datetime import date, datetime, time, timezone

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
    """Verificar que TOOL_DEFINITIONS tiene las 13 herramientas."""

    def test_tool_definitions_count(self):
        self.assertEqual(len(TOOL_DEFINITIONS), 17)

    def test_tool_definitions_format(self):
        for td in TOOL_DEFINITIONS:
            self.assertEqual(td["type"], "function")
            self.assertIn("name", td["function"])
            self.assertIn("description", td["function"])
            self.assertIn("parameters", td["function"])


class TestSqlToolsGetWeighingNotes(_SqlToolsTestBase):
    """T22-T24 (Feature 37): Tests para get_weighing_notes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()  # Carga datos base
        # Add notas to one weighing for test
        db = cls.SessionLocal()
        try:
            w = db.query(Weighing).filter(Weighing.vagon == "V0").first()
            if w:
                w.notas = "Problemas con core sampler, muestra muy humeda"
                db.commit()
        finally:
            db.close()

    # T22: Filter by vagon returns notes for that vagon (R9)
    def test_get_weighing_notes_by_vagon(self):
        result = self.tools.get_weighing_notes(vagon="V0")
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 1)
        self.assertEqual(result[0]["vagon"], "V0")
        self.assertIn("Problemas con core sampler", result[0]["notas"])

    # T23: Filter by date range returns notes in range (R9)
    def test_get_weighing_notes_by_date_range(self):
        result = self.tools.get_weighing_notes(
            fecha_inicio="2026-06-01", fecha_fin="2026-06-30"
        )
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 1)
        self.assertIn("id", result[0])
        self.assertIn("notas", result[0])

    # T24: No params raises ToolExecutionError (R9)
    def test_get_weighing_notes_no_params_error(self):
        with self.assertRaises(ToolExecutionError):
            self.tools.get_weighing_notes()

    # Verify execute_tool dispatches correctly
    def test_execute_tool_get_weighing_notes(self):
        result = self.tools.execute_tool(
            "get_weighing_notes",
            {"vagon": "V0", "limit": 5},
        )
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 1)


class TestSqlToolsInvalidTool(_SqlToolsTestBase):
    """T28: Verificar ToolExecutionError para tool inexistente."""

    def test_invalid_tool_raises(self):
        with self.assertRaises(ToolExecutionError):
            self.tools.execute_tool("tool_falsa", {})


# ─────────────────────────────────────────────────────────────
# F33: Nuevos tests — shortcuts, filtro vehiculo, nuevas tools,
#      agrupacion, compatibilidad inversa
# ─────────────────────────────────────────────────────────────

class TestDateShortcuts(_SqlToolsTestBase):
    """T2: Tests para _resolve_date_shortcut (R1, R2, R17)."""

    def test_shortcut_hoy(self):
        from datetime import date as dt
        today = dt.today()
        fi, ff = self.tools._resolve_date_shortcut("hoy")
        self.assertEqual(fi, today.isoformat())
        self.assertEqual(ff, today.isoformat())

    def test_shortcut_ayer(self):
        from datetime import date as dt, timedelta
        yesterday = dt.today() - timedelta(days=1)
        fi, ff = self.tools._resolve_date_shortcut("ayer")
        self.assertEqual(fi, yesterday.isoformat())
        self.assertEqual(ff, yesterday.isoformat())

    def test_shortcut_ultimos_7_dias(self):
        from datetime import date as dt, timedelta
        today = dt.today()
        start = today - timedelta(days=6)
        fi, ff = self.tools._resolve_date_shortcut("ultimos_7_dias")
        self.assertEqual(fi, start.isoformat())
        self.assertEqual(ff, today.isoformat())

    def test_shortcut_mes_actual(self):
        from datetime import date as dt
        today = dt.today()
        start = today.replace(day=1)
        fi, ff = self.tools._resolve_date_shortcut("mes_actual")
        self.assertEqual(fi, start.isoformat())
        self.assertEqual(ff, today.isoformat())

    def test_shortcut_personalizado_con_fechas(self):
        fi, ff = self.tools._resolve_date_shortcut("personalizado", "2026-06-01", "2026-06-15")
        self.assertEqual(fi, "2026-06-01")
        self.assertEqual(ff, "2026-06-15")

    def test_shortcut_personalizado_sin_fechas(self):
        with self.assertRaises(ToolExecutionError):
            self.tools._resolve_date_shortcut("personalizado")

    def test_shortcut_invalido(self):
        with self.assertRaises(ToolExecutionError):
            self.tools._resolve_date_shortcut("periodo_inventado")

    def test_shortcut_none_con_fechas(self):
        fi, ff = self.tools._resolve_date_shortcut(None, "2026-06-01", "2026-06-15")
        self.assertEqual(fi, "2026-06-01")
        self.assertEqual(ff, "2026-06-15")

    def test_shortcut_none_sin_fechas(self):
        with self.assertRaises(ToolExecutionError):
            self.tools._resolve_date_shortcut(None)


class TestVehicleFilter(unittest.TestCase):
    """T4: Tests para _apply_vehicle_filter (R5, R6, R17)."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    def test_filter_tractomula_adds_filter(self):
        db = self.SessionLocal()
        try:
            q = db.query(Weighing)
            q2 = SqlTools._apply_vehicle_filter(q, "tractomula")
            # Verificar que el WHERE traducido contiene tractomula
            sql = str(q2).lower()
            self.assertIn("tractomula", sql)
            self.assertIn("!=", sql)
        finally:
            db.close()

    def test_filter_vagon_adds_filter(self):
        db = self.SessionLocal()
        try:
            q = db.query(Weighing)
            q2 = SqlTools._apply_vehicle_filter(q, "vagon")
            sql = str(q2).lower()
            self.assertIn("vagon", sql)
            self.assertIn("!=", sql)
        finally:
            db.close()

    def test_filter_invalid_raises(self):
        db = self.SessionLocal()
        try:
            q = db.query(Weighing)
            with self.assertRaises(ToolExecutionError):
                SqlTools._apply_vehicle_filter(q, "avion")
        finally:
            db.close()

    def test_filter_none_no_filter(self):
        db = self.SessionLocal()
        try:
            q = db.query(Weighing)
            q2 = SqlTools._apply_vehicle_filter(q, None)
            self.assertIs(q, q2)  # mismo objeto, sin filtro
        finally:
            db.close()


class TestNewToolsAvgWeighingTime(_SqlToolsTestBase):
    """T10: Tests para get_avg_weighing_time (R7, R8, R18)."""

    def test_avg_weighing_time_with_data(self):
        result = self.tools.get_avg_weighing_time("2026-06-15", "2026-06-15")
        self.assertGreater(result["count"], 1)
        self.assertGreater(result["avg_time_minutes"], 0)

    def test_avg_weighing_time_single_record(self):
        # Crear un solo pesaje en un dia distinto
        db = self.SessionLocal()
        try:
            u = db.query(User).first()
            h = db.query(Hacienda).first()
            s = db.query(Suerte).first()
            w = Weighing(
                fecha=date(2026, 7, 1),
                hora=time(10, 0),
                tractomula="TX", vagon="VX", numero_guia="GX",
                hacienda_id=h.id, suerte_id=s.id,
                peso_muestra=100, peso_mineral=5, peso_vegetal_extrano=2,
                usuario_id=u.id,
                created_at=datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc),
            )
            db.add(w)
            db.commit()
        finally:
            db.close()

        result = self.tools.get_avg_weighing_time("2026-07-01", "2026-07-01")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["avg_time_minutes"], 0.0)
        self.assertIn("Datos insuficientes", result["message"])

    def test_avg_weighing_time_empty_range(self):
        result = self.tools.get_avg_weighing_time("2020-01-01", "2020-01-02")
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["avg_time_minutes"], 0.0)


class TestNewToolsAnomalyRate(_SqlToolsTestBase):
    """T11: Tests para get_anomaly_rate (R9, R10, R18)."""

    def test_anomaly_rate_with_data(self):
        from datetime import date as dt
        today = dt.today()
        result = self.tools.get_anomaly_rate(today.isoformat(), today.isoformat())
        self.assertGreaterEqual(result["total_weighings"], 0)
        self.assertGreaterEqual(result["total_anomalies"], 0)
        self.assertGreaterEqual(result["anomaly_rate_pct"], 0)

    def test_anomaly_rate_empty_range(self):
        result = self.tools.get_anomaly_rate("2020-01-01", "2020-01-02")
        self.assertEqual(result["total_weighings"], 0)
        self.assertEqual(result["total_anomalies"], 0)
        self.assertEqual(result["anomaly_rate_pct"], 0.0)

    def test_anomaly_rate_no_anomalies(self):
        # Rango donde hay pesajes pero no anomalias (las anomalias fueron creadas con created_at por defecto)
        result = self.tools.get_anomaly_rate("2025-01-01", "2025-01-02")
        self.assertEqual(result["total_anomalies"], 0)
        self.assertEqual(result["anomaly_rate_pct"], 0.0)


class TestNewToolsTopHaciendas(_SqlToolsTestBase):
    """T12: Tests para get_top_haciendas (R11, R12)."""

    def test_top_haciendas_with_data(self):
        result = self.tools.get_top_haciendas("2026-06-15", "2026-06-15", limite=5)
        self.assertIn("ranking", result)
        self.assertGreaterEqual(len(result["ranking"]), 1)
        self.assertIn("codigo", result["ranking"][0])

    def test_top_haciendas_invalid_limit(self):
        with self.assertRaises(ToolExecutionError):
            self.tools.get_top_haciendas("2026-06-15", "2026-06-15", limite=0)

    def test_top_haciendas_invalid_limit_negative(self):
        with self.assertRaises(ToolExecutionError):
            self.tools.get_top_haciendas("2026-06-15", "2026-06-15", limite=-5)


class TestNewToolsPeriodComparison(_SqlToolsTestBase):
    """T13: Tests para get_period_comparison (R13, R14, R18)."""

    def test_period_comparison_with_data(self):
        result = self.tools.get_period_comparison(
            "2026-06-15", "2026-06-15",
            "2026-06-14", "2026-06-14",
        )
        self.assertIn("periodo_actual", result)
        self.assertIn("periodo_anterior", result)
        self.assertIn("delta", result)
        self.assertIn("delta_pct", result)
        self.assertGreaterEqual(result["periodo_actual"]["count"], 1)

    def test_period_comparison_anterior_vacio(self):
        result = self.tools.get_period_comparison(
            "2026-06-15", "2026-06-15",
            "2020-01-01", "2020-01-02",
        )
        self.assertEqual(result["periodo_anterior"]["count"], 0)
        self.assertIsNone(result["delta_pct"]["count"])

    def test_period_comparison_both_empty(self):
        result = self.tools.get_period_comparison(
            "2020-01-01", "2020-01-02",
            "2020-01-03", "2020-01-04",
        )
        self.assertEqual(result["periodo_actual"]["count"], 0)
        self.assertEqual(result["periodo_anterior"]["count"], 0)


class TestBasicStatsWithGrouping(_SqlToolsTestBase):
    """T18: Tests para get_basic_stats con agrupacion y filtro (R3, R4, R5, R6, R17, R19)."""

    def test_basic_stats_with_dia_grouping(self):
        result = self.tools.get_basic_stats("2026-06-15", "2026-06-15", agrupacion="dia")
        self.assertEqual(result["agrupacion"], "dia")
        self.assertIn("grupos", result)
        self.assertGreaterEqual(len(result["grupos"]), 1)

    def test_basic_stats_with_turno_grouping(self):
        result = self.tools.get_basic_stats("2026-06-15", "2026-06-15", agrupacion="turno")
        self.assertEqual(result["agrupacion"], "turno")
        self.assertIn("grupos", result)
        self.assertGreaterEqual(len(result["grupos"]), 1)

    def test_basic_stats_with_tractomula_filter(self):
        result = self.tools.get_basic_stats(
            "2026-06-15", "2026-06-15", tipo_vehiculo="tractomula",
        )
        self.assertGreaterEqual(result["count"], 0)

    def test_basic_stats_invalid_grouping(self):
        with self.assertRaises(ToolExecutionError):
            self.tools.get_basic_stats("2026-06-15", "2026-06-15", agrupacion="anual")

    def test_basic_stats_no_new_params_compatibility(self):
        result = self.tools.get_basic_stats("2026-06-15", "2026-06-15")
        self.assertIn("count", result)
        self.assertIn("avg", result)
        self.assertEqual(result["count"], 10)


class TestBreakdownByHaciendaWithGrouping(_SqlToolsTestBase):
    """T19: Tests para get_breakdown_by_hacienda con agrupacion y filtro (R3, R4, R5, R6, R19)."""

    def test_breakdown_with_semana_grouping(self):
        result = self.tools.get_breakdown_by_hacienda(
            "2026-06-15", "2026-06-15", agrupacion="semana",
        )
        self.assertIn("grupos", result)
        self.assertGreaterEqual(len(result["grupos"]), 1)

    def test_breakdown_with_vagon_filter(self):
        result = self.tools.get_breakdown_by_hacienda(
            "2026-06-15", "2026-06-15", tipo_vehiculo="vagon",
        )
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 1)

    def test_breakdown_no_new_params_compatibility(self):
        result = self.tools.get_breakdown_by_hacienda("2026-06-15", "2026-06-15")
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 1)
        self.assertIn("hacienda_id", result[0])


class TestCustomPeriodSummaryWithGrouping(_SqlToolsTestBase):
    """T20: Tests para get_custom_period_summary con agrupacion y filtro (R3, R4, R5, R6, R19)."""

    def test_custom_period_with_mes_grouping(self):
        result = self.tools.get_custom_period_summary(
            "2026-06-15", "2026-06-15", agrupacion="mes",
        )
        self.assertIn("grupos", result)
        self.assertGreaterEqual(len(result["grupos"]), 1)

    def test_custom_period_with_tractomula_filter(self):
        result = self.tools.get_custom_period_summary(
            "2026-06-15", "2026-06-15", tipo_vehiculo="tractomula",
        )
        self.assertIn("count", result)

    def test_custom_period_no_new_params_compatibility(self):
        result = self.tools.get_custom_period_summary("2026-06-15", "2026-06-15")
        self.assertIn("count", result)
        self.assertEqual(result["count"], 10)


class TestCheckThresholdsWithAgentConfig(unittest.TestCase):
    """T30: Tests para check_thresholds con umbrales desde AgentConfig (R25)."""

    @classmethod
    def setUpClass(cls):
        from src.config import AgentConfig as AC
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

        db = cls.SessionLocal()
        try:
            u = User(username="th_op", password_hash="h", role="operator", full_name="Th Op")
            h = Hacienda(codigo="TH", nombre="Hacienda TH")
            db.add_all([u, h])
            db.flush()
            s = Suerte(hacienda_id=h.id, codigo_suerte="TH-S")
            db.add(s)
            db.flush()

            # Pesajes con ratios altos
            w1 = Weighing(
                fecha=date(2026, 6, 15),
                hora=time(9, 0),
                tractomula="TTH1", vagon="VTH1", numero_guia="GTH1",
                hacienda_id=h.id, suerte_id=s.id,
                peso_muestra=100, peso_mineral=40, peso_vegetal_extrano=60,
                usuario_id=u.id,
                created_at=datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc),
            )
            db.add(w1)
            db.commit()
        finally:
            db.close()

        # Sin AgentConfig → usa defaults 0.5 / 0.3
        cls.tools_default = SqlTools(db_session_factory=cls.SessionLocal)

        # Con AgentConfig con umbrales mas estrictos
        cls.tools_strict = SqlTools(
            db_session_factory=cls.SessionLocal,
            agent_config=AC(
                max_vegetal_to_muestra=0.2,
                max_mineral_to_muestra=0.2,
            ),
        )

    def test_check_thresholds_default_config(self):
        result = self.tools_default.check_thresholds(5)
        # Con default 0.5/0.3: ratio_veg=60/100=0.6 > 0.5 → violation
        # ratio_min=40/100=0.4 > 0.3 → violation
        self.assertGreaterEqual(result["total_violations"], 1)

    def test_check_thresholds_strict_config(self):
        result = self.tools_strict.check_thresholds(5)
        # Con strict 0.2/0.2: ratio_veg=0.6 > 0.2, ratio_min=0.4 > 0.2 → 2 violations
        self.assertGreaterEqual(result["total_violations"], 2)

    def test_check_thresholds_uses_injected_values(self):
        """Verifica que los umbrales usados son los de AgentConfig, no hardcodeados."""
        result = self.tools_strict.check_thresholds(5)
        for v in result["violations"]:
            if v["tipo"] == "vegetal_ratio_alto":
                self.assertEqual(v["umbral"], 0.2)
            elif v["tipo"] == "mineral_ratio_alto":
                self.assertEqual(v["umbral"], 0.2)
