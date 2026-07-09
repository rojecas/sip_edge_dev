"""Migration: Create report_template_users pivot table and drop recipients column.

Fase 8 — Feature 17 (frontend_analytics): Normaliza destinatarios de plantillas
de reportes usando tabla pivote en vez de JSON en columna recipients.
"""

from sqlalchemy import BigInteger, Column, ForeignKey, Integer, Index
from sqlalchemy.engine import Connection
from sqlalchemy.schema import PrimaryKeyConstraint
from sqlalchemy.sql import text


def upgrade(connection: Connection) -> None:
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS report_template_users (
            template_id BIGINT NOT NULL,
            user_id BIGINT NOT NULL,
            PRIMARY KEY (template_id, user_id),
            CONSTRAINT fk_rtu_template FOREIGN KEY (template_id)
                REFERENCES report_templates(id) ON DELETE CASCADE,
            CONSTRAINT fk_rtu_user FOREIGN KEY (user_id)
                REFERENCES users(id) ON DELETE CASCADE
        )
    """))
    connection.execute(text("""
        CREATE INDEX idx_rtu_user_id ON report_template_users(user_id)
    """))
    connection.execute(text("""
        ALTER TABLE report_templates DROP COLUMN recipients
    """))


def downgrade(connection: Connection) -> None:
    connection.execute(text("""
        ALTER TABLE report_templates ADD COLUMN recipients TEXT NOT NULL DEFAULT '[]'
    """))
    connection.execute(text("DROP TABLE IF EXISTS report_template_users"))
