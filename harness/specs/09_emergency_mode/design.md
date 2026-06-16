# Design — Modo Manual de Emergencia

> Feature 9 — emergency_mode  
> Dependencies: 2 (auth_rbac), 3 (user_management), 7 (sms_service)

---

## Arquitectura

### Visión general

El modo manual de emergencia se implementa como un nuevo módulo
`src/emergency_mode.py` que orquesta:

1. **API endpoints REST** — para que el kiosco (frontend) liste admins, cree
   solicitudes y consulte el estado del modo manual.
2. **Parsing de SMS entrantes** — una función pura que interpreta comandos SMS
   (`manual on`, `manual on Xh`, `manual off`, etc.) de forma case-insensitive.
3. **Polling de SMS entrantes vía ModemManager** — tarea asyncio en segundo
   plano que revisa periódicamente la bandeja de entrada del módem GSM usando
   `mmcli`.
4. **Core service** — lógica de activación/desactivación/extensión con
   persistencia en `emergency_mode_log`.
5. **Expiry checker** — tarea asyncio que cada 30 segundos verifica si el modo
   activo ha expirado y lo desactiva automáticamente.

### Flujo de datos

```
Kiosco UI → POST /api/emergency/request → EmergencyModeService → SMSService.send_sms()
                                                                       ↓
                                                              Admin recibe SMS
                                                                       ↓
                                                              Admin responde SMS
                                                                       ↓
SMS inbox polling (mmcli) → parse_emergency_sms() → EmergencyModeService.activate()
                                                              ↓
                                                     emergency_mode_log (BD)
                                                              ↓
                                              Frontend consulta GET /api/emergency/status
                                                              ↓
                                              Campo peso editable mientras active=true
```

---

## Archivos a crear

| Archivo | Propósito |
|---------|-----------|
| `src/emergency_mode.py` | Lógica completa: modelo, parser SMS, servicio, router de endpoints |
| `tests/test_emergency_mode.py` | Tests unitarios y de integración |

---

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `src/models.py` | Añadir modelo ORM `EmergencyModeLog` mapeado a tabla `emergency_mode_log` |
| `src/main.py` | Importar e incluir `emergency_router`; inicializar `EmergencyModeService` en lifespan; iniciar/detener tareas de polling y expiry checker |
| `database/migrations/2026_06_16_000001_create_emergency_mode_log.sql` | Crear migración SQL para producción |

---

## Firmas nuevas

### `src/emergency_mode.py`

#### SMS Parser

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ParsedSmsCommand:
    """Resultado del parsing de un SMS de emergencia."""

    action: str  # "activate", "extend", "deactivate", "invalid", "unauthorized"
    duration_minutes: int | None = None  # None para "manual off" e "invalid"
    raw_text: str = ""


def parse_emergency_sms(text: str) -> ParsedSmsCommand:
    """Analiza el texto de un SMS y determina el comando.

    Patrones soportados (case-insensitive):
      - "manual on"                    → activate, 1440 min (24h)
      - "manual on <N>h"               → activate, N*60 min
      - "manual on <N>m"               → activate, N min
      - "manual on ext <N>h"           → extend, N*60 min
      - "manual on ext <N>m"           → extend, N min
      - "manual off"                   → deactivate
      - cualquier otro                 → invalid

    Returns:
        ParsedSmsCommand con action="invalid" si no hay coincidencia.
    """
```

#### Excepciones

```python
class EmergencyModeError(Exception):
    """Error base del módulo de emergencia."""
    pass


class InvalidSmsCommandError(EmergencyModeError):
    """Se lanza cuando un comando SMS no es reconocido."""
    pass


class UnauthorizedSenderError(EmergencyModeError):
    """Se lanza cuando el emisor del SMS no es un admin registrado."""
    pass
