"""Tests for user management CRUD endpoints."""

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
        inactive_user = User(
            username="inactive",
            password_hash=hash_password("inactivepass"),
            role="operator",
            full_name="Inactivo",
            is_active=False,
        )
        db.add_all([admin, operator, inactive_user])
        db.commit()
    finally:
        db.close()

    import src.main as main_mod

    main_mod.app.dependency_overrides.clear()

    main_mod.CONFIG_PATH = os.path.join(tempfile.mkdtemp(), "config.yaml")

    from src.config import BackupConfig, ScaleConfig, SessionConfig, SystemConfig, default_config

    main_mod.app.state.config = default_config()
    main_mod.app.state.session = SessionConfig(session_timeout_minutes=15)
    main_mod.app.state.scale_config = ScaleConfig(timeout_seconds=3)
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


class TestUserManagement(unittest.TestCase):
    def setUp(self):
        self.client = _build_test_app()

    def _login(self, username="admin", password="adminpass"):
        response = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
        )
        return response.json()["access_token"]

    # --- R7: No token -> 401 ---
    def test_list_users_without_token(self):
        response = self.client.get("/api/users")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Not authenticated")

    def test_get_user_without_token(self):
        response = self.client.get("/api/users/1")
        self.assertEqual(response.status_code, 401)

    def test_create_user_without_token(self):
        response = self.client.post(
            "/api/users",
            json={"username": "new", "password": "pass", "full_name": "Nuevo", "role": "operator"},
        )
        self.assertEqual(response.status_code, 401)

    def test_update_user_without_token(self):
        response = self.client.put(
            "/api/users/1",
            json={"full_name": "Updated"},
        )
        self.assertEqual(response.status_code, 401)

    def test_delete_user_without_token(self):
        response = self.client.delete("/api/users/1")
        self.assertEqual(response.status_code, 401)

    # --- R6: Non-admin -> 403 ---
    def test_list_users_as_operator(self):
        token = self._login("operator", "operatorpass")
        response = self.client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Insufficient permissions")

    def test_get_user_as_operator(self):
        token = self._login("operator", "operatorpass")
        response = self.client.get(
            "/api/users/1",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_create_user_as_operator(self):
        token = self._login("operator", "operatorpass")
        response = self.client.post(
            "/api/users",
            json={"username": "new", "password": "pass", "full_name": "Nuevo", "role": "operator"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_update_user_as_operator(self):
        token = self._login("operator", "operatorpass")
        response = self.client.put(
            "/api/users/1",
            json={"full_name": "Updated"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_deactivate_user_as_operator(self):
        token = self._login("operator", "operatorpass")
        response = self.client.delete(
            "/api/users/1",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)

    # --- R1: List users (paginated) ---
    def test_list_users_as_admin(self):
        token = self._login()
        response = self.client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertIn("total", data)
        self.assertIn("page", data)
        self.assertIn("page_size", data)
        self.assertIn("total_pages", data)
        self.assertIsInstance(data["items"], list)
        self.assertGreaterEqual(len(data["items"]), 2)
        usernames = [u["username"] for u in data["items"]]
        self.assertIn("admin", usernames)
        self.assertIn("operator", usernames)
        self.assertIn("inactive", usernames)
        for user in data["items"]:
            self.assertNotIn("password_hash", user)
            self.assertIn("employee_code", user)
            self.assertIn("phone", user)

    # --- R2: Get user by ID ---
    def test_get_user_by_id(self):
        token = self._login()
        response = self.client.get(
            "/api/users/1",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["username"], "admin")
        self.assertIn("employee_code", data)
        self.assertIn("phone", data)
        self.assertNotIn("password_hash", data)

    def test_get_user_not_found(self):
        token = self._login()
        response = self.client.get(
            "/api/users/9999",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "User not found")

    # --- R3: Create user ---
    def test_create_user_valid(self):
        token = self._login()
        response = self.client.post(
            "/api/users",
            json={
                "username": "newuser",
                "password": "secret123",
                "full_name": "Nuevo Usuario",
                "employee_code": "EMP001",
                "phone": "573001234567",
                "role": "operator",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["username"], "newuser")
        self.assertEqual(data["full_name"], "Nuevo Usuario")
        self.assertEqual(data["employee_code"], "EMP001")
        self.assertEqual(data["phone"], "573001234567")
        self.assertEqual(data["role"], "operator")
        self.assertTrue(data["is_active"])
        self.assertNotIn("password_hash", data)
        self.assertIn("id", data)

    def test_create_user_duplicate_username(self):
        token = self._login()
        response = self.client.post(
            "/api/users",
            json={
                "username": "admin",
                "password": "pass",
                "full_name": "Duplicado",
                "employee_code": "EMP999",
                "phone": "573009999999",
                "role": "operator",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["detail"], "Ya existe un usuario con este nombre. Elija otro nombre para poder guardarlo.")

    def test_create_user_invalid_role(self):
        token = self._login()
        response = self.client.post(
            "/api/users",
            json={
                "username": "badrole",
                "password": "pass",
                "full_name": "Bad Role",
                "role": "superadmin",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 422)

    def test_create_user_empty_name(self):
        token = self._login()
        response = self.client.post(
            "/api/users",
            json={
                "username": "emptyname",
                "password": "pass",
                "full_name": "",
                "role": "operator",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 422)

    def test_create_user_empty_username(self):
        token = self._login()
        response = self.client.post(
            "/api/users",
            json={
                "username": "",
                "password": "pass",
                "full_name": "No Username",
                "role": "operator",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 422)

    def test_create_user_empty_password(self):
        token = self._login()
        response = self.client.post(
            "/api/users",
            json={
                "username": "nopass",
                "password": "",
                "full_name": "No Password",
                "role": "operator",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 422)

    def test_create_user_password_hashed(self):
        token = self._login()
        self.client.post(
            "/api/users",
            json={
                "username": "checkhash",
                "password": "plaintext",
                "full_name": "Hash Check",
                "employee_code": "EMP999",
                "phone": "573009999999",
                "role": "operator",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        response = self.client.post(
            "/api/auth/login",
            json={"username": "checkhash", "password": "plaintext"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())

        response = self.client.post(
            "/api/auth/login",
            json={"username": "checkhash", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 401)

    # --- R4: Update user ---
    def test_update_user_fields(self):
        token = self._login()
        response = self.client.put(
            "/api/users/2",
            json={
                "full_name": "Operador Modificado",
                "employee_code": "EMP002",
                "phone": "573009876543",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["full_name"], "Operador Modificado")
        self.assertEqual(data["employee_code"], "EMP002")
        self.assertEqual(data["phone"], "573009876543")
        self.assertNotIn("password_hash", data)

    def test_update_user_password(self):
        token = self._login()
        response = self.client.put(
            "/api/users/2",
            json={"new_password": "newsecret"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)

        login_response = self.client.post(
            "/api/auth/login",
            json={"username": "operator", "password": "newsecret"},
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertIn("access_token", login_response.json())

    def test_update_user_not_found(self):
        token = self._login()
        response = self.client.put(
            "/api/users/9999",
            json={"full_name": "Ghost"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "User not found")

    def test_update_user_invalid_role(self):
        token = self._login()
        response = self.client.put(
            "/api/users/1",
            json={"role": "superadmin"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 422)

    def test_update_user_set_active(self):
        token = self._login()
        response = self.client.put(
            "/api/users/2",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_active"])

        response = self.client.put(
            "/api/users/2",
            json={"is_active": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_active"])

    # --- R5: Deactivate user (logical delete) ---
    def test_deactivate_user(self):
        token = self._login()
        response = self.client.delete(
            "/api/users/2",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["is_active"])
        self.assertEqual(data["id"], 2)
        self.assertNotIn("password_hash", data)

        response = self.client.get(
            "/api/users/2",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_active"])

    def test_deactivate_user_already_inactive(self):
        token = self._login()
        response = self.client.delete(
            "/api/users/3",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_active"])

        response = self.client.delete(
            "/api/users/3",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_active"])

    def test_deactivate_user_not_found(self):
        token = self._login()
        response = self.client.delete(
            "/api/users/9999",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "User not found")

    # --- Pagination tests (R15) ---

    def test_list_users_default_pagination(self):
        """GET /api/users sin parametros retorna formato paginado con defaults."""
        token = self._login()
        response = self.client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertIn("total", data)
        self.assertIn("page", data)
        self.assertIn("page_size", data)
        self.assertIn("total_pages", data)
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 20)
        self.assertIsInstance(data["items"], list)
        self.assertGreaterEqual(data["total"], 0)

    def test_list_users_with_custom_pagination(self):
        """GET /api/users?page=1&page_size=5 retorna page_size=5."""
        token = self._login()
        response = self.client.get(
            "/api/users?page=1&page_size=5",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 5)
        self.assertLessEqual(len(data["items"]), 5)

    def test_list_users_page_beyond_total(self):
        """GET /api/users?page=999 retorna items vacio con metadata correcta."""
        token = self._login()
        response = self.client.get(
            "/api/users?page=999",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["page"], 999)
        self.assertEqual(data["items"], [])
        self.assertGreaterEqual(data["total"], 0)
        self.assertGreaterEqual(data["total_pages"], 1)


if __name__ == "__main__":
    unittest.main()
