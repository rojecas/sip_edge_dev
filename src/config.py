"""Modelo de dominio para configuracion del sistema: puertos RS485/RS232 y GSM."""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import logging
import os
import tempfile

import yaml

logger = logging.getLogger(__name__)

VALID_BAUDRATES = {300, 600, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200}
VALID_DATA_BITS = {5, 6, 7, 8}
VALID_PARITY = {"N", "E", "O", "M", "S"}
VALID_STOP_BITS = {1.0, 1.5, 2.0}
VALID_TEST_PORTS = {"rs485", "rs232", "gsm"}
DEFAULT_SESSION_TIMEOUT_MINUTES = 15
DEFAULT_SCALE_TIMEOUT = 3
DEFAULT_BACKUP_USB_MOUNT_PATH = "/mnt/backup_usb"
DEFAULT_BACKUP_LOCAL_DIR = "/home/bkmngr/backups"
DEFAULT_BACKUP_KEEP_DAYS = 30


@dataclass(frozen=True)
class SerialPortConfig:
    path: str
    baudrate: int
    parity: str
    data_bits: int
    stop_bits: float


@dataclass(frozen=True)
class GsmConfig:
    modem_index: int


@dataclass(frozen=True)
class SystemConfig:
    rs485: SerialPortConfig
    rs232: SerialPortConfig
    gsm: GsmConfig
    last_updated: str


@dataclass(frozen=True)
class SessionConfig:
    session_timeout_minutes: int


@dataclass(frozen=True)
class ScaleConfig:
    timeout_seconds: int


@dataclass(frozen=True)
class BackupConfig:
    usb_mount_path: str
    local_dir: str
    keep_days: int


DEFAULT_SMS_ADMIN_PHONES: list[str] = []
DEFAULT_SMS_SCHEDULED_REPORTS: list[str] = ["06:00", "14:00", "22:00"]


@dataclass(frozen=True)
class SmsConfig:
    admin_phones: list[str]
    scheduled_reports: list[str]


@dataclass(frozen=True)
class AgentConfig:
    llm_url: str = "http://localhost:8080"
    llm_model: str = "qwen2.5-1.5b-instruct-q4_k_m"
    llm_timeout: int = 30
    window_size: int = 120
    window_hours: int = 4
    z_threshold: float = 3.0
    max_vegetal_to_muestra: float = 0.5
    max_mineral_to_muestra: float = 0.3
    max_rate_change: float = 0.5
    max_consecutive_anomalies: int = 3


def default_config() -> SystemConfig:
    return SystemConfig(
        rs485=SerialPortConfig(
            path="/dev/ttyACM0",
            baudrate=115200,
            parity="N",
            data_bits=8,
            stop_bits=1.0,
        ),
        rs232=SerialPortConfig(
            path="/dev/ttyACM1",
            baudrate=115200,
            parity="N",
            data_bits=8,
            stop_bits=1.0,
        ),
        gsm=GsmConfig(modem_index=0),
        last_updated=datetime.now(timezone.utc).isoformat(),
    )


