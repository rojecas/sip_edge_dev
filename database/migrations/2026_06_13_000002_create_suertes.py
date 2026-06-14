"""Migration: Create suertes table."""

from sqlalchemy import BigInteger, Column, ForeignKey, String, TIMESTAMP, func, text
from sqlalchemy.engine import Connection


def upgrade(connection: Connection) -> None:
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS suertes (
            id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            hacienda_id BIGINT UNSIGNED NOT NULL,
            codigo_suerte VARCHAR(4) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP NULL DEFAULT NULL,
            FOREIGN KEY (hacienda_id) REFERENCES haciendas(id) ON DELETE RESTRICT,
            UNIQUE KEY uq_hacienda_codigo_suerte (hacienda_id, codigo_suerte)
        )
    """))


def downgrade(connection: Connection) -> None:
    connection.execute(text("DROP TABLE IF EXISTS suertes"))
