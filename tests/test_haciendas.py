"""Tests for haciendas and suertes CRUD endpoints."""

import os
import tempfile
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.auth import hash_password
from src.models import Base, User


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
        db.add_all([admin, operator])
        db.commit()
    finally:
        db.close()

    import src.main as main_mod

    main_mod.app.dependency_overrides.clear()

    main_mod.CONFIG_PATH = os.path.join(tempfile.mkdtemp(), "config.yaml")

    from src.config import BackupConfig, SessionConfig, default_config

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


class TestHaciendasAuth(unittest.TestCase):
    def setUp(self):
        self.client = _build_test_app()

    def _login(self, username="admin", password="adminpass"):
        response = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
        )
        return response.json()["access_token"]

    # R21: No token -> 401
    def test_list_haciendas_without_token(self):
        response = self.client.get("/api/haciendas")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Not authenticated")

    def test_create_hacienda_without_token(self):
        response = self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": "Test"},
        )
        self.assertEqual(response.status_code, 401)

    def test_get_hacienda_without_token(self):
        response = self.client.get("/api/haciendas/1")
        self.assertEqual(response.status_code, 401)

    def test_update_hacienda_without_token(self):
        response = self.client.put(
            "/api/haciendas/1",
            json={"nombre": "Updated"},
        )
        self.assertEqual(response.status_code, 401)

    def test_delete_hacienda_without_token(self):
        response = self.client.delete("/api/haciendas/1")
        self.assertEqual(response.status_code, 401)

    def test_list_suertes_without_token(self):
        response = self.client.get("/api/suertes")
        self.assertEqual(response.status_code, 401)

    def test_create_suerte_without_token(self):
        response = self.client.post(
            "/api/suertes",
            json={"hacienda_id": 1, "codigo_suerte": "A1"},
        )
        self.assertEqual(response.status_code, 401)

    def test_get_suerte_without_token(self):
        response = self.client.get("/api/suertes/1")
        self.assertEqual(response.status_code, 401)

    def test_update_suerte_without_token(self):
        response = self.client.put(
            "/api/suertes/1",
            json={"codigo_suerte": "B2"},
        )
        self.assertEqual(response.status_code, 401)

    def test_delete_suerte_without_token(self):
        response = self.client.delete("/api/suertes/1")
        self.assertEqual(response.status_code, 401)

    # R22: Non-admin -> 403 for writes, but GET is now allowed for operators — paginated
    def test_list_haciendas_as_operator(self):
        token = self._login("operator", "operatorpass")
        response = self.client.get(
            "/api/haciendas",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data["items"], list)

    def test_create_hacienda_as_operator_returns_201(self):
        token = self._login("operator", "operatorpass")
        response = self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": "Test"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["codigo"], "H001")
        self.assertEqual(data["nombre"], "Test")
        self.assertIn("id", data)

    def test_get_hacienda_as_operator(self):
        token = self._login("operator", "operatorpass")
        response = self.client.get(
            "/api/haciendas/1",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 404)  # No hacienda 1 in test

    def test_update_hacienda_as_operator_returns_200(self):
        # First create a hacienda as admin
        admin_token = self._login("admin", "adminpass")
        create_resp = self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": "Original"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        hacienda_id = create_resp.json()["id"]

        # Now update as operator
        token = self._login("operator", "operatorpass")
        response = self.client.put(
            f"/api/haciendas/{hacienda_id}",
            json={"nombre": "Updated by operator"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["nombre"], "Updated by operator")

    def test_delete_hacienda_as_operator(self):
        token = self._login("operator", "operatorpass")
        response = self.client.delete(
            "/api/haciendas/1",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_list_suertes_as_operator(self):
        token = self._login("operator", "operatorpass")
        response = self.client.get(
            "/api/suertes",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_create_suerte_as_operator_returns_201(self):
        # First create a hacienda as admin (needed for suerte creation)
        admin_token = self._login("admin", "adminpass")
        hacienda_resp = self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": "Hacienda Test"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        hacienda_id = hacienda_resp.json()["id"]

        # Now create suerte as operator
        token = self._login("operator", "operatorpass")
        response = self.client.post(
            "/api/suertes",
            json={"hacienda_id": hacienda_id, "codigo_suerte": "A1"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["hacienda_id"], hacienda_id)
        self.assertEqual(data["codigo_suerte"], "A1")
        self.assertIn("id", data)

    def test_get_suerte_as_operator(self):
        token = self._login("operator", "operatorpass")
        response = self.client.get(
            "/api/suertes/1",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 404)  # No suerte 1 in test

    def test_update_suerte_as_operator_returns_200(self):
        # First create a hacienda and suerte as admin
        admin_token = self._login("admin", "adminpass")
        hacienda_resp = self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": "Hacienda Test"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        hacienda_id = hacienda_resp.json()["id"]
        suerte_resp = self.client.post(
            "/api/suertes",
            json={"hacienda_id": hacienda_id, "codigo_suerte": "A1"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        suerte_id = suerte_resp.json()["id"]

        # Now update as operator
        token = self._login("operator", "operatorpass")
        response = self.client.put(
            f"/api/suertes/{suerte_id}",
            json={"codigo_suerte": "B2"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["codigo_suerte"], "B2")

    def test_delete_suerte_as_operator(self):
        token = self._login("operator", "operatorpass")
        response = self.client.delete(
            "/api/suertes/1",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_new_hacienda_available_after_creation(self):
        """R10: New hacienda created by operator appears in GET /api/haciendas."""
        token = self._login("operator", "operatorpass")
        # Create hacienda as operator
        create_resp = self.client.post(
            "/api/haciendas",
            json={"codigo": "NEW001", "nombre": "Nueva Hacienda"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(create_resp.status_code, 201)
        new_id = create_resp.json()["id"]
        # GET haciendas and verify it appears
        list_resp = self.client.get(
            "/api/haciendas",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(list_resp.status_code, 200)
        data = list_resp.json()
        ids = [h["id"] for h in data["items"]]
        self.assertIn(new_id, ids)


class TestHaciendasCRUD(unittest.TestCase):
    def setUp(self):
        self.client = _build_test_app()

    def _login(self):
        response = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "adminpass"},
        )
        return response.json()["access_token"]

    def _auth_header(self):
        return {"Authorization": f"Bearer {self._login()}"}

    # R1: List haciendas — paginated
    def test_list_haciendas(self):
        # Create two haciendas
        self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": "Hacienda Uno"},
            headers=self._auth_header(),
        )
        self.client.post(
            "/api/haciendas",
            json={"codigo": "H002", "nombre": "Hacienda Dos"},
            headers=self._auth_header(),
        )
        response = self.client.get(
            "/api/haciendas",
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertIn("total", data)
        self.assertIn("page", data)
        self.assertIn("page_size", data)
        self.assertIn("total_pages", data)
        self.assertEqual(data["total"], 2)
        self.assertEqual(len(data["items"]), 2)

    # R2: Create hacienda
    def test_create_hacienda(self):
        response = self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": "Hacienda Uno"},
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["codigo"], "H001")
        self.assertEqual(data["nombre"], "Hacienda Uno")
        self.assertIn("id", data)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)
        self.assertNotIn("deleted_at", data)

    def test_create_hacienda_validation_empty_codigo(self):
        response = self.client.post(
            "/api/haciendas",
            json={"codigo": "", "nombre": "Test"},
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 422)

    def test_create_hacienda_validation_empty_nombre(self):
        response = self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": ""},
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 422)

    # R9: Duplicate codigo -> 409
    def test_create_hacienda_duplicate_codigo(self):
        self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": "Primera"},
            headers=self._auth_header(),
        )
        response = self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": "Duplicada"},
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["detail"],
            "Ya existe una hacienda con este codigo. Cambielo para poder guardarla.",
        )

    # R3: Get hacienda by id
    def test_get_hacienda(self):
        created = self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": "Hacienda Uno"},
            headers=self._auth_header(),
        )
        hid = created.json()["id"]
        response = self.client.get(
            f"/api/haciendas/{hid}",
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], hid)
        self.assertEqual(data["codigo"], "H001")
        self.assertEqual(data["nombre"], "Hacienda Uno")

    # R4: Get hacienda not found
    def test_get_hacienda_not_found(self):
        response = self.client.get(
            "/api/haciendas/9999",
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Hacienda not found")

    def test_get_hacienda_soft_deleted(self):
        created = self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": "Hacienda Uno"},
            headers=self._auth_header(),
        )
        hid = created.json()["id"]
        self.client.delete(
            f"/api/haciendas/{hid}",
            headers=self._auth_header(),
        )
        response = self.client.get(
            f"/api/haciendas/{hid}",
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 404)

    # R5: Update hacienda
    def test_update_hacienda(self):
        created = self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": "Hacienda Uno"},
            headers=self._auth_header(),
        )
        hid = created.json()["id"]
        response = self.client.put(
            f"/api/haciendas/{hid}",
            json={"nombre": "Hacienda Modificada", "codigo": "H002"},
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["nombre"], "Hacienda Modificada")
        self.assertEqual(data["codigo"], "H002")

    # R6: Update hacienda not found
    def test_update_hacienda_not_found(self):
        response = self.client.put(
            "/api/haciendas/9999",
            json={"nombre": "Ghost"},
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Hacienda not found")

    def test_update_hacienda_soft_deleted(self):
        created = self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": "Hacienda Uno"},
            headers=self._auth_header(),
        )
        hid = created.json()["id"]
        self.client.delete(
            f"/api/haciendas/{hid}",
            headers=self._auth_header(),
        )
        response = self.client.put(
            f"/api/haciendas/{hid}",
            json={"nombre": "Updated"},
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 404)

    def test_update_hacienda_duplicate_codigo(self):
        self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": "Primera"},
            headers=self._auth_header(),
        )
        created = self.client.post(
            "/api/haciendas",
            json={"codigo": "H002", "nombre": "Segunda"},
            headers=self._auth_header(),
        )
        hid = created.json()["id"]
        response = self.client.put(
            f"/api/haciendas/{hid}",
            json={"codigo": "H001"},
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 409)

    # R7: Soft delete hacienda
    def test_soft_delete_hacienda(self):
        created = self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": "Hacienda Uno"},
            headers=self._auth_header(),
        )
        hid = created.json()["id"]
        response = self.client.delete(
            f"/api/haciendas/{hid}",
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], hid)

    # R8: Delete hacienda not found
    def test_soft_delete_hacienda_not_found(self):
        response = self.client.delete(
            "/api/haciendas/9999",
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Hacienda not found")

    def test_soft_delete_hacienda_already_deleted(self):
        created = self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": "Hacienda Uno"},
            headers=self._auth_header(),
        )
        hid = created.json()["id"]
        self.client.delete(
            f"/api/haciendas/{hid}",
            headers=self._auth_header(),
        )
        response = self.client.delete(
            f"/api/haciendas/{hid}",
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 404)

    # R1 + R7: List excludes deleted — paginated
    def test_list_haciendas_excludes_deleted(self):
        c1 = self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": "Primera"},
            headers=self._auth_header(),
        )
        c2 = self.client.post(
            "/api/haciendas",
            json={"codigo": "H002", "nombre": "Segunda"},
            headers=self._auth_header(),
        )
        hid1 = c1.json()["id"]
        self.client.delete(
            f"/api/haciendas/{hid1}",
            headers=self._auth_header(),
        )
        response = self.client.get(
            "/api/haciendas",
            headers=self._auth_header(),
        )
        data = response.json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["codigo"], "H002")

    # R23: Response fields
    def test_hacienda_response_fields(self):
        created = self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": "Hacienda Uno"},
            headers=self._auth_header(),
        )
        data = created.json()
        self.assertIn("id", data)
        self.assertIn("codigo", data)
        self.assertIn("nombre", data)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)
        self.assertNotIn("deleted_at", data)


