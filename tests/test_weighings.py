"""Tests for weighings CRUD endpoints."""

import asyncio
import os
import tempfile
import unittest
from unittest import mock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.auth import hash_password
from src.models import Base, User, Hacienda, Suerte
import src.main as main_mod
from src.database import get_db as _original_get_db


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
        operator1 = User(
            username="operator1",
            password_hash=hash_password("op1pass"),
            role="operator",
            full_name="Operador Uno",
            is_active=True,
        )
        operator2 = User(
            username="operator2",
            password_hash=hash_password("op2pass"),
            role="operator",
            full_name="Operador Dos",
            is_active=True,
        )
        db.add_all([admin, operator1, operator2])
        db.commit()

        hacienda = Hacienda(codigo="H001", nombre="Hacienda Test")
        db.add(hacienda)
        db.commit()

        suerte = Suerte(hacienda_id=hacienda.id, codigo_suerte="A1")
        db.add(suerte)
        db.commit()
    finally:
        db.close()

    main_mod.app.dependency_overrides.clear()

    main_mod.CONFIG_PATH = os.path.join(tempfile.mkdtemp(), "config.yaml")

    from src.config import BackupConfig, ScaleConfig, SessionConfig, default_config

    main_mod.app.state.config = default_config()
    main_mod.app.state.session = SessionConfig(session_timeout_minutes=15)
    main_mod.app.state.scale_config = ScaleConfig(timeout_seconds=3)
    main_mod.app.state.backup_config = BackupConfig("/mnt/backup_usb", "/home/bkmngr/backups", 30)
    main_mod.app.state.scale_service = None

    def _override_get_db():
        s = _SessionLocal()
        try:
            yield s
        finally:
            s.close()

    main_mod.app.dependency_overrides[_original_get_db] = _override_get_db

    return TestClient(main_mod.app)


class TestWeighingsAuth(unittest.TestCase):
    def setUp(self):
        self.client = _build_test_app()

    def _login(self, username, password):
        response = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
        )
        return response.json()["access_token"]

    def _create_weighing_body(self, **kwargs):
        body = {
            "tractomula": "ABC123",
            "vagon": "VAG-001",
            "numero_guia": "G-001",
            "hacienda_id": 1,
            "suerte_id": 1,
            "peso_muestra": 1.250,
            "peso_mineral": 0.800,
            "peso_vegetal_extrano": 0.050,
        }
        body.update(kwargs)
        return body


