# Design — backup_system

> Decisiones tecnicas para respaldo diario con mysqldump, rotacion FIFO 30 dias,
> copia a USB con CRC32 y registro en backup_logs.

## Archivos creados / modificados

| Archivo | Accion | Proposito |
|---------|--------|-----------|
| `src/backup.py` | **CREAR** | Logica de backup: mysqldump, gzip, rotacion, copia USB, CRC32 |
| `src/config.py` | MODIFICAR | Anadir `BackupConfig` dataclass + `load_backup_config` + seccion `backup` |
| `src/models.py` | MODIFICAR | Anadir modelo ORM `BackupLog` |
| `src/main.py` | MODIFICAR | Anadir `backup_router` con `GET /api/backup/status` y `POST /api/backup/run`; incluir `BackupConfig` en lifespan |
| `scripts/backup.py` | **CREAR** | Script standalone para cron |
| `tests/test_backup.py` | **CREAR** | Tests de logica de backup, rotacion, CRC32, endpoints |
| `config.yaml` | **MODIFICADO** (runtime) | Nueva seccion `backup` anadida en arranque si no existe |

---

## Arquitectura de capas

```
scripts/backup.py  ──┐
                     ├──> src/backup.py ──> MariaDB (mysqldump) + filesystem + backup_logs
FastAPI (main.py)  ──┘     (POST /run)
FastAPI (main.py) ────────> backup_logs (GET /status)
```

- `src/backup.py`: modulo con la funcion `run_backup()`. No depende de FastAPI.
  Usa `subprocess` para `mysqldump`, `gzip` para compresion, `zlib` para CRC32.
  Se conecta a la BD via `src.database` para escribir en `backup_logs`.
- `scripts/backup.py`: wrapper minimo que importa y llama `run_backup()`.
  Diseñado para ser ejecutado por cron.
- `src/main.py`: endpoints `GET /api/backup/status` (consulta `backup_logs`) y
  `POST /api/backup/run` (dispara `run_backup()` en background).
- `src/config.py`: dataclass `BackupConfig`, lectura/escritura de seccion
  `backup` en `config.yaml`.

---

## Configuracion de backup: `src/config.py`

### Dataclass nuevo

```python
@dataclass(frozen=True)
class BackupConfig:
    usb_mount_path: str
    local_dir: str
    keep_days: int

DEFAULT_BACKUP_USB_MOUNT_PATH = "/mnt/backup_usb"
DEFAULT_BACKUP_LOCAL_DIR = "/home/bkmngr/backups"
DEFAULT_BACKUP_KEEP_DAYS = 30
```

### Funcion `load_config` modificada

Firma actual: `load_config(path) -> tuple[SystemConfig, SessionConfig, ScaleConfig]`

Nueva firma: `load_config(path) -> tuple[SystemConfig, SessionConfig, ScaleConfig, BackupConfig]`

Esto rompe compatibilidad hacia atras. Los callers actuales (`lifespan` en
`main.py`) DEBEN adaptarse para recibir el cuarto elemento.

Lectura de la seccion `backup`:

```python
if "backup" in data and data["backup"] is not None:
    backup_config = BackupConfig(
        usb_mount_path=data["backup"].get("usb_mount_path", DEFAULT_BACKUP_USB_MOUNT_PATH),
        local_dir=data["backup"].get("local_dir", DEFAULT_BACKUP_LOCAL_DIR),
        keep_days=data["backup"].get("keep_days", DEFAULT_BACKUP_KEEP_DAYS),
    )
else:
    backup_config = BackupConfig(
        DEFAULT_BACKUP_USB_MOUNT_PATH, DEFAULT_BACKUP_LOCAL_DIR, DEFAULT_BACKUP_KEEP_DAYS
    )
```

### Validacion de keep_days

Si `keep_days <= 0` en el YAML cargado, se usa el default y se emite un warning
via logger.

### Formato `config.yaml` extendido

```yaml
rs485:
  path: /dev/ttyACM0
  baudrate: 115200
  parity: N
  data_bits: 8
  stop_bits: 1.0
rs232:
  path: /dev/ttyACM1
  baudrate: 115200
  parity: N
  data_bits: 8
  stop_bits: 1.0
gsm:
  modem_index: 0
session:
  session_timeout_minutes: 15
scale:
  timeout_seconds: 3
last_updated: "2026-06-14T16:00:00"
backup:
  usb_mount_path: /mnt/backup_usb
  local_dir: /home/bkmngr/backups
  keep_days: 30
```

---

## Modelo de datos: `src/models.py`

### Clase nueva: `BackupLog`

```python
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
```

Nota: `BigInteger().with_variant(Integer, "sqlite")` sigue el patron establecido
en `User`, `Hacienda`, `Suerte`, `Weighing` para compatibilidad con SQLite en tests.

---

## Logica de backup: `src/backup.py`

### Constantes y funciones

```python
import gzip
import logging
import os
import subprocess
import tempfile
import zlib
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

BACKUP_FILENAME_FORMAT = "backup_%Y%m%d_%H%M%S.sql.gz"
```

