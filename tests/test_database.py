"""Tests for database connection, models, and seed admin."""

import os
import tempfile
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.models import Base, User


class TestUserModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        with self.engine.connect() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                conn.execute(table.delete())
            conn.commit()

    def test_create_user_with_required_fields(self):
        user = User(username="testuser", password_hash="hash123", role="operator")
        self.db.add(user)
        self.db.commit()
        fetched = self.db.query(User).filter(User.username == "testuser").first()
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.username, "testuser")
        self.assertEqual(fetched.password_hash, "hash123")
        self.assertEqual(fetched.role, "operator")

    def test_default_values(self):
        user = User(username="admin", password_hash="hash", role="admin")
        self.db.add(user)
        self.db.commit()
        fetched = self.db.query(User).filter(User.username == "admin").first()
        self.assertEqual(fetched.full_name, "")
        self.assertEqual(fetched.employee_code, "")
        self.assertTrue(fetched.is_active)
        self.assertIsNotNone(fetched.created_at)
        self.assertIsNotNone(fetched.updated_at)

    def test_username_unique_constraint(self):
        user1 = User(username="dup", password_hash="hash", role="operator")
        user2 = User(username="dup", password_hash="hash2", role="admin")
        self.db.add(user1)
        self.db.commit()
        self.db.add(user2)
        with self.assertRaises(Exception):
            self.db.commit()

    def test_role_enum_values(self):
        for role in ("admin", "operator", "corresponsal"):
            user = User(username=role, password_hash="x", role=role)
            self.db.add(user)
        self.db.commit()
        count = self.db.query(User).count()
        self.assertEqual(count, 3)


class TestSeedAdmin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        with self.engine.connect() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                conn.execute(table.delete())
            conn.commit()

    def test_seed_creates_admin_when_table_empty(self):
        from src.seed import seed_admin_user

        seed_admin_user(self.db)
        user = self.db.query(User).filter(User.username == "admin").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.role, "admin")
        self.assertEqual(user.full_name, "Administrador")
        self.assertTrue(user.is_active)
        self.assertNotEqual(user.password_hash, "admin")

    def test_seed_does_not_duplicate_when_users_exist(self):
        from src.seed import seed_admin_user

        user = User(username="existing", password_hash="hash", role="operator")
        self.db.add(user)
        self.db.commit()
        count_before = self.db.query(User).count()
        seed_admin_user(self.db)
        count_after = self.db.query(User).count()
        self.assertEqual(count_before, count_after)

    def test_seed_uses_env_password(self):
        from src.seed import seed_admin_user

        os.environ["ADMIN_DEFAULT_PASSWORD"] = "testpass123"
        seed_admin_user(self.db)
        del os.environ["ADMIN_DEFAULT_PASSWORD"]
        user = self.db.query(User).filter(User.username == "admin").first()
        self.assertIsNotNone(user)
        from src.auth import verify_password
        self.assertTrue(verify_password("testpass123", user.password_hash))


class TestHashPassword(unittest.TestCase):
    def test_hash_and_verify_roundtrip(self):
        from src.auth import hash_password, verify_password

        plain = "my_secret_password"
        hashed = hash_password(plain)
        self.assertNotEqual(hashed, plain)
        self.assertTrue(verify_password(plain, hashed))

    def test_verify_wrong_password(self):
        from src.auth import hash_password, verify_password

        hashed = hash_password("correct")
        self.assertFalse(verify_password("wrong", hashed))

    def test_hash_is_deterministic_by_salt(self):
        from src.auth import hash_password

        h1 = hash_password("same")
        h2 = hash_password("same")
        self.assertNotEqual(h1, h2)