class TestSuertesCRUD(unittest.TestCase):
    def setUp(self):
        self.client = _build_test_app()

    def _login(self):
        response = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "adminpass"},
        )
        return response.json()["access_token"]

    def _auth_header(self):
        return {"Authorization": f"Bearer {self._login()}"}

    def _create_hacienda(self, codigo="H001", nombre="Hacienda Test"):
        response = self.client.post(
            "/api/haciendas",
            json={"codigo": codigo, "nombre": nombre},
            headers=self._auth_header(),
        )
        return response.json()["id"]

    # R10: List suertes
    def test_list_suertes(self):
        hid = self._create_hacienda()
        self.client.post(
            "/api/suertes",
            json={"hacienda_id": hid, "codigo_suerte": "A1"},
            headers=self._auth_header(),
        )
        self.client.post(
            "/api/suertes",
            json={"hacienda_id": hid, "codigo_suerte": "B2"},
            headers=self._auth_header(),
        )
        response = self.client.get(
            "/api/suertes",
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)

    # R11: Filter by hacienda_id
    def test_list_suertes_filter_by_hacienda(self):
        hid1 = self._create_hacienda("H001", "Hacienda Uno")
        hid2 = self._create_hacienda("H002", "Hacienda Dos")
        self.client.post(
            "/api/suertes",
            json={"hacienda_id": hid1, "codigo_suerte": "A1"},
            headers=self._auth_header(),
        )
        self.client.post(
            "/api/suertes",
            json={"hacienda_id": hid2, "codigo_suerte": "B1"},
            headers=self._auth_header(),
        )
        response = self.client.get(
            f"/api/suertes?hacienda_id={hid1}",
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["codigo_suerte"], "A1")

    # R12: Create suerte
    def test_create_suerte(self):
        hid = self._create_hacienda()
        response = self.client.post(
            "/api/suertes",
            json={"hacienda_id": hid, "codigo_suerte": "A1"},
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["hacienda_id"], hid)
        self.assertEqual(data["codigo_suerte"], "A1")
        self.assertIn("id", data)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)
        self.assertNotIn("deleted_at", data)

    def test_create_suerte_validation_empty_codigo(self):
        hid = self._create_hacienda()
        response = self.client.post(
            "/api/suertes",
            json={"hacienda_id": hid, "codigo_suerte": ""},
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 422)

    # R13: Create suerte with invalid hacienda
    def test_create_suerte_invalid_hacienda(self):
        response = self.client.post(
            "/api/suertes",
            json={"hacienda_id": 9999, "codigo_suerte": "A1"},
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Hacienda not found")

    def test_create_suerte_deleted_hacienda(self):
        hid = self._create_hacienda()
        self.client.delete(
            f"/api/haciendas/{hid}",
            headers=self._auth_header(),
        )
        response = self.client.post(
            "/api/suertes",
            json={"hacienda_id": hid, "codigo_suerte": "A1"},
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 404)

    # R14: Get suerte by id
    def test_get_suerte(self):
        hid = self._create_hacienda()
        created = self.client.post(
            "/api/suertes",
            json={"hacienda_id": hid, "codigo_suerte": "A1"},
            headers=self._auth_header(),
        )
        sid = created.json()["id"]
        response = self.client.get(
            f"/api/suertes/{sid}",
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], sid)
        self.assertEqual(data["codigo_suerte"], "A1")

    # R15: Get suerte not found
    def test_get_suerte_not_found(self):
        response = self.client.get(
            "/api/suertes/9999",
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Suerte not found")

    def test_get_suerte_soft_deleted(self):
        hid = self._create_hacienda()
        created = self.client.post(
            "/api/suertes",
            json={"hacienda_id": hid, "codigo_suerte": "A1"},
            headers=self._auth_header(),
        )
        sid = created.json()["id"]
        self.client.delete(
            f"/api/suertes/{sid}",
            headers=self._auth_header(),
        )
        response = self.client.get(
            f"/api/suertes/{sid}",
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 404)

    # R16: Update suerte
    def test_update_suerte(self):
        hid = self._create_hacienda()
        created = self.client.post(
            "/api/suertes",
            json={"hacienda_id": hid, "codigo_suerte": "A1"},
            headers=self._auth_header(),
        )
        sid = created.json()["id"]
        response = self.client.put(
            f"/api/suertes/{sid}",
            json={"codigo_suerte": "B2"},
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["codigo_suerte"], "B2")

    # R17: Update suerte not found
    def test_update_suerte_not_found(self):
        response = self.client.put(
            "/api/suertes/9999",
            json={"codigo_suerte": "B2"},
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Suerte not found")

    def test_update_suerte_soft_deleted(self):
        hid = self._create_hacienda()
        created = self.client.post(
            "/api/suertes",
            json={"hacienda_id": hid, "codigo_suerte": "A1"},
            headers=self._auth_header(),
        )
        sid = created.json()["id"]
        self.client.delete(
            f"/api/suertes/{sid}",
            headers=self._auth_header(),
        )
        response = self.client.put(
            f"/api/suertes/{sid}",
            json={"codigo_suerte": "B2"},
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 404)

    # R18: Soft delete suerte
    def test_soft_delete_suerte(self):
        hid = self._create_hacienda()
        created = self.client.post(
            "/api/suertes",
            json={"hacienda_id": hid, "codigo_suerte": "A1"},
            headers=self._auth_header(),
        )
        sid = created.json()["id"]
        response = self.client.delete(
            f"/api/suertes/{sid}",
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], sid)

    # R19: Delete suerte not found
    def test_soft_delete_suerte_not_found(self):
        response = self.client.delete(
            "/api/suertes/9999",
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Suerte not found")

    def test_soft_delete_suerte_already_deleted(self):
        hid = self._create_hacienda()
        created = self.client.post(
            "/api/suertes",
            json={"hacienda_id": hid, "codigo_suerte": "A1"},
            headers=self._auth_header(),
        )
        sid = created.json()["id"]
        self.client.delete(
            f"/api/suertes/{sid}",
            headers=self._auth_header(),
        )
        response = self.client.delete(
            f"/api/suertes/{sid}",
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 404)

    # R20: Duplicate (hacienda_id, codigo_suerte) -> 409
    def test_create_suerte_duplicate_codigo(self):
        hid = self._create_hacienda()
        self.client.post(
            "/api/suertes",
            json={"hacienda_id": hid, "codigo_suerte": "A1"},
            headers=self._auth_header(),
        )
        response = self.client.post(
            "/api/suertes",
            json={"hacienda_id": hid, "codigo_suerte": "A1"},
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["detail"],
            "Ya existe una suerte con este codigo en esta hacienda. Cambielo para poder guardarla.",
        )

    def test_create_suerte_same_codigo_different_hacienda(self):
        hid1 = self._create_hacienda("H001", "Hacienda Uno")
        hid2 = self._create_hacienda("H002", "Hacienda Dos")
        self.client.post(
            "/api/suertes",
            json={"hacienda_id": hid1, "codigo_suerte": "A1"},
            headers=self._auth_header(),
        )
        response = self.client.post(
            "/api/suertes",
            json={"hacienda_id": hid2, "codigo_suerte": "A1"},
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 201)

    # R24: Response fields
    def test_suerte_response_fields(self):
        hid = self._create_hacienda()
        response = self.client.post(
            "/api/suertes",
            json={"hacienda_id": hid, "codigo_suerte": "A1"},
            headers=self._auth_header(),
        )
        data = response.json()
        self.assertIn("id", data)
        self.assertIn("hacienda_id", data)
        self.assertIn("codigo_suerte", data)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)
        self.assertNotIn("deleted_at", data)

    # R10 + R18: List excludes deleted suertes
    def test_list_suertes_excludes_deleted(self):
        hid = self._create_hacienda()
        c1 = self.client.post(
            "/api/suertes",
            json={"hacienda_id": hid, "codigo_suerte": "A1"},
            headers=self._auth_header(),
        )
        self.client.post(
            "/api/suertes",
            json={"hacienda_id": hid, "codigo_suerte": "B2"},
            headers=self._auth_header(),
        )
        sid1 = c1.json()["id"]
        self.client.delete(
            f"/api/suertes/{sid1}",
            headers=self._auth_header(),
        )
        response = self.client.get(
            "/api/suertes",
            headers=self._auth_header(),
        )
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["codigo_suerte"], "B2")