def load_config(path: str) -> tuple[SystemConfig, SessionConfig, ScaleConfig, BackupConfig, SmsConfig, AgentConfig]:
    session_config = SessionConfig(DEFAULT_SESSION_TIMEOUT_MINUTES)
    scale_config = ScaleConfig(DEFAULT_SCALE_TIMEOUT)
    backup_config = BackupConfig(
        DEFAULT_BACKUP_USB_MOUNT_PATH, DEFAULT_BACKUP_LOCAL_DIR, DEFAULT_BACKUP_KEEP_DAYS
    )
    sms_config = SmsConfig(
        admin_phones=list(DEFAULT_SMS_ADMIN_PHONES),
        scheduled_reports=list(DEFAULT_SMS_SCHEDULED_REPORTS),
    )
    agent_config = AgentConfig()
    if not os.path.exists(path):
        config = default_config()
        logger.warning("config.yaml not found, created with defaults")
        _atomic_write_sections(config, session_config, scale_config, backup_config, sms_config, agent_config, path)
        return config, session_config, scale_config, backup_config, sms_config, agent_config
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            raise ValueError("config.yaml is empty")
        config = SystemConfig(
            rs485=SerialPortConfig(**data["rs485"]),
            rs232=SerialPortConfig(**data["rs232"]),
            gsm=GsmConfig(**data["gsm"]),
            last_updated=data.get("last_updated", datetime.now(timezone.utc).isoformat()),
        )
        validate_config(config)
        if "session" in data and data["session"] is not None:
            session_config = SessionConfig(
                session_timeout_minutes=data["session"].get(
                    "session_timeout_minutes", DEFAULT_SESSION_TIMEOUT_MINUTES
                )
            )
        if "scale" in data and data["scale"] is not None:
            timeout = data["scale"].get("timeout_seconds", DEFAULT_SCALE_TIMEOUT)
            if not isinstance(timeout, int) or timeout < 1 or timeout > 10:
                timeout = DEFAULT_SCALE_TIMEOUT
            scale_config = ScaleConfig(timeout_seconds=timeout)
        if "backup" in data and data["backup"] is not None:
            usb = data["backup"].get("usb_mount_path", DEFAULT_BACKUP_USB_MOUNT_PATH)
            local = data["backup"].get("local_dir", DEFAULT_BACKUP_LOCAL_DIR)
            keep = data["backup"].get("keep_days", DEFAULT_BACKUP_KEEP_DAYS)
            if not isinstance(keep, int) or keep <= 0:
                logger.warning("backup.keep_days <= 0, usando default %d", DEFAULT_BACKUP_KEEP_DAYS)
                keep = DEFAULT_BACKUP_KEEP_DAYS
            backup_config = BackupConfig(usb, local, keep)
        if "sms" in data and data["sms"] is not None:
            admin_phones = data["sms"].get("admin_phones", [])
            if not isinstance(admin_phones, list):
                admin_phones = []
            scheduled_reports = data["sms"].get("scheduled_reports", DEFAULT_SMS_SCHEDULED_REPORTS)
            if not isinstance(scheduled_reports, list) or not scheduled_reports:
                scheduled_reports = list(DEFAULT_SMS_SCHEDULED_REPORTS)
            sms_config = SmsConfig(
                admin_phones=list(admin_phones),
                scheduled_reports=list(scheduled_reports),
            )
        if "agent" in data and data["agent"] is not None:
            ad = data["agent"]
            agent_config = AgentConfig(
                llm_url=ad.get("llm_url", agent_config.llm_url),
                llm_model=ad.get("llm_model", agent_config.llm_model),
                llm_timeout=ad.get("llm_timeout", agent_config.llm_timeout),
                window_size=ad.get("window_size", agent_config.window_size),
                window_hours=ad.get("window_hours", agent_config.window_hours),
                z_threshold=ad.get("z_threshold", agent_config.z_threshold),
                max_vegetal_to_muestra=ad.get("max_vegetal_to_muestra", agent_config.max_vegetal_to_muestra),
                max_mineral_to_muestra=ad.get("max_mineral_to_muestra", agent_config.max_mineral_to_muestra),
                max_rate_change=ad.get("max_rate_change", agent_config.max_rate_change),
                max_consecutive_anomalies=ad.get("max_consecutive_anomalies", agent_config.max_consecutive_anomalies),
            )
        return config, session_config, scale_config, backup_config, sms_config, agent_config
    except Exception:
        logger.warning("Failed to load config.yaml, using defaults", exc_info=True)
        config = default_config()
        sms_config = SmsConfig(
            admin_phones=list(DEFAULT_SMS_ADMIN_PHONES),
            scheduled_reports=list(DEFAULT_SMS_SCHEDULED_REPORTS),
        )
        _atomic_write_sections(config, session_config, scale_config, backup_config, sms_config, agent_config, path)
        return config, session_config, scale_config, backup_config, sms_config, agent_config


def save_config(config: SystemConfig, path: str) -> None:
    _save_system_config_atomic(config, path)


def save_system_config(config: SystemConfig, path: str) -> None:
    _save_system_config_atomic(config, path)


def save_session_config(config: SessionConfig, path: str) -> None:
    _save_session_config_atomic(config, path)


def save_scale_config(config: ScaleConfig, path: str) -> None:
    existing = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = yaml.safe_load(f) or {}
        except Exception:
            existing = {}
    existing["scale"] = {"timeout_seconds": config.timeout_seconds}
    yaml_text = yaml.dump(existing, default_flow_style=False, allow_unicode=True)
    _atomic_write(yaml_text, path)


def save_sms_config(config: SmsConfig, path: str) -> None:
    existing = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = yaml.safe_load(f) or {}
        except Exception:
            existing = {}
    existing["sms"] = {
        "admin_phones": config.admin_phones,
        "scheduled_reports": config.scheduled_reports,
    }
    yaml_text = yaml.dump(existing, default_flow_style=False, allow_unicode=True)
    _atomic_write(yaml_text, path)


