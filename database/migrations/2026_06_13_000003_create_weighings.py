"""Migration: Create weighings table."""

from sqlalchemy import BigInteger, Boolean, Column, Date, ForeignKey, Integer, Numeric, String, Time, TIMESTAMP, func, text
from sqlalchemy.engine import Connection


def upgrade(connection: Connection) -> None:
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS weighings (
            id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            fecha DATE NOT NULL,
            hora TIME NOT NULL,
            tractomula VARCHAR(32) NOT NULL DEFAULT '',
            vagon VARCHAR(32) NOT NULL DEFAULT '',
            numero_guia VARCHAR(32) NOT NULL DEFAULT '',
            hacienda_id BIGINT UNSIGNED NOT NULL,
            suerte_id BIGINT UNSIGNED NOT NULL,
            peso_muestra DECIMAL(10,3) NOT NULL,
            peso_mineral DECIMAL(10,3) NOT NULL,
            peso_vegetal_extrano DECIMAL(10,3) NOT NULL,
            usuario_id BIGINT UNSIGNED NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            enviado_pc BOOLEAN NOT NULL DEFAULT FALSE,
            FOREIGN KEY (hacienda_id) REFERENCES haciendas(id) ON DELETE RESTRICT,
            FOREIGN KEY (suerte_id) REFERENCES suertes(id) ON DELETE RESTRICT,
            FOREIGN KEY (usuario_id) REFERENCES users(id) ON DELETE RESTRICT
        )
    """))


def downgrade(connection: Connection) -> None:
    connection.execute(text("DROP TABLE IF EXISTS weighings"))
