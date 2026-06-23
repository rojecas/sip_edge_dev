"""Add extra test data for pagination testing on EdgeBox."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import User, Hacienda, Suerte, BackupLog
from src.auth import hash_password
from datetime import datetime

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "sip_user")
DB_PASS = os.environ.get("DB_PASSWORD", "sip_pass")
engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/sip_edge")
db = sessionmaker(bind=engine)()

# Add 30 operators
existing_u = {u.username for u in db.query(User.username).all()}
users_to_add = []
for i in range(1, 31):
    uname = f"operador{i:03d}"
    if uname not in existing_u:
        users_to_add.append(User(
            username=uname,
            password_hash=hash_password(uname),
            full_name=f"Operador Prueba {i}",
            employee_code=f"EMP{i:06d}",
            role="operator",
            is_active=True,
        ))
if users_to_add:
    db.add_all(users_to_add)
    db.commit()
    print(f"+ {len(users_to_add)} usuarios creados")
else:
    print("Usuarios ya existentes")

# Add 25 haciendas
existing_h = {h.codigo for h in db.query(Hacienda.codigo).all()}
haciendas_to_add = []
for i in range(1, 26):
    code = f"HDA{i:03d}"
    if code not in existing_h:
        haciendas_to_add.append(Hacienda(codigo=code, nombre=f"Hacienda Prueba {i}"))
if haciendas_to_add:
    db.add_all(haciendas_to_add)
    db.commit()
    print(f"+ {len(haciendas_to_add)} haciendas creadas")
else:
    print("Haciendas ya existentes")

# Add suertes (4 per hacienda)
haciendas = db.query(Hacienda).filter(Hacienda.deleted_at == None).all()
existing_s = {(s.hacienda_id, s.codigo_suerte) for s in db.query(Suerte.hacienda_id, Suerte.codigo_suerte).all()}
suertes_to_add = []
for h in haciendas:
    for j in range(1, 5):
        code = f"S{j:02d}"
        if (h.id, code) not in existing_s:
            suertes_to_add.append(Suerte(hacienda_id=h.id, codigo_suerte=code))
if suertes_to_add:
    db.add_all(suertes_to_add)
    db.commit()
    print(f"+ {len(suertes_to_add)} suertes creadas")
else:
    print("Suertes ya existentes")

# Add 50 backup logs
existing_b = db.query(BackupLog).count()
if existing_b < 50:
    for d in range(1, 51):
        db.add(BackupLog(
            filename=f"dump_2026-06-{d:02d}.sql.gz",
            file_size=102400 + d * 10000,
            local_checksum=f"chk{d:06d}",
            usb_copied=(d % 3 == 0),
            error_message="USB no disponible" if d % 5 == 0 else None,
            created_at=datetime(2026, 6, d, 6, 0),
        ))
    db.commit()
    print(f"+ 50 backups creados")
else:
    print(f"Ya hay {existing_b} backups")

db.close()
print("Done.")