```

#### EmergencyModeService

```python
class EmergencyModeService:
    """Servicio central del modo manual de emergencia.

    Gestiona solicitudes, autorizaciones por SMS, estado activo/inactivo,
    persistencia en BD y tareas en segundo plano (polling SMS, expiry).
    """

    def __init__(
        self,
        db_session_factory: callable,
        sms_service,
        modem_index: int = 0,
        dev_mode: bool = False,
    ) -> None:
        """
        Args:
            db_session_factory: Callable que retorna una SQLAlchemy Session.
            sms_service: Instancia de SMSService para enviar SMS.
            modem_index: Índice del módem para mmcli (default 0).
            dev_mode: Si True, simula recepción de SMS sin mmcli.
        """
        self._active: bool = False
        self._expires_at: datetime | None = None
        self._active_record_id: int | None = None
        self._sms_poll_task: asyncio.Task | None = None
        self._expiry_check_task: asyncio.Task | None = None
        # ...

    async def start(self) -> None:
        """Inicia las tareas en segundo plano (polling SMS + expiry checker)."""

    async def stop(self) -> None:
        """Cancela las tareas en segundo plano."""

    # --- Solicitudes desde kiosco ---

    def create_request(
        self, analyst_id: int, supervisor_id: int, motivo: str
    ) -> int:
        """Crea una solicitud en BD y envía SMS al supervisor.

        Args:
            analyst_id: ID del analista que solicita.
            supervisor_id: ID del admin destinatario.
            motivo: Texto obligatorio del motivo.

        Returns:
            request_id (int) de la solicitud creada.

        Raises:
            ValueError: Si supervisor_id no corresponde a un admin activo.
            ValueError: Si motivo está vacío o solo contiene espacios.
        """

    # --- Estado ---

    def is_active(self) -> bool:
        """Retorna True si el modo manual está actualmente activo."""

    def get_status(self) -> dict:
        """Retorna el estado actual del modo manual.

        Returns:
            {
                "active": bool,
                "expires_at": str | None,  # ISO format
                "remaining_seconds": int | None,
                "active_record_id": int | None,
            }
        """

    # --- Activación/desactivación programática ---

    def activate(
        self,
        request_id: int | None,
        supervisor_id: int,
        duration_minutes: int,
        cmd_raw: str,
        cmd_source: str,
    ) -> None:
        """Activa el modo manual.

        Args:
            request_id: ID de solicitud si proviene de una, None si es directa.
            supervisor_id: ID del admin que autoriza.
            duration_minutes: Duración en minutos.
            cmd_raw: Texto crudo del comando que originó la activación.
            cmd_source: "sms" o "ui".

        Raises:
            EmergencyModeError: Si supervisor_id no existe o no es admin.
        """

    def extend(
        self, supervisor_id: int, extra_minutes: int, cmd_raw: str
    ) -> None:
        """Extiende el modo manual activo sumando minutos al expires_at actual.

        Raises:
            EmergencyModeError: Si el modo manual no está activo.
        """

    def deactivate(
        self, supervisor_id: int | None, cmd_raw: str
    ) -> None:
        """Desactiva el modo manual inmediatamente.

        Args:
            supervisor_id: ID del admin (None si es por expiración automática).
            cmd_raw: Texto crudo del comando o "auto_expire".
        """

    def restore_from_db(self) -> None:
        """Restaura el estado del modo manual desde la BD.

        Busca el registro más reciente con status='active' y expires_at futuro,
        y restablece self._active, self._expires_at y self._active_record_id.
        Si expires_at ya expiró, actualiza el registro a status='expired'.
        """

    # --- Procesamiento interno de SMS ---

    def process_incoming_sms(self, sender_phone: str, text: str) -> None:
        """Procesa un SMS entrante: parsea, verifica emisor, ejecuta comando.

        Args:
            sender_phone: Número de teléfono del remitente.
            text: Texto completo del SMS.
        """

    # --- Tareas asyncio ---

    async def _poll_incoming_sms(self) -> None:
        """Tarea asyncio que cada 15 segundos consulta SMS entrantes vía mmcli.

        En DEV_MODE=true no ejecuta mmcli, simula con una cola interna.
        En DEV_MODE=false ejecuta:
          mmcli -m <modem_index> --messaging-list-sms
          mmcli -s <sms_id>
          mmcli -s <sms_id> --delete
        """

    async def _check_expiry_loop(self) -> None:
        """Tarea asyncio que cada 30 segundos verifica expiración."""
```

### `src/models.py` — Modelo nuevo

```python
class EmergencyModeLog(Base):
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
    )
    status = Column(String(20), nullable=False, default="pending")
    analyst_id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.id"),
        nullable=True,
        default=None,
    )
    supervisor_id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.id"),
        nullable=True,
        default=None,
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
```

### `src/main.py` — Modificaciones

#### Lifespan

```python
# --- Al inicio del lifespan ---
from src.emergency_mode import EmergencyModeService

# Cargar config existente...
app.state.emergency_service = EmergencyModeService(
    db_session_factory=SessionLocal,
    sms_service=app.state.sms_service,
    modem_index=app.state.config.gsm.modem_index,
    dev_mode=os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes"),
)
# Restaurar estado desde BD (R14)
app.state.emergency_service.restore_from_db()
# Iniciar tareas de background
await app.state.emergency_service.start()

# --- Al final del lifespan ---
await app.state.emergency_service.stop()
```

#### Router

```python
from src.emergency_mode import router as emergency_router

# Después de los otros include_router
app.include_router(emergency_router)
```

### Endpoints

Definidos en `src/emergency_mode.py` como `emergency_router`:

```python
emergency_router = APIRouter(prefix="/api/emergency", tags=["emergency"])