class TestCreatedBy(unittest.TestCase):
    """Tests for Feature 39 — Trazabilidad: Registro de usuario creador."""

    def setUp(self):
        self.client = _build_test_app()

    def _login(self, username="admin", password="adminpass"):
        response = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
        )
        return response.json()["access_token"]

    def _auth_header(self):
        return {"Authorization": f"Bearer {self._login()}"}

    def _create_hacienda(self, codigo="H001", nombre="Hacienda Test"):
        response = self.client.post(
            "/api/haciendas",
            json={"codigo": codigo, "nombre": nombre},
            headers=self._auth_header(),
        )
        return response.json()

    # T15 — R3, R5: POST /api/haciendas asigna created_by
    def test_create_hacienda_sets_created_by(self):
        data = self._create_hacienda("H001", "Hacienda Test")
        self.assertIn("created_by", data)
        self.assertEqual(data["created_by"], 1)  # admin is user_id=1
        self.assertIn("created_by_username", data)
        self.assertEqual(data["created_by_username"], "admin")

    # T16 — R4, R6: POST /api/suertes asigna created_by
    def test_create_suerte_sets_created_by(self):
        hacienda = self._create_hacienda()
        response = self.client.post(
            "/api/suertes",
            json={"hacienda_id": hacienda["id"], "codigo_suerte": "A1"},
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("created_by", data)
        self.assertEqual(data["created_by"], 1)
        self.assertIn("created_by_username", data)
        self.assertEqual(data["created_by_username"], "admin")

    # T15 extra: operator también asigna created_by
    def test_create_hacienda_as_operator_sets_created_by(self):
        token = self._login("operator", "operatorpass")
        response = self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": "Test"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("created_by", data)
        self.assertEqual(data["created_by"], 2)  # operator is user_id=2
        self.assertEqual(data["created_by_username"], "operator")

    # T17 — R5: GET /api/haciendas incluye created_by
    def test_list_haciendas_includes_created_by(self):
        self._create_hacienda("H001", "Hacienda Uno")
        self._create_hacienda("H002", "Hacienda Dos")
        response = self.client.get(
            "/api/haciendas",
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data["items"]), 2)
        for h in data["items"]:
            self.assertIn("created_by", h)
            self.assertIn("created_by_username", h)
            self.assertEqual(h["created_by"], 1)
            self.assertEqual(h["created_by_username"], "admin")

    # T18 — R6: GET /api/suertes incluye created_by
    def test_list_suertes_includes_created_by(self):
        hacienda = self._create_hacienda()
        headers = self._auth_header()
        for cod in ["A1", "B2"]:
            self.client.post(
                "/api/suertes",
                json={"hacienda_id": hacienda["id"], "codigo_suerte": cod},
                headers=headers,
            )
        response = self.client.get(
            "/api/suertes",
            headers=headers,
        )
        self.assertEqual(response.status_code, 200)
        suertes_list = response.json()
        self.assertGreaterEqual(len(suertes_list), 2)
        for s in suertes_list:
            self.assertIn("created_by", s)
            self.assertIn("created_by_username", s)
            self.assertEqual(s["created_by"], 1)
            self.assertEqual(s["created_by_username"], "admin")

    # T19 — R9: Existing records with NULL created_by expose null
    def test_existing_records_have_null_created_by(self):
        # Create a hacienda first, then directly set created_by to NULL
        hacienda = self._create_hacienda("H001", "Hacienda Test")
        # Direct SQL to simulate pre-migration record
        from src.models import Hacienda as HaciendaModel

        # We need access to the test DB session
        import src.main as main_mod
        from src.database import get_db as _original_get_db
        override_gen = main_mod.app.dependency_overrides.get(_original_get_db)
        if override_gen is None:
            self.skipTest("DB override not available")
        session = next(override_gen())
        try:
            h = session.query(HaciendaModel).filter(HaciendaModel.id == hacienda["id"]).first()
            h.created_by = None
            session.commit()
        finally:
            session.close()

        # Now GET the hacienda — should have null created_by/created_by_username
        response = self.client.get(
            f"/api/haciendas/{hacienda['id']}",
            headers=self._auth_header(),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("created_by", data)
        self.assertIsNone(data["created_by"])
        self.assertIn("created_by_username", data)
        self.assertIsNone(data["created_by_username"])

    # T20 — R10: POST sin token sigue devolviendo 401
    def test_create_hacienda_without_token_still_returns_401(self):
        response = self.client.post(
            "/api/haciendas",
            json={"codigo": "H001", "nombre": "Test"},
        )
        self.assertEqual(response.status_code, 401)

    def test_create_suerte_without_token_still_returns_401(self):
        response = self.client.post(
            "/api/suertes",
            json={"hacienda_id": 1, "codigo_suerte": "A1"},
        )
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
