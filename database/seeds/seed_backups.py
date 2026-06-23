"""Add extra backup logs for pagination testing on EdgeBox."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import BackupLog
from datetime import datetime

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "sip_user")
DB_PASS = os.environ.get("DB_PASSWORD", "sip_pass")
engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/sip_edge")
db = sessionmaker(bind=engine)()

existing = db.query(BackupLog).count()
if existing < 50:
    for d in range(1, 51):
        if d <= 30:
            dt = datetime(2026, 6, d, 6, 0)
        else:
            dt = datetime(2026, 5, d - 30, 6, 0)
        db.add(BackupLog(
            filename=f"dump_2026-{6 if d<=30 else 5:02d}-{d if d<=30 else d-30:02d}.sql.gz",
            file_size=102400 + d * 10000,
            local_checksum=f"{d:08x}"[:8],
            usb_copied=(d % 3 == 0),
            error_message="USB no disponible" if d % 5 == 0 else None,
            created_at=dt,
        ))
    db.commit()
    print(f"+ 50 backups creados (total: {db.query(BackupLog).count()})")
else:
    print(f"Ya hay {existing} backups")

db.close()
