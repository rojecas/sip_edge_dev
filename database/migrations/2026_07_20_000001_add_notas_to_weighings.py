"""Migration: Add notas column to weighings table.

Feature 37 — notas_muestras: Campo de Notas Colapsable.
"""

from sqlalchemy.engine import Connection
from sqlalchemy.sql import text


def upgrade(connection: Connection) -> None:
    connection.execute(text("""
        ALTER TABLE weighings
        ADD COLUMN notas TEXT NULL DEFAULT NULL
        AFTER tipo_cosecha
    """))


def downgrade(connection: Connection) -> None:
    connection.execute(text("""
        ALTER TABLE weighings
        DROP COLUMN notas
    """))
