"""Seed admin user on first run."""

import logging
import os

from sqlalchemy.orm import Session

from src.auth import hash_password
from src.models import User

logger = logging.getLogger(__name__)


def seed_admin_user(db: Session) -> None:
    if db.query(User).count() > 0:
        return
    password = os.environ.get("ADMIN_DEFAULT_PASSWORD", "admin")
    admin = User(
        username="admin",
        password_hash=hash_password(password),
        role="admin",
        full_name="Administrador",
        employee_code="",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    logger.info("Admin user seeded successfully")