### Funciones principales

```python
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
                    name,
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = proc.communicate(input=password.encode())
            if proc.returncode != 0:
                raise RuntimeError(f"mysqldump failed (exit={proc.returncode}): {stderr.decode().strip()}")
            f_gz.write(stdout)


def _rotate_backups(local_dir: str, keep_days: int) -> None:
    """Elimina los archivos .sql.gz mas antiguos hasta no exceder keep_days."""
    files = sorted(
        [
            f for f in os.listdir(local_dir)
            if f.endswith(".sql.gz") and os.path.isfile(os.path.join(local_dir, f))
        ],
        key=lambda f: os.path.getmtime(os.path.join(local_dir, f)),
    )
    while len(files) > keep_days:
        os.unlink(os.path.join(local_dir, files.pop(0)))
        logger.info("Rotated old backup: %s", files[0])


def run_backup(usb_mount_path: str, local_dir: str, keep_days: int) -> None:
    """Ejecuta el ciclo completo de backup: dump, rotacion, copia USB y registro en DB.
    Crea su propia sesion de BD para insertar el BackupLog."""
    from src.database import SessionLocal
    from src.models import BackupLog

    os.makedirs(local_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime(BACKUP_FILENAME_FORMAT)
    filename = f"backup_{timestamp}.sql.gz"
    local_path = os.path.join(local_dir, filename)

    error_message = None
    local_checksum = None
    file_size = 0
    usb_copied = False
    usb_checksum = None

    try:
        # Fase 1: mysqldump + gzip
        _mysqldump_to_file(local_path)
        file_size = os.path.getsize(local_path)
        local_checksum = _compute_crc32(local_path)
        logger.info("Backup created: %s (%d bytes, crc32=%s)", filename, file_size, local_checksum)

        # Fase 2: rotacion
        _rotate_backups(local_dir, keep_days)

        # Fase 3: copia a USB
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

    # Fase 4: registrar en backup_logs
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
```

### Nota sobre seguridad de mysqldump

Se usa `mysqldump --user=<u> --host=<h> --port=<p> <db>` con stdin para la
contrasena. Esto evita que la contrasena aparezca en `ps aux` o en
`/proc/<pid>/cmdline`, cumpliendo R24.

Alternativa: `--defaults-extra-file=<(echo ...)` crea un archivo temporal con
las credenciales. Descartado por complejidad innecesaria para este caso.

---

## Script standalone: `scripts/backup.py`

```python
"""Script standalone de backup para ejecucion via cron.
Uso: python scripts/backup.py"""

import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

config_path = os.environ.get("CONFIG_PATH", "config.yaml")

from src.database import init_db
init_db()

from src.config import load_config
_, _, _, backup_config = load_config(config_path)

from src.backup import run_backup
run_backup(backup_config.usb_mount_path, backup_config.local_dir, backup_config.keep_days)
```

- Lee `CONFIG_PATH` de variable de entorno con fallback `config.yaml`.
- Inicializa la conexion a BD via `init_db()`.
- Carga configuracion y ejecuta `run_backup()`.
- Si `run_backup()` lanza, el script termina con exit != 0.
- El logging va a stdout (capturable por cron).

### Configuracion de cron (EdgeBox)

```cron
55 23 * * * cd /home/sipedge/sip_edge && python scripts/backup.py >> /var/log/sip_edge_backup.log 2>&1
```

Ejecutado como usuario `sipedge`, que tiene acceso al `.env` con las variables
de entorno. Si se usa un usuario `bkmngr` dedicado, las variables de entorno
deben definirse en su crontab o en un archivo `.env` accesible.

---

## Endpoints en `src/main.py`

### Router `backup_router`

Para mantener `main.py` manejable, los endpoints de backup se definen en un
router APIRouter dentro del propio `src/main.py` (siguiendo el patron de
`users_router`, `haciendas_router`, etc.).

```python
from fastapi import APIRouter, BackgroundTasks, Depends

backup_router = APIRouter(prefix="/api/backup", tags=["backup"])

@backup_router.get("/status")
async def get_backup_status(
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    logs = (
        db.query(BackupLog)
        .order_by(BackupLog.created_at.desc())
        .limit(10)
        .all()
    )
    return [
        {
            "id": log.id,
            "filename": log.filename,
            "file_size": log.file_size,
            "local_checksum": log.local_checksum,
            "usb_copied": log.usb_copied,
            "usb_checksum": log.usb_checksum,
            "error_message": log.error_message,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]

def _run_backup_background():
    """Wrapper para ejecutar backup en background thread."""
    from src.backup import run_backup
    config: BackupConfig = app.state.backup_config
    run_backup(config.usb_mount_path, config.local_dir, config.keep_days)

@backup_router.post("/run")
async def run_backup_endpoint(
    background_tasks: BackgroundTasks,
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_role("admin")),
):
    background_tasks.add_task(_run_backup_background)
    return {"status": "accepted", "message": "Backup started"}
```

