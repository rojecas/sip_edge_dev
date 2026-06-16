"""SQLAlchemy ORM models for SIP-Edge."""

from sqlalchemy import BigInteger, Boolean, Column, Date, Enum, ForeignKey, Integer, Numeric, String, Text, Time, TIMESTAMP, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    username = Column(String(64), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False, default="")
    document = Column(String(32), nullable=False, default="")
    role = Column(Enum("admin", "operator", "corresponsal"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    failed_login_attempts = Column(
        Integer, nullable=False, default=0, server_default="0"
    )
    created_at = Column(
        TIMESTAMP, nullable=False, server_default=func.current_timestamp()
    )
    updated_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )


class Hacienda(Base):
    __tablename__ = "haciendas"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    codigo = Column(String(8), nullable=False, unique=True)
    nombre = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), server_onupdate=func.current_timestamp())
    deleted_at = Column(TIMESTAMP, nullable=True, default=None)

    suertes = relationship("Suerte", back_populates="hacienda")


class Suerte(Base):
    __tablename__ = "suertes"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    hacienda_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("haciendas.id"), nullable=False)
    codigo_suerte = Column(String(4), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), server_onupdate=func.current_timestamp())
    deleted_at = Column(TIMESTAMP, nullable=True, default=None)
    __table_args__ = (UniqueConstraint("hacienda_id", "codigo_suerte"),)

    hacienda = relationship("Hacienda", back_populates="suertes")


class Weighing(Base):
    __tablename__ = "weighings"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    tractomula = Column(String(32), nullable=False, default="")
    vagon = Column(String(32), nullable=False, default="")
    numero_guia = Column(String(32), nullable=False, default="")
    hacienda_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("haciendas.id"), nullable=False)
    suerte_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("suertes.id"), nullable=False)
    peso_muestra = Column(Numeric(10, 3), nullable=False)
    peso_mineral = Column(Numeric(10, 3), nullable=False)
    peso_vegetal_extrano = Column(Numeric(10, 3), nullable=False)
    usuario_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    enviado_pc = Column(Boolean, nullable=False, default=False)


class BackupLog(Base):
    __tablename__ = "backup_logs"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    local_checksum = Column(String(8), nullable=False)
    usb_copied = Column(Boolean, nullable=False, default=False)
    usb_checksum = Column(String(8), nullable=True, default=None)
    error_message = Column(Text, nullable=True, default=None)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