def save_agent_config(config: AgentConfig, path: str) -> None:
    """Persiste la seccion agent en config.yaml preservando las demas secciones."""
    existing = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = yaml.safe_load(f) or {}
        except Exception:
            existing = {}
    existing["agent"] = asdict(config)
    yaml_text = yaml.dump(existing, default_flow_style=False, allow_unicode=True)
    _atomic_write(yaml_text, path)


def _save_system_config_atomic(config: SystemConfig, path: str) -> None:
    existing = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = yaml.safe_load(f) or {}
        except Exception:
            existing = {}
    existing["rs485"] = asdict(config.rs485)
    existing["rs232"] = asdict(config.rs232)
    existing["gsm"] = asdict(config.gsm)
    existing["last_updated"] = config.last_updated
    if "session" not in existing:
        existing["session"] = {"session_timeout_minutes": DEFAULT_SESSION_TIMEOUT_MINUTES}
    if "scale" not in existing:
        existing["scale"] = {"timeout_seconds": DEFAULT_SCALE_TIMEOUT}
    if "sms" not in existing:
        existing["sms"] = {
            "admin_phones": DEFAULT_SMS_ADMIN_PHONES,
            "scheduled_reports": DEFAULT_SMS_SCHEDULED_REPORTS,
        }
    yaml_text = yaml.dump(existing, default_flow_style=False, allow_unicode=True)
    _atomic_write(yaml_text, path)


def _save_session_config_atomic(config: SessionConfig, path: str) -> None:
    existing = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = yaml.safe_load(f) or {}
        except Exception:
            existing = {}
    existing["session"] = {"session_timeout_minutes": config.session_timeout_minutes}
    yaml_text = yaml.dump(existing, default_flow_style=False, allow_unicode=True)
    _atomic_write(yaml_text, path)


def _atomic_write(content: str, path: str) -> None:
    fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path) or ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def _atomic_write_sections(
    system_config: SystemConfig, session_config: SessionConfig,
    scale_config: ScaleConfig, backup_config: BackupConfig,
    sms_config: SmsConfig, agent_config: AgentConfig, path: str
) -> None:
    existing = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = yaml.safe_load(f) or {}
        except Exception:
            existing = {}
    existing["rs485"] = asdict(system_config.rs485)
    existing["rs232"] = asdict(system_config.rs232)
    existing["gsm"] = asdict(system_config.gsm)
    existing["last_updated"] = system_config.last_updated
    existing["session"] = {"session_timeout_minutes": session_config.session_timeout_minutes}
    existing["scale"] = {"timeout_seconds": scale_config.timeout_seconds}
    existing["backup"] = {
        "usb_mount_path": backup_config.usb_mount_path,
        "local_dir": backup_config.local_dir,
        "keep_days": backup_config.keep_days,
    }
    existing["sms"] = {
        "admin_phones": sms_config.admin_phones,
        "scheduled_reports": sms_config.scheduled_reports,
    }
    existing["agent"] = asdict(agent_config)
    yaml_text = yaml.dump(existing, default_flow_style=False, allow_unicode=True)
    _atomic_write(yaml_text, path)


def validate_config(config: SystemConfig) -> None:
    if config.rs485.baudrate not in VALID_BAUDRATES:
        raise ValueError(f"Invalid baudrate for rs485: {config.rs485.baudrate}")
    if config.rs485.data_bits not in VALID_DATA_BITS:
        raise ValueError(f"Invalid data_bits for rs485: {config.rs485.data_bits}")
    if config.rs485.parity not in VALID_PARITY:
        raise ValueError(f"Invalid parity for rs485: {config.rs485.parity}")
    if config.rs485.stop_bits not in VALID_STOP_BITS:
        raise ValueError(f"Invalid stop_bits for rs485: {config.rs485.stop_bits}")
    if config.rs232.baudrate not in VALID_BAUDRATES:
        raise ValueError(f"Invalid baudrate for rs232: {config.rs232.baudrate}")
    if config.rs232.data_bits not in VALID_DATA_BITS:
        raise ValueError(f"Invalid data_bits for rs232: {config.rs232.data_bits}")
    if config.rs232.parity not in VALID_PARITY:
        raise ValueError(f"Invalid parity for rs232: {config.rs232.parity}")
    if config.rs232.stop_bits not in VALID_STOP_BITS:
        raise ValueError(f"Invalid stop_bits for rs232: {config.rs232.stop_bits}")
    if not isinstance(config.gsm.modem_index, int) or config.gsm.modem_index < 0:
        raise ValueError(f"Invalid modem_index: {config.gsm.modem_index}")
