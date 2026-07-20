"""Migration: Add created_by column to haciendas table with FK to users.

Feature 39 — Trazabilidad: Registro de usuario creador en Haciendas y Suertes.
"""

from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.engine import Connection
from sqlalchemy.sql import text


def upgrade(connection: Connection) -> None:
    connection.execute(text("""
        ALTER TABLE haciendas
        ADD COLUMN created_by BIGINT NULL AFTER updated_at,
        ADD CONSTRAINT fk_haciendas_created_by FOREIGN KEY (created_by)
            REFERENCES users(id) ON DELETE SET NULL
    """))


def downgrade(connection: Connection) -> None:
    connection.execute(text("""
        ALTER TABLE haciendas
        DROP FOREIGN KEY fk_haciendas_created_by,
        DROP COLUMN created_by
    """))