El router se incluye con `app.include_router(backup_router)`.

### Lifespan modificado

```python
app.state.config, app.state.session, app.state.scale_config, app.state.backup_config = load_config(CONFIG_PATH)
```

---

## Persistencia

### Tabla nueva: `backup_logs`

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK |
| filename | VARCHAR(255) | NO | | Nombre del archivo de backup |
| file_size | BIGINT | NO | | Tamano en bytes |
| local_checksum | VARCHAR(8) | NO | | CRC32 hex del archivo local |
| usb_copied | BOOLEAN | NO | FALSE | 1 si se copio al USB exitosamente |
| usb_checksum | VARCHAR(8) | YES | NULL | CRC32 hex del archivo en USB |
| error_message | TEXT | YES | NULL | Mensaje de error si fallo |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | Momento del registro |

Sin indices adicionales. El indice `PRIMARY KEY` en `id` es el default.

### Migraciones

No se usa sistema de migraciones (Alembic). La tabla se crea via
`Base.metadata.create_all()` en cada arranque.

---

## Excepciones

| Excepcion | Contexto |
|-----------|----------|
| `RuntimeError` | `mysqldump` falla. Capturada en `run_backup()` y registrada en `backup_logs.error_message` |
| `sqlalchemy.exc.SQLAlchemyError` | Error al insertar en `backup_logs`. Capturado con rollback |
| `OSError` / `IOError` | Error de escritura en disco local o USB. Capturado en `run_backup()` |
| `HTTPException` (FastAPI) | Usada por dependencias de auth para devolver 401/403 |

---

## Alternativas descartadas

### Alternativa 1: Backup programatico con SQLAlchemy (sin mysqldump)

**Descartada porque:** Generar un `.sql` valido via SQLAlchemy (iterando tablas,
generando INSERTs) es propenso a errores y produce archivos no compatibles con
`mysql < dump.sql`. `mysqldump` es la herramienta estandar, probada, y ya esta
disponible en el contenedor MariaDB y en la EdgeBox.

### Alternativa 2: Rotacion por fecha en el nombre en lugar de st_mtime

**Descartada porque:** `st_mtime` refleja el momento real de creacion en disco,
mientras que el nombre de archivo puede ser manipulado. `st_mtime` es mas fiable
para determinar antiguedad real. Ademas, si por alguna razon se copian archivos
antiguos al directorio, `st_mtime` preserva su antiguedad original.

### Alternativa 3: SHA256 en lugar de CRC32 para verificacion

**Descartada porque:** CRC32 es suficiente para detectar corrupcion por copia en
USB (el caso de uso real). SHA256 anade carga computacional innecesaria en un
dispositivo embebido (CM4). Si se requiere integridad criptografica en el
futuro, se puede anadir como feature separada.

### Alternativa 4: Servicio background dentro de FastAPI en lugar de script + cron

**Descartada porque:** La discusion con el humano determino que un script + cron
es preferible: sobrevive a reinicios de la app, no consume recursos del event
loop, y es mas simple de mantener. El endpoint `POST /api/backup/run` existe como
conveniencia para backups manuales, no como mecanismo primario.

### Alternativa 5: Pasar password de mysqldump como argumento (--password=X)

**Descartada porque:** En Linux, los argumentos de linea de comandos son visibles
en `/proc/<pid>/cmdline` para cualquier usuario del sistema. Usar stdin evita
esta exposicion.

---

## Tests

### `tests/test_backup.py`

Usa `tempfile.TemporaryDirectory()` para simular `local_dir` y `usb_mount_path`.
Para `mysqldump`, se usa `unittest.mock.patch` sobre `subprocess.Popen` para
simular salida exitosa y fallida sin necesidad de MariaDB real.

Clases de test:

- `TestBackupConfig`: carga de seccion `backup` desde YAML, fallback a defaults,
  validacion de `keep_days <= 0`.

- `TestMysqldumpToFile`: ejecucion exitosa de `mysqldump` (mock), fallo de
  `mysqldump` lanza `RuntimeError`, creacion de directorio si no existe.

- `TestRotateBackups`: elimina el mas antiguo al exceder `keep_days`, no afecta
  archivos sin extension `.sql.gz`, no elimina si hay exactamente `keep_days`
  archivos.

- `TestComputeCRC32`: calcula CRC32 consistente para mismo contenido, CRC32
  diferente para contenido diferente.

- `TestRunBackup`: ciclo completo exitoso (dump + rotate + USB copy + log en BD),
  fallo de `mysqldump` registra error en `backup_logs`, USB no montado no
  interrumpe el backup, CRC32 mismatch en USB registra error.

- `TestBackupEndpoints`: `GET /api/backup/status` con admin devuelve 200,
  `POST /api/backup/run` con admin devuelve 202, ambos retornan 401 sin token,
  ambos retornan 403 con token operator.

Se usa `Base.metadata.create_all(bind=engine)` con SQLite en memoria para la
tabla `backup_logs` en tests.

---

## `github_labels`

No se requieren etiquetas adicionales.