@emergency_router.get("/admins")
def list_admin_users(
    _: dict = Depends(check_inactivity),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Retorna lista de usuarios con rol admin y is_active=true.
    Cada elemento incluye: id, full_name, document, phone (si existe).

    Accesible por: cualquier rol autenticado.
    """
    users = db.query(User).filter(
        User.role == "admin",
        User.is_active == True,
    ).all()
    return [
        {"id": u.id, "full_name": u.full_name, "document": u.document}
        for u in users
    ]


@emergency_router.post("/request")
def create_emergency_request(
    body: EmergencyRequest,
    _: dict = Depends(check_inactivity),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Crea una solicitud de modo manual.

    Body: { supervisor_id: int, motivo: str }
    El analista actual se obtiene del token JWT.

    Retorna: { request_id: int, message: str }
    """
    svc: EmergencyModeService = app.state.emergency_service
    request_id = svc.create_request(
        analyst_id=current_user.id,
        supervisor_id=body.supervisor_id,
        motivo=body.motivo,
    )
    return {"request_id": request_id, "message": "Solicitud enviada. Esperando autorización por SMS."}


@emergency_router.get("/status")
def get_emergency_status(
    _: dict = Depends(check_inactivity),
) -> dict:
    """Retorna el estado actual del modo manual.

    No requiere rol específico (cualquier usuario autenticado puede consultar).

    Retorna:
    {
        "active": bool,
        "expires_at": str | None,
        "remaining_seconds": int | None,
        "active_record_id": int | None,
    }
    """
    svc: EmergencyModeService = app.state.emergency_service
    return svc.get_status()
```

#### Pydantic models (en `src/emergency_mode.py`)

```python
from pydantic import BaseModel, Field


class EmergencyRequest(BaseModel):
    supervisor_id: int = Field(gt=0)
    motivo: str = Field(min_length=1, strip_whitespace=True)
```

---

## Inbound SMS polling (diseño detallado)

El polling de SMS entrantes se implementa como una corutina asyncio lanzada
en `EmergencyModeService.start()`:

```python
async def _poll_incoming_sms(self) -> None:
    """Cada 15 segundos consulta SMS nuevos via mmcli."""
    while True:
        try:
            if self._dev_mode:
                # En desarrollo: leer de una cola interna in-memory
                # (se alimenta en tests o manualmente)
                pass
            else:
                # 1. Listar SMS en la bandeja de entrada
                result = subprocess.run(
                    ["mmcli", "-m", str(self._modem_index), "--messaging-list-sms"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode != 0:
                    logger.warning("mmcli list-sms failed: %s", result.stderr.strip())
                    await asyncio.sleep(15)
                    continue

                # 2. Extraer IDs de SMS de la salida
                sms_ids = _SMS_ID_RE.findall(result.stdout)
                for sms_id in sms_ids:
                    # 3. Leer cada SMS
                    read = subprocess.run(
                        ["mmcli", "-s", sms_id],
                        capture_output=True, text=True, timeout=10,
                    )
                    if read.returncode != 0:
                        continue
                    # 4. Extraer número y texto
                    sender = _extract_sms_field(read.stdout, "number")
                    text = _extract_sms_field(read.stdout, "text")
                    if sender and text:
                        self.process_incoming_sms(sender, text)
                    # 5. Eliminar el SMS procesado
                    subprocess.run(
                        ["mmcli", "-s", sms_id, "--delete"],
                        capture_output=True, timeout=10,
                    )
        except Exception:
            logger.exception("Error in SMS polling loop")
        await asyncio.sleep(15)
```

Helpers para parsear salida de `mmcli -s <id>`:

```python
_SMS_ID_RE = re.compile(r"/org/freedesktop/ModemManager1/SMS/(\d+)")
_SMS_FIELD_RE = re.compile(r"^\s+(\w+)\s*:\s*(.+)$", re.MULTILINE)


def _extract_sms_field(mmcli_output: str, field: str) -> str | None:
    """Extrae el valor de un campo de la salida de mmcli -s <id>."""
    match = _SMS_FIELD_RE.search(mmcli_output)
    # ... implementación basada en el formato real de mmcli
```

---

## Persistencia

### Tabla nueva: `emergency_mode_log`

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK |
| request_id | BIGINT UNSIGNED | YES | NULL | FK → emergency_mode_log.id (auto-referencia: apunta al registro de solicitud que originó esta acción) |
| status | VARCHAR(20) | NO | 'pending' | Valores: `pending`, `active`, `expired`, `cancelled`, `extended`, `invalid` |
| analyst_id | BIGINT UNSIGNED | YES | NULL | FK → users.id (quién solicita, NULL si activación directa por SMS) |
| supervisor_id | BIGINT UNSIGNED | YES | NULL | FK → users.id (quién autoriza/ejecuta, NULL en expiración automática) |
| motivo | TEXT | YES | NULL | Motivo de la solicitud |
| started_at | DATETIME | YES | NULL | Momento de activación |
| duration_seconds | INT UNSIGNED | YES | NULL | Duración autorizada en segundos |
| expires_at | DATETIME | YES | NULL | started_at + duration |
| cmd_source | VARCHAR(10) | NO | | Valores: `sms`, `ui` |
| cmd_raw | VARCHAR(255) | YES | NULL | Texto crudo del comando SMS, o `"auto_expire"` si expiración, o `"ui_request"` si solicitud desde kiosco |
| created_at | DATETIME | NO | CURRENT_TIMESTAMP | |
| updated_at | DATETIME | YES | NULL | ON UPDATE CURRENT_TIMESTAMP |

**Índices:**
- `(status, expires_at)` — búsqueda rápida de registros activos y expiración
- `(analyst_id)` — consultas por analista
- `(supervisor_id)` — consultas por supervisor
- `(request_id)` — JOIN con auto-referencia

**Foráneas:**
- `request_id` → `emergency_mode_log.id` (auto-referencia)
- `analyst_id` → `users.id`
- `supervisor_id` → `users.id`

### Migraciones

1. `database/migrations/2026_06_16_000001_create_emergency_mode_log.sql`

```sql
CREATE TABLE emergency_mode_log (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    request_id BIGINT UNSIGNED NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    analyst_id BIGINT UNSIGNED NULL,
    supervisor_id BIGINT UNSIGNED NULL,
    motivo TEXT NULL,
    started_at DATETIME NULL,
    duration_seconds INT UNSIGNED NULL,
    expires_at DATETIME NULL,
    cmd_source VARCHAR(10) NOT NULL,
    cmd_raw VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status_expires (status, expires_at),
    INDEX idx_analyst (analyst_id),
    INDEX idx_supervisor (supervisor_id),
    INDEX idx_request (request_id),
    CONSTRAINT fk_emergency_request FOREIGN KEY (request_id) REFERENCES emergency_mode_log(id),
    CONSTRAINT fk_emergency_analyst FOREIGN KEY (analyst_id) REFERENCES users(id),
    CONSTRAINT fk_emergency_supervisor FOREIGN KEY (supervisor_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

Para entornos nuevos (tests, primer deploy): `Base.metadata.create_all()` ya
incluye la nueva tabla porque el modelo se define en `src/models.py`.

---

## Excepciones

| Excepción | Módulo | Cuándo se lanza |
|-----------|--------|-----------------|
| `EmergencyModeError` | `src/emergency_mode.py` | Error base del módulo |
| `InvalidSmsCommandError` | `src/emergency_mode.py` | Comando SMS no reconocido (capturado internamente) |
| `UnauthorizedSenderError` | `src/emergency_mode.py` | Emisor del SMS no es un admin registrado (capturado internamente) |
| `ValueError` | `src/emergency_mode.py` | Motivo vacío, supervisor inválido en `create_request()` |
| `HTTPException` (FastAPI) | `src/emergency_mode.py` | Usado por dependencias de auth (401/403) |

---

## Alternativas descartadas

### Alternativa 1: Webhook / callback HTTP para recepción de SMS

**Descartada porque:** El módem GSM no tiene capacidad de notificar por HTTP
cuando recibe un SMS. La integración con ModemManager es vía D-Bus (accesible
con `mmcli`) o polling. No hay un servicio externo que pueda hacer webhook. El
polling es la única opción viable sin añadir dependencias (como `dbus` bindings
de Python).

### Alternativa 2: Escucha D-Bus con pydbus

**Descartada porque:** Introduciría una dependencia externa (`pydbus` o
`dbus-python`), violando el principio de "Sin dependencias externas"
(architecture.md §2). Además, las bindings de D-Bus para Python pueden no estar
disponibles para aarch64 en Debian Trixie sin compilar desde fuente. El polling
vía `subprocess.run("mmcli", ...)` usa solo stdlib y es suficientemente
eficiente para un intervalo de 15 segundos.

### Alternativa 3: Almacenar el estado activo en un archivo JSON para persistencia

**Descartada porque:** La BD (`emergency_mode_log`) ya es la fuente de verdad
para auditoría. Mantener un archivo JSON adicional para la restauración rápida
introduciría un riesgo de inconsistencia entre el archivo y la BD. Es más
simple y robusto leer el último registro activo desde la BD al iniciar (R14).

### Alternativa 4: Websocket en tiempo real para el estado del modo manual

**Descartada porque:** El frontend puede consultar `GET /api/emergency/status`
con la frecuencia que necesite (ej. cada 5 segundos vía polling del lado del
cliente). Un WebSocket añade complejidad de gestión de conexiones sin un
beneficio claro, dado que el estado cambia como máximo una vez cada 30 segundos
(expiry check).

---

## github_labels

`emergency`, `sms-command`, `manual-mode`, `kiosco`, `audit-log`
