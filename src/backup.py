"""Logica de backup: mysqldump, gzip, rotacion FIFO, copia USB y CRC32."""

import gzip
import logging
import os
import subprocess
import zlib
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

BACKUP_FILENAME_FORMAT = "backup_%Y%m%d_%H%M%S.sql.gz"


def _compute_crc32(filepath: str) -> str:
    """Calcula CRC32 de un archivo. Retorna hex string de 8 caracteres."""
    crc = 0
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            crc = zlib.crc32(chunk, crc)
    return f"{crc & 0xFFFFFFFF:08x}"


def _mysqldump_to_file(output_path: str) -> None:
    """Ejecuta mysqldump y escribe comprimido con gzip al archivo de salida.
    Usa stdin para pasar la contrasena (no visible en ps aux).
    Lanza RuntimeError si mysqldump falla."""
    host = os.environ["DB_HOST"]
    port = os.environ["DB_PORT"]
    user = os.environ["DB_USER"]
    password = os.environ["DB_PASSWORD"]
    name = os.environ["DB_NAME"]

    with open(output_path, "wb") as f_out:
        with gzip.open(f_out, "wb", compresslevel=6) as f_gz:
            proc = subprocess.Popen(
                [
                    "mysqldump",
                    f"--host={host}",
                    f"--port={port}",
                    f"--user={user}",
                    "--password",
                    name,
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = proc.communicate(input=password.encode())
            if proc.returncode != 0:
                raise RuntimeError(
                    f"mysqldump failed (exit={proc.returncode}): "
                    f"{stderr.decode().strip()}"
                )
            f_gz.write(stdout)


def _rotate_backups(local_dir: str, keep_days: int) -> None:
    """Elimina los archivos .sql.gz mas antiguos hasta no exceder keep_days."""
    files = sorted(
        [
            f
            for f in os.listdir(local_dir)
            if f.endswith(".sql.gz") and os.path.isfile(os.path.join(local_dir, f))
        ],
        key=lambda f: os.path.getmtime(os.path.join(local_dir, f)),
    )
    while len(files) > keep_days:
        removed = files.pop(0)
        os.unlink(os.path.join(local_dir, removed))
        logger.info("Rotated old backup: %s", removed)


def run_backup(usb_mount_path: str, local_dir: str, keep_days: int) -> None:
    """Ejecuta el ciclo completo de backup: dump, rotacion, copia USB y registro
    en BD. Crea su propia sesion de BD para insertar el BackupLog."""
    from src.database import SessionLocal
    from src.models import BackupLog

    os.makedirs(local_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.sql.gz"
    local_path = os.path.join(local_dir, filename)

    error_message = None
    local_checksum = None
    file_size = 0
    usb_copied = False
    usb_checksum = None

    try:
        _mysqldump_to_file(local_path)
        file_size = os.path.getsize(local_path)
        local_checksum = _compute_crc32(local_path)
        logger.info(
            "Backup created: %s (%d bytes, crc32=%s)",
            filename, file_size, local_checksum,
        )

        _rotate_backups(local_dir, keep_days)

        if os.path.isdir(usb_mount_path):
            usb_path = os.path.join(usb_mount_path, filename)
            with open(local_path, "rb") as src, open(usb_path, "wb") as dst:
                dst.write(src.read())
            usb_checksum = _compute_crc32(usb_path)
            if usb_checksum == local_checksum:
                usb_copied = True
                logger.info("Backup copied to USB: %s (crc32 ok)", usb_path)
            else:
                error_message = (
                    f"USB CRC32 mismatch: local={local_checksum}, usb={usb_checksum}"
                )
                logger.error(error_message)
        else:
            logger.info("USB mount path not found: %s", usb_mount_path)

    except Exception as e:
        error_message = str(e)
        logger.error("Backup failed: %s", error_message)

    db = SessionLocal()
    try:
        log_entry = BackupLog(
            filename=filename,
            file_size=file_size,
            local_checksum=local_checksum or "00000000",
            usb_copied=usb_copied,
            usb_checksum=usb_checksum,
            error_message=error_message,
        )
        db.add(log_entry)
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to write backup log entry", exc_info=True)
    finally:
        db.close()
