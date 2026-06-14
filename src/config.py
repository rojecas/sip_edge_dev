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


def load_config(path: str) -> tuple[SystemConfig, SessionConfig, ScaleConfig, BackupConfig]:
    session_config = SessionConfig(DEFAULT_SESSION_TIMEOUT_MINUTES)
    scale_config = ScaleConfig(DEFAULT_SCALE_TIMEOUT)
    backup_config = BackupConfig(
        DEFAULT_BACKUP_USB_MOUNT_PATH, DEFAULT_BACKUP_LOCAL_DIR, DEFAULT_BACKUP_KEEP_DAYS
    )
    if not os.path.exists(path):
        config = default_config()
        logger.warning("config.yaml not found, created with defaults")
        _atomic_write_sections(config, session_config, scale_config, backup_config, path)
        return config, session_config, scale_config, backup_config
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
            usb_mount_path = data["backup"].get("usb_mount_path", DEFAULT_BACKUP_USB_MOUNT_PATH)
            local_dir = data["backup"].get("local_dir", DEFAULT_BACKUP_LOCAL_DIR)
            keep_days = data["backup"].get("keep_days", DEFAULT_BACKUP_KEEP_DAYS)
            if not isinstance(keep_days, int) or keep_days <= 0:
                logger.warning("backup.keep_days invalid (%s), using default %d", keep_days, DEFAULT_BACKUP_KEEP_DAYS)
                keep_days = DEFAULT_BACKUP_KEEP_DAYS
            backup_config = BackupConfig(
                usb_mount_path=usb_mount_path,
                local_dir=local_dir,
                keep_days=keep_days,
            )
        return config, session_config, scale_config, backup_config
    except Exception:
        logger.warning("Failed to load config.yaml, using defaults", exc_info=True)
        config = default_config()
        _atomic_write_sections(config, session_config, scale_config, backup_config, path)
        return config, session_config, scale_config, backup_config


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
    if "backup" not in existing:
        existing["backup"] = {
            "usb_mount_path": DEFAULT_BACKUP_USB_MOUNT_PATH,
            "local_dir": DEFAULT_BACKUP_LOCAL_DIR,
            "keep_days": DEFAULT_BACKUP_KEEP_DAYS,
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
    scale_config: ScaleConfig, backup_config: BackupConfig, path: str
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