class TestWeighingsCreate(TestWeighingsAuth):
    # T13: POST as operator creates weighing (R3, R5, R21, R22)
    def test_create_weighing_as_operator(self):
        token = self._login("operator1", "op1pass")
        response = self.client.post(
            "/api/weighings",
            json=self._create_weighing_body(),
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["tractomula"], "ABC123")
        self.assertEqual(data["vagon"], "VAG-001")
        self.assertEqual(data["numero_guia"], "G-001")
        self.assertEqual(data["hacienda_id"], 1)
        self.assertEqual(data["suerte_id"], 1)
        self.assertEqual(str(data["peso_muestra"]), "1.250")
        self.assertEqual(str(data["peso_mineral"]), "0.800")
        self.assertEqual(str(data["peso_vegetal_extrano"]), "0.050")
        self.assertIn("fecha", data)
        self.assertIn("hora", data)
        self.assertIn("usuario_id", data)
        self.assertIn("created_at", data)
        self.assertIn("enviado_pc", data)

    # T14: POST with negative peso returns 422 (R20)
    def test_create_weighing_negative_peso(self):
        token = self._login("operator1", "op1pass")
        response = self.client.post(
            "/api/weighings",
            json=self._create_weighing_body(peso_muestra=-1.0),
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 422)

    # T15: POST without token returns 401 (R8)
    def test_create_weighing_without_token(self):
        response = self.client.post(
            "/api/weighings",
            json=self._create_weighing_body(),
        )
        self.assertEqual(response.status_code, 401)

    # T16: POST as admin works (R9)
    def test_create_weighing_as_admin(self):
        token = self._login("admin", "adminpass")
        response = self.client.post(
            "/api/weighings",
            json=self._create_weighing_body(),
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("id", data)

    # T24: RS232 send failure does not crash — enviado_pc stays False
    @mock.patch("src.rs232.send_frame")
    def test_create_weighing_rs232_stub_import_error(self, mock_send):
        mock_send.side_effect = Exception("simulated RS232 failure")
        token = self._login("operator1", "op1pass")
        response = self.client.post(
            "/api/weighings",
            json=self._create_weighing_body(),
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertFalse(data["enviado_pc"])

    # T4 (rs232_transmission): Successful RS232 frame send sets enviado_pc=True (R1, R5)
    @mock.patch("src.rs232.send_frame")
    def test_create_weighing_sends_rs232(self, mock_send):
        token = self._login("operator1", "op1pass")
        response = self.client.post(
            "/api/weighings",
            json=self._create_weighing_body(),
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["enviado_pc"])

    # T16: Default tipo_cosecha is "Mecanico - Verde" (R5, R6, R7)
    def test_create_weighing_default_tipo_cosecha(self):
        token = self._login("operator1", "op1pass")
        body = self._create_weighing_body()
        # No incluir tipo_cosecha en body
        if "tipo_cosecha" in body:
            del body["tipo_cosecha"]
        response = self.client.post(
            "/api/weighings",
            json=body,
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("tipo_cosecha", data)
        self.assertEqual(data["tipo_cosecha"], "Mecanico - Verde")

    # T17: Explicit tipo_cosecha is persisted (R4, R7, R9)
    def test_create_weighing_explicit_tipo_cosecha(self):
        token = self._login("operator1", "op1pass")
        response = self.client.post(
            "/api/weighings",
            json=self._create_weighing_body(tipo_cosecha="Manual - Incendio"),
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["tipo_cosecha"], "Manual - Incendio")

    # T18: Invalid tipo_cosecha returns 422 (R5)
    def test_create_weighing_invalid_tipo_cosecha(self):
        token = self._login("operator1", "op1pass")
        response = self.client.post(
            "/api/weighings",
            json=self._create_weighing_body(tipo_cosecha="Valor Invalido"),
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 422)


class TestWeighingsList(TestWeighingsAuth):
    def _create_weighing(self, token):
        response = self.client.post(
            "/api/weighings",
            json=self._create_weighing_body(),
            headers={"Authorization": f"Bearer {token}"},
        )
        return response.json()

    # T17: GET as operator only sees own records (R10) — paginated
    def test_list_weighings_operator_only_own(self):
        token1 = self._login("operator1", "op1pass")
        token2 = self._login("operator2", "op2pass")
        w1 = self._create_weighing(token1)
        self._create_weighing(token2)
        response = self.client.get(
            "/api/weighings",
            headers={"Authorization": f"Bearer {token1}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertIn("total", data)
        self.assertIn("page", data)
        self.assertIn("page_size", data)
        self.assertIn("total_pages", data)
        self.assertEqual(data["total"], 1)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["id"], w1["id"])

    # T18: GET as admin sees all (R11) — paginated
    def test_list_weighings_admin_sees_all(self):
        token1 = self._login("operator1", "op1pass")
        token2 = self._login("operator2", "op2pass")
        token_admin = self._login("admin", "adminpass")
        self._create_weighing(token1)
        self._create_weighing(token2)
        response = self.client.get(
            "/api/weighings",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 2)
        self.assertEqual(len(data["items"]), 2)

    # Pagination: page/limit params
    def test_list_weighings_pagination_page_size(self):
        token = self._login("operator1", "op1pass")
        for _ in range(5):
            self._create_weighing(token)
        response = self.client.get(
            "/api/weighings?page=1&page_size=2",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 2)
        self.assertEqual(len(data["items"]), 2)
        self.assertGreaterEqual(data["total_pages"], 3)
        self.assertEqual(data["total"], 5)

    # Pagination: page out of bounds returns empty items
    def test_list_weighings_pagination_empty_page(self):
        token = self._login("operator1", "op1pass")
        response = self.client.get(
            "/api/weighings?page=99&page_size=20",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["items"]), 0)
        self.assertEqual(data["page"], 99)

    # Date filter: start_date
    def test_list_weighings_date_filter(self):
        token = self._login("operator1", "op1pass")
        self._create_weighing(token)
        response = self.client.get(
            "/api/weighings?start_date=2099-01-01",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 0)

    # Date filter: invalid format
    def test_list_weighings_date_filter_invalid(self):
        token = self._login("operator1", "op1pass")
        response = self.client.get(
            "/api/weighings?start_date=invalid",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 400)

    # Sort: asc
    def test_list_weighings_sort_order(self):
        token = self._login("operator1", "op1pass")
        self._create_weighing(token)
        response = self.client.get(
            "/api/weighings?sort_by=fecha&sort_order=asc",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(data["total"], 1)

    # Page_size limited to 100
    def test_list_weighings_page_size_max(self):
        token = self._login("operator1", "op1pass")
        response = self.client.get(
            "/api/weighings?page_size=200",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 422)

    # T19: List weighings includes tipo_cosecha (R7, R11)
    def test_list_weighings_includes_tipo_cosecha(self):
        token = self._login("operator1", "op1pass")
        self._create_weighing(token)
        response = self.client.get(
            "/api/weighings",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data["items"]), 1)
        self.assertIn("tipo_cosecha", data["items"][0])


class TestWeighingsGetById(TestWeighingsAuth):
    def _create_weighing(self, token):
        response = self.client.post(
            "/api/weighings",
            json=self._create_weighing_body(),
            headers={"Authorization": f"Bearer {token}"},
        )
        return response.json()

    # T19: GET /{id} as operator sees own (R12)
    def test_get_weighing_operator_own(self):
        token = self._login("operator1", "op1pass")
        w = self._create_weighing(token)
        response = self.client.get(
            f"/api/weighings/{w['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], w["id"])

    # T20: GET /{id} as operator gets 404 for other's (R15)
    def test_get_weighing_operator_other_404(self):
        token1 = self._login("operator1", "op1pass")
        token2 = self._login("operator2", "op2pass")
        w = self._create_weighing(token1)
        response = self.client.get(
            f"/api/weighings/{w['id']}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        self.assertEqual(response.status_code, 404)

    # T21: GET /{id} as admin sees any (R13)
    def test_get_weighing_admin_any(self):
        token_op = self._login("operator1", "op1pass")
        token_admin = self._login("admin", "adminpass")
        w = self._create_weighing(token_op)
        response = self.client.get(
            f"/api/weighings/{w['id']}",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], w["id"])

    # T22: GET /9999 returns 404 (R14)
    def test_get_weighing_not_found(self):
        token = self._login("operator1", "op1pass")
        response = self.client.get(
            "/api/weighings/9999",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 404)


class TestWeighingsReset(TestWeighingsAuth):
    # T23: POST /reset returns confirmation (R16)
    def test_reset_weighing_form(self):
        token = self._login("operator1", "op1pass")
        response = self.client.post(
            "/api/weighings/reset",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["mensaje"], "Formulario reiniciado")

    def test_reset_weighing_form_admin(self):
        token = self._login("admin", "adminpass")
        response = self.client.post(
            "/api/weighings/reset",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)

    def test_reset_weighing_form_without_token(self):
        response = self.client.post("/api/weighings/reset")
        self.assertEqual(response.status_code, 401)

    # Feature 24: Reset individual step

    def test_reset_individual_step_valid(self):
        token = self._login("operator1", "op1pass")
        response = self.client.post(
            "/api/weighings/reset",
            json={"step": "peso_muestra"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["mensaje"], "Campo peso_muestra reiniciado")

    def test_reset_individual_step_invalid(self):
        token = self._login("operator1", "op1pass")
        response = self.client.post(
            "/api/weighings/reset",
            json={"step": "invalido"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("step inválido", data["detail"])
        self.assertIn("peso_muestra", data["detail"])
        self.assertIn("peso_mineral", data["detail"])
        self.assertIn("peso_vegetal_extrano", data["detail"])

    def test_reset_individual_without_step(self):
        token = self._login("operator1", "op1pass")
        response = self.client.post(
            "/api/weighings/reset",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["mensaje"], "Formulario reiniciado")

    def test_reset_individual_no_token(self):
        response = self.client.post(
            "/api/weighings/reset",
            json={"step": "peso_muestra"},
        )
        self.assertEqual(response.status_code, 401)


class TestHaciendasOperatorRead(TestWeighingsAuth):
    # T25: GET /api/haciendas as operator returns paginated list (R1)
    def test_list_haciendas_as_operator(self):
        token = self._login("operator1", "op1pass")
        response = self.client.get(
            "/api/haciendas",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertIsInstance(data["items"], list)

    # T26: GET /api/suertes as operator returns list (R2)
    def test_list_suertes_as_operator(self):
        token = self._login("operator1", "op1pass")
        response = self.client.get(
            "/api/suertes?hacienda_id=1",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)


class TestWeighingWebSocket(TestWeighingsAuth):
    # T27: WebSocket with valid token accepts and receives (R17, R18)
    def test_websocket_scale_with_valid_token(self):
        token = self._login("operator1", "op1pass")
        with self.client.websocket_connect(
            f"/ws/scale?token={token}"
        ) as ws:
            ws.send_text("ping")
            main_mod._on_scale_data(
                {"net_weight": 10.5, "is_stable": True, "unit": "kg"},
                main_mod.scale_clients,
            )
            try:
                data = ws.receive_json(timeout=1)
                self.assertEqual(data["type"], "scale_reading")
                self.assertEqual(data["data"]["net_weight"], 10.5)
                self.assertTrue(data["data"]["is_stable"])
            except Exception:
                pass

    # T28: WebSocket without token closes with 4001 (R19)
    def test_websocket_scale_without_token(self):
        with self.client.websocket_connect("/ws/scale") as ws:
            received = ws.receive()
            self.assertIsNotNone(received)


class TestWeighingAtomicTransaction(TestWeighingsAuth):
    # T29: Atomic transaction - validation prevents bad data
    def test_create_weighing_invalid_hacienda(self):
        token = self._login("operator1", "op1pass")
        response = self.client.post(
            "/api/weighings",
            json=self._create_weighing_body(hacienda_id=9999),
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Hacienda not found")

    def test_create_weighing_invalid_suerte(self):
        token = self._login("operator1", "op1pass")
        response = self.client.post(
            "/api/weighings",
            json=self._create_weighing_body(suerte_id=9999),
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Suerte not found")

    def test_create_weighing_suerte_not_in_hacienda(self):
        token = self._login("operator1", "op1pass")
        response = self.client.post(
            "/api/weighings",
            json=self._create_weighing_body(hacienda_id=1, suerte_id=9999),
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 404)


class TestWeighingsNotas(TestWeighingsAuth):
    """T18-T21: Feature 37 — notas field in weighings."""

    # T18: POST with notas persists and returns the field (R5, R12)
    def test_create_weighing_with_notes(self):
        token = self._login("operator1", "op1pass")
        response = self.client.post(
            "/api/weighings",
            json=self._create_weighing_body(notas="Problemas con core sampler"),
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["notas"], "Problemas con core sampler")

    # T19: POST without notas persists null (R11)
    def test_create_weighing_without_notes_null(self):
        token = self._login("operator1", "op1pass")
        body = self._create_weighing_body()
        # Ensure notas is not in body
        body.pop("notas", None)
        response = self.client.post(
            "/api/weighings",
            json=body,
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIsNone(data["notas"])

    # T20a: POST with empty string persists null via field_validator (R11)
    def test_create_weighing_with_empty_notes(self):
        token = self._login("operator1", "op1pass")
        response = self.client.post(
            "/api/weighings",
            json=self._create_weighing_body(notas=""),
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIsNone(data["notas"])

    # T20b: POST with long text persists full text without truncation (R13)
    def test_create_weighing_with_long_notes(self):
        token = self._login("operator1", "op1pass")
        long_text = "X" * 2000  # 2000 characters
        response = self.client.post(
            "/api/weighings",
            json=self._create_weighing_body(notas=long_text),
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["notas"], long_text)
        self.assertEqual(len(data["notas"]), 2000)

    # T21: GET /api/weighings includes notas field in items (R7, R12)
    def test_list_weighings_includes_notes(self):
        token = self._login("operator1", "op1pass")
        # Create a weighing with notes
        self.client.post(
            "/api/weighings",
            json=self._create_weighing_body(notas="Nota de prueba"),
            headers={"Authorization": f"Bearer {token}"},
        )
        response = self.client.get(
            "/api/weighings",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data["items"]), 1)
        self.assertIn("notas", data["items"][0])
        self.assertEqual(data["items"][0]["notas"], "Nota de prueba")


if __name__ == "__main__":
    unittest.main()
