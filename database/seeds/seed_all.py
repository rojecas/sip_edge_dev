"""Seed script - Pobla la BD con datos de ejemplo para pruebas locales."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import User, Hacienda, Suerte, Weighing, BackupLog
from src.auth import hash_password
from datetime import date, time, datetime
from decimal import Decimal
import random

DB_HOST = os.environ.get('DB_HOST', 'mariadb')
DB_NAME = os.environ.get('DB_NAME', 'sip_edge')
DB_USER = os.environ.get('DB_USER', 'sip_user')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'sip_pass')
DATABASE_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'

print(f'Conectando a {DATABASE_URL}...')
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    print()
    print('==> Creando usuarios...')
    existing = db.query(User).count()
    if existing > 0:
        print(f'Ya existen {existing} usuarios. Saltando...')
    else:
        users_data = [
            User(username='admin', password_hash=hash_password('admin'),
                 full_name='Administrador del Sistema', document='123456789',
                 role='admin', is_active=True),
            User(username='operador1', password_hash=hash_password('operador1'),
                 full_name='Carlos Perez', document='987654321',
                 role='operator', is_active=True),
            User(username='operador2', password_hash=hash_password('operador2'),
                 full_name='Maria Lopez', document='456789123',
                 role='operator', is_active=True),
            User(username='supervisor', password_hash=hash_password('supervisor'),
                 full_name='Juan Garcia', document='789123456',
                 role='operator', is_active=True),
            User(username='corresponsal1', password_hash=hash_password('corresponsal1'),
                 full_name='Pedro Martinez', document='321654987',
                 role='corresponsal', is_active=True, phone='573001234567'),
            User(username='inactivo', password_hash=hash_password('inactivo'),
                 full_name='Usuario Inactivo', document='111222333',
                 role='operator', is_active=False),
        ]
        db.add_all(users_data)
        db.commit()
        print(f'OK {len(users_data)} usuarios creados')

    print()
    print('==> Creando haciendas...')
    existing_h = db.query(Hacienda).count()
    if existing_h > 0:
        print(f'Ya existen {existing_h} haciendas. Saltando...')
    else:
        haciendas_data = [
            Hacienda(codigo='HDA001', nombre='Hacienda El Porvenir'),
            Hacienda(codigo='HDA002', nombre='Hacienda San Jose'),
            Hacienda(codigo='HDA003', nombre='Hacienda La Esperanza'),
            Hacienda(codigo='HDA004', nombre='Hacienda El Triunfo'),
            Hacienda(codigo='HDA005', nombre='Hacienda Santa Barbara'),
            Hacienda(codigo='HDA006', nombre='Hacienda Las Palmas'),
        ]
        db.add_all(haciendas_data)
        db.commit()
        print(f'OK {len(haciendas_data)} haciendas creadas')
        hda_elim = Hacienda(codigo='HDA999', nombre='Hacienda Eliminada', deleted_at=datetime.utcnow())
        db.add(hda_elim)
        db.commit()
        print('OK 1 hacienda soft-delete creada')

    print()
    print('==> Creando suertes...')
    existing_s = db.query(Suerte).count()
    if existing_s > 0:
        print(f'Ya existen {existing_s} suertes. Saltando...')
    else:
        haciendas = db.query(Hacienda).filter(Hacienda.deleted_at.is_(None)).all()
        suertes_map = {}
        suertes_map[haciendas[0].id] = ['A01', 'A02', 'B01']
        suertes_map[haciendas[1].id] = ['C01', 'C02', 'D01', 'D02']
        suertes_map[haciendas[2].id] = ['E01', 'E02']
        suertes_map[haciendas[3].id] = ['F01']
        suertes_map[haciendas[4].id] = ['G01', 'G02', 'G03']
        suertes_map[haciendas[5].id] = ['H01', 'H02']
        suertes_data = []
        for hid, cods in suertes_map.items():
            for c in cods:
                suertes_data.append(Suerte(hacienda_id=hid, codigo_suerte=c))
        db.add_all(suertes_data)
        db.commit()
        print(f'OK {len(suertes_data)} suertes creadas')

    print()
    print('==> Creando pesajes de ejemplo...')
    existing_w = db.query(Weighing).count()
    if existing_w > 0:
        print(f'Ya existen {existing_w} pesajes. Saltando...')
    else:
        users = db.query(User).filter(User.is_active == True).all()
        hs = db.query(Hacienda).filter(Hacienda.deleted_at.is_(None)).all()
        ss = db.query(Suerte).filter(Suerte.deleted_at.is_(None)).all()
        if users and hs and ss:
            wdata = []
            for i in range(15):
                wdata.append(Weighing(
                    fecha=date(2026, 6, 10 + (i % 10)),
                    hora=time(6 + (i % 12), (i * 7) % 60),
                    tractomula=f'ABC-{100 + i:03d}',
                    vagon=f'V{200 + i:03d}',
                    numero_guia=f'GUIA-{3000 + i:04d}',
                    hacienda_id=random.choice(hs).id,
                    suerte_id=random.choice(ss).id,
                    peso_muestra=Decimal(f'{random.uniform(10.0, 50.0):.3f}'),
                    peso_mineral=Decimal(f'{random.uniform(5.0, 30.0):.3f}'),
                    peso_vegetal_extrano=Decimal(f'{random.uniform(0.0, 5.0):.3f}'),
                    usuario_id=random.choice(users).id,
                    enviado_pc=random.choice([True, False]),
                    manual_entry=random.choice([True, False]),
                ))
            db.add_all(wdata)
            db.commit()
            print(f'OK {len(wdata)} pesajes creados')

    print()
    print('==> Creando registros de backup...')
    existing_b = db.query(BackupLog).count()
    if existing_b > 0:
        print(f'Ya existen {existing_b} backups. Saltando...')
    else:
        bdata = [
            BackupLog(filename='dump_2026-06-18.sql.gz', file_size=1048576,
                      local_checksum='a1b2c3d4', usb_copied=True,
                      usb_checksum='a1b2c3d4', error_message=None,
                      created_at=datetime(2026, 6, 18, 6, 0)),
            BackupLog(filename='dump_2026-06-17.sql.gz', file_size=512000,
                      local_checksum='e5f6g7h8', usb_copied=False,
                      usb_checksum=None, error_message='USB no disponible',
                      created_at=datetime(2026, 6, 17, 6, 0)),
            BackupLog(filename='dump_2026-06-16.sql.gz', file_size=768000,
                      local_checksum='i9j0k1l2', usb_copied=True,
                      usb_checksum='i9j0k1l2', error_message=None,
                      created_at=datetime(2026, 6, 16, 6, 0)),
        ]
        db.add_all(bdata)
        db.commit()
        print(f'OK {len(bdata)} backups creados')

    print()
    print('=' * 50)
    print('SEED COMPLETADO EXITOSAMENTE')
    print('=' * 50)
    print()
    print('Credenciales de prueba:')
    print('   Admin:       admin / admin')
    print('   Operador1:   operador1 / operador1')
    print('   Operador2:   operador2 / operador2')
    print('   Supervisor:  supervisor / supervisor')
    print()
    print('Haciendas: 6 activas + 1 soft-delete')
    print('Suertes: 15 en total')
    print('Pesajes: 15 de ejemplo')
    print('Backups: 3 registros')
    print()

except Exception as e:
    db.rollback()
    print(f'ERROR: {e}')
    raise
finally:
    db.close()
