"""Migration: Create haciendas table."""

from sqlalchemy import BigInteger, Column, String, TIMESTAMP, func, text
from sqlalchemy.engine import Connection


def upgrade(connection: Connection) -> None:
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS haciendas (
            id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            codigo VARCHAR(8) NOT NULL UNIQUE,
            nombre VARCHAR(255) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP NULL DEFAULT NULL
        )
    """))


def downgrade(connection: Connection) -> None:
    connection.execute(text("DROP TABLE IF EXISTS haciendas"))
