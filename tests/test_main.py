"""Tests for main.py endpoints — anomaly history pagination, anomaly detection on demand."""

import unittest
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.models import Base, AnomalyLog, Hacienda, Suerte, User, Weighing


class TestAnomalyHistoryPagination(unittest.TestCase):
    """Tests for GET /api/anomalies/history with pagination (T3, T4)."""

    @classmethod
    def setUpClass(cls):
        from src.main import app, get_db
        from src.config import SessionConfig
        from src.auth import get_current_user

        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

        # Override get_db dependency to use SQLite in-memory
        def override_get_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": 1, "role": "admin", "iat": 9999999999,
        }

        # Set up session config to avoid session expiry
        app.state.session = SessionConfig(session_timeout_minutes=999999)

        cls.client = TestClient(app, raise_server_exceptions=False)

        # Seed test data
        db = cls.SessionLocal()
        try:
            u = User(username="admin", password_hash="h", role="admin", full_name="Admin")
            h = Hacienda(codigo="H001", nombre="Hacienda Test")
            db.add_all([u, h])
            db.flush()
            s = Suerte(hacienda_id=h.id, codigo_suerte="S01")
            db.add(s)
            db.flush()

            # Create 25 anomaly logs for pagination testing
            for i in range(25):
                w = Weighing(
                    fecha=date(2026, 6, 15),
                    hora=datetime.strptime("10:00", "%H:%M").time(),
                    tractomula=f"T{i}",
                    vagon=f"V{i}",
                    numero_guia=f"G{i}",
                    hacienda_id=h.id,
                    suerte_id=s.id,
                    peso_muestra=100.0,
                    peso_mineral=5.0,
                    peso_vegetal_extrano=2.0,
                    usuario_id=u.id,
                    created_at=datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
                )
                db.add(w)
                db.flush()

                al = AnomalyLog(
                    record_id=w.id,
                    layer="zscore",
                    z_score=3.5 + (i * 0.1),
                    metric_value=107.0 + i,
                    threshold=3.0,
                    llm_report=f"Reporte de anomalia {i}" if i % 2 == 0 else None,
                    sent_sms=i % 3 == 0,
                    created_at=datetime(2026, 6, 15, 10 + (i // 4), i % 60, 0, tzinfo=timezone.utc),
                )
                db.add(al)
            db.commit()
        finally:
            db.close()

    @classmethod
    def tearDownClass(cls):
        from src.main import app
        app.dependency_overrides.clear()

    # ─── T3: test_anomaly_history_pagination ───────────────────────
    def test_anomaly_history_pagination_response_format(self):
        """Verify paginated response has items, total, page, page_size, total_pages."""
        resp = self.client.get("/api/anomalies/history?page=1&page_size=10")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("items", data)
        self.assertIn("total", data)
        self.assertIn("page", data)
        self.assertIn("page_size", data)
        self.assertIn("total_pages", data)
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 10)
        self.assertEqual(len(data["items"]), 10)
        self.assertGreaterEqual(data["total"], 25)
        self.assertGreaterEqual(data["total_pages"], 3)

    def test_anomaly_history_page_2(self):
        """Verify page 2 returns different items."""
        resp = self.client.get("/api/anomalies/history?page=2&page_size=10")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["page"], 2)
        self.assertEqual(len(data["items"]), 10)

    def test_anomaly_history_last_page(self):
        """Verify last page returns fewer items."""
        resp = self.client.get("/api/anomalies/history?page=3&page_size=10")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertLessEqual(len(data["items"]), 10)
        self.assertEqual(data["page"], 3)

    # ─── T4: test_anomaly_history_default_params ───────────────────
    def test_anomaly_history_default_params(self):
        """Verify default page=1 and page_size=20."""
        resp = self.client.get("/api/anomalies/history")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 20)
        self.assertLessEqual(len(data["items"]), 20)

    # ─── Item structure verification ───────────────────────────────
    def test_anomaly_history_item_structure(self):
        """Verify each item has the expected fields."""
        resp = self.client.get("/api/anomalies/history?page=1&page_size=2")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        item = data["items"][0]
        expected_fields = ["id", "record_id", "layer", "z_score",
                          "metric_value", "threshold", "llm_report",
                          "sent_sms", "created_at"]
        for field in expected_fields:
            self.assertIn(field, item, f"Field {field} missing from anomaly log item")

    # ─── Edge cases ────────────────────────────────────────────────
    def test_anomaly_history_invalid_page_returns_422(self):
        """Verify page=0 returns validation error."""
        resp = self.client.get("/api/anomalies/history?page=0")
        self.assertEqual(resp.status_code, 422)

    def test_anomaly_history_invalid_page_size_returns_422(self):
        """Verify page_size=0 returns validation error."""
        resp = self.client.get("/api/anomalies/history?page_size=0")
        self.assertEqual(resp.status_code, 422)

    def test_anomaly_history_page_size_max(self):
        """Verify page_size=100 is accepted."""
        resp = self.client.get("/api/anomalies/history?page_size=100")
        self.assertEqual(resp.status_code, 200)


