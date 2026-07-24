"""Migration: Add resend_count column to weighings table.

Feature 44 — rs232_resend: Reenvío de Datos RS232 desde Kiosko.
"""

from sqlalchemy.engine import Connection
from sqlalchemy.sql import text


def upgrade(connection: Connection) -> None:
    connection.execute(text("""
        ALTER TABLE weighings
        ADD COLUMN resend_count INTEGER NOT NULL DEFAULT 0
        AFTER enviado_pc
    """))


def downgrade(connection: Connection) -> None:
    connection.execute(text("""
        ALTER TABLE weighings
        DROP COLUMN resend_count
    """))
