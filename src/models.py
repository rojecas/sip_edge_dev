"""SQLAlchemy ORM models for SIP-Edge."""

from sqlalchemy import BigInteger, Boolean, Column, Date, Enum, ForeignKey, Index, Integer, Numeric, String, Text, Time, TIMESTAMP, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    username = Column(String(64), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False, default="")
    employee_code = Column(String(32), nullable=False, default="")
    role = Column(Enum("admin", "operator", "corresponsal"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    phone = Column(String(32), nullable=True, default=None)
    failed_login_attempts = Column(
        Integer, nullable=False, default=0, server_default="0"
    )
    force_password_change = Column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    reset_pin = Column(String(128), nullable=True, default=None)
    reset_pin_expires_at = Column(TIMESTAMP, nullable=True, default=None)
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
    manual_entry = Column(Boolean, nullable=False, default=False)


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


class EmergencyModeLog(Base):
    """Log de auditoria para el modo manual de emergencia.

    Cada accion (solicitud, activacion, extension, suspension, expiracion,
    comando invalido) queda registrada aqui para trazabilidad completa.
    """

    __tablename__ = "emergency_mode_log"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    request_id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("emergency_mode_log.id"),
        nullable=True,
        default=None,
        index=True,
    )
    status = Column(String(20), nullable=False, default="pending")
    analyst_id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.id"),
        nullable=True,
        default=None,
        index=True,
    )
    supervisor_id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.id"),
        nullable=True,
        default=None,
        index=True,
    )
    motivo = Column(Text, nullable=True, default=None)
    started_at = Column(TIMESTAMP, nullable=True, default=None)
    duration_seconds = Column(Integer, nullable=True, default=None)
    expires_at = Column(TIMESTAMP, nullable=True, default=None)
    cmd_source = Column(String(10), nullable=False)
    cmd_raw = Column(String(255), nullable=True, default=None)
    created_at = Column(
        TIMESTAMP, nullable=False, server_default=func.current_timestamp()
    )
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        default=None,
        server_onupdate=func.current_timestamp(),
    )
    sender_phone = Column(String(32), nullable=True, default=None)

    __table_args__ = (
        Index("idx_eml_status_expires", "status", "expires_at"),
        {"sqlite_autoincrement": True},
    )


class ReportTemplate(Base):
    """Plantilla de reporte programado con metricas seleccionables."""

    __tablename__ = "report_templates"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    name = Column(String(255), nullable=False)
    schedule = Column(Text, nullable=False)  # JSON array de horarios "HH:MM"
    recipients = Column(Text, nullable=False)  # JSON array de telefonos
    metrics = Column(Text, nullable=False)  # JSON array de metricas
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        TIMESTAMP, nullable=False, server_default=func.current_timestamp()
    )
    updated_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )

    __table_args__ = (
        Index("idx_rt_active", "is_active"),
        {"sqlite_autoincrement": True},
    )


class AnomalyLog(Base):
    """Registro de anomalias detectadas por capa."""

    __tablename__ = "anomaly_log"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    record_id = Column(
        BigInteger().with_variant(Integer, "sqlite"), nullable=False, index=True
    )
    layer = Column(String(20), nullable=False)
    z_score = Column(Numeric(10, 4), nullable=True, default=None)
    metric_value = Column(Numeric(10, 4), nullable=False)
    threshold = Column(Numeric(10, 4), nullable=False)
    llm_report = Column(Text, nullable=True, default=None)
    sent_sms = Column(Boolean, nullable=False, default=False)
    anomaly_context = Column(Text, nullable=True, default=None)  # JSON
    created_at = Column(
        TIMESTAMP, nullable=False, server_default=func.current_timestamp()
    )

    __table_args__ = (
        Index("idx_al_record", "record_id"),
        Index("idx_al_layer", "layer"),
        Index("idx_al_created", "created_at"),
        {"sqlite_autoincrement": True},
    )