# ─── T20: test_anomaly_detect_on_demand ─────────────────────────────
class TestAnomalyDetectOnDemand(unittest.TestCase):
    """Tests for GET /api/anomalies on-demand detection (T20)."""

    @classmethod
    def setUpClass(cls):
        from src.main import app, get_db
        from src.config import AgentConfig, SessionConfig
        from src.anomaly_detector import AnomalyDetector
        from src.auth import get_current_user

        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

        def override_get_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": 1, "role": "admin", "iat": 9999999999,
        }

        app.state.session = SessionConfig(session_timeout_minutes=999999)

        # Set up anomaly detector
        agent_config = AgentConfig(
            window_size=10,
            window_hours=24,
            z_threshold=3.0,
            max_vegetal_to_muestra=0.5,
            max_mineral_to_muestra=0.3,
            max_rate_change=0.5,
            max_consecutive_anomalies=3,
        )
        app.state.anomaly_detector = AnomalyDetector(
            db_session_factory=cls.SessionLocal, config=agent_config,
        )

        cls.client = TestClient(app, raise_server_exceptions=False)

        # Seed test data
        db = cls.SessionLocal()
        try:
            u = User(username="admin", password_hash="h", role="admin", full_name="Admin")
            h = Hacienda(codigo="H001", nombre="Hacienda Test")
            db.add_all([u, h])
            db.flush()
            s = Suerte(hacienda_id=h.id, codigo_suerte="S01")
            db.add(s)
            db.flush()

            for i in range(5):
                w = Weighing(
                    fecha=date(2026, 6, 15),
                    hora=datetime.strptime("10:00", "%H:%M").time(),
                    tractomula=f"T{i}",
                    vagon=f"V{i}",
                    numero_guia=f"G{i}",
                    hacienda_id=h.id,
                    suerte_id=s.id,
                    peso_muestra=100.0,
                    peso_mineral=5.0,
                    peso_vegetal_extrano=2.0,
                    usuario_id=u.id,
                    tipo_cosecha="Mecanico - Verde",
                    created_at=datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
                )
                db.add(w)
            db.commit()
        finally:
            db.close()

    @classmethod
    def tearDownClass(cls):
        from src.main import app
        app.dependency_overrides.clear()

    def test_detect_anomalies_default_params(self):
        """GET /api/anomalies with default parameters returns list."""
        resp = self.client.get("/api/anomalies")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)

    def test_detect_anomalies_custom_params(self):
        """GET /api/anomalies with custom window and threshold."""
        resp = self.client.get("/api/anomalies?window=60&threshold=2.5")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)

    def test_detect_anomalies_with_tipo_cosecha(self):
        """GET /api/anomalies with tipo_cosecha filter."""
        resp = self.client.get("/api/anomalies?tipo_cosecha=Mecanico - Verde")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)


class TestEventLoopReference(unittest.TestCase):
    """Regression tests for Bug 2b — _event_loop module variable."""

    def test_event_loop_module_variable_exists(self):
        """Verify _event_loop is defined as module-level variable."""
        import src.main as main_mod
        self.assertTrue(hasattr(main_mod, "_event_loop"),
                        "main module must have _event_loop variable")

    def test_on_scale_data_uses_event_loop_when_set(self):
        """Verify _on_scale_data prefers stored _event_loop over
        _resolve_event_loop()."""
        import src.main as main_mod
        import asyncio

        # Save original
        original_loop = main_mod._event_loop

        try:
            # Set a sentinel loop
            sentinel = asyncio.new_event_loop()
            main_mod._event_loop = sentinel

            # Mock websocket
            ws = MagicMock()
            ws.send_text = AsyncMock()
            clients = {ws}

            # Call _on_scale_data — it should use sentinel loop
            with patch.object(main_mod, "_resolve_event_loop") as mock_resolve:
                main_mod._on_scale_data(
                    {"net_weight": 42.0, "is_stable": True, "unit": "kg"},
                    clients,
                )
                # _resolve_event_loop should NOT be called
                mock_resolve.assert_not_called()

            # Clean up sentinel loop
            sentinel.close()
        finally:
            main_mod._event_loop = original_loop


if __name__ == "__main__":
    unittest.main()
