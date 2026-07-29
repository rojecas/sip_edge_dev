"""Script standalone de backup para ejecucion via cron.
Uso: python scripts/backup.py"""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
)

config_path = os.environ.get("CONFIG_PATH", "config.yaml")

from src.database import init_db
init_db()

from src.config import load_config
_, _, _, _, backup_config, _ = load_config(config_path)

from src.backup import run_backup
try:
    run_backup(backup_config.usb_mount_path, backup_config.local_dir, backup_config.keep_days)
except Exception as e:
    logging.error("Backup script failed: %s", e)
    sys.exit(1)
