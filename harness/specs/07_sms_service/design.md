# Design — Servicio de Notificaciones y Reportes SMS

> Feature 7 — sms_service  
> Dependencies: 1 (system_config), 6 (weighing_capture)

---

## Arquitectura

### SMSService — Estrategia dual Dev/Prod

Se introduce una clase `SMSService` en un nuevo módulo `src/sms_service.py`.
El modo de operación se selecciona mediante la variable de entorno `DEV_MODE`
(leída en el lifespan de la aplicación).

- **DEV_MODE=false (producción):** Ejecuta `mmcli` vía `subprocess.run()` para
  crear y enviar SMS a través del módem Quectel EC25 gestionado por
  ModemManager.
- **DEV_MODE=true (desarrollo):** Simula el envío escribiendo en log con
  `logger.info()`. No se ejecuta `mmcli`, no se requiere módem GSM.

### Planificador de reportes

Se implementa un planificador basado en `asyncio` (sin dependencias externas).
Una corutina en segundo plano, lanzada con `asyncio.create_task()` durante el
lifespan, verifica cada 30 segundos si la hora actual coincide con alguno de
los horarios configurados en `sms.scheduled_reports`. Para evitar duplicados,
lleva un registro interno (`set`) de los horarios ya enviados en el día
actual; el set se resetea cada día a las 00:00.

### Flujo de alerta de seguridad

```
POST /api/auth/login → login fallido → incrementar failed_login_attempts
                                    → ¿>= 3? → SMSService.send_alert_to_admins()
                                            → resetear failed_login_attempts = 0
login exitoso → resetear failed_login_attempts = 0
```

---

## Archivos a crear

| Archivo | Propósito |
|---------|-----------|
| `src/sms_service.py` | Clase SMSService, excepción SMSDeliveryError, lógica de envío dual y planificador |
| `tests/test_sms_service.py` | Tests unitarios del SMSService |

---

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `src/models.py` | Añadir columna `failed_login_attempts` a `User` |
| `src/config.py` | Añadir dataclass `SmsConfig`, extender `load_config()` para parsear sección `sms`, función `save_sms_config()`, cargar defaults en `_atomic_write_sections` |
| `src/main.py` | Modificar `POST /api/auth/login` para contador + alerta; inicializar SMSService y planificador en lifespan; almacenar en `app.state.sms_service` y `app.state.sms_config` |
| `tests/test_auth.py` | Añadir tests para el contador de intentos fallidos y alerta SMS |

---

## Firmas nuevas

### `src/config.py`

```python
@dataclass(frozen=True)
class SmsConfig:
    admin_phones: list[str]
    scheduled_reports: list[str]  # formato "HH:MM"


def load_config(path: str) -> tuple[SystemConfig, SessionConfig, ScaleConfig, BackupConfig, SmsConfig]:
    # ... existing logic ... también parsea sección "sms"
    # Devuelve el tuple con 5 elementos


def save_sms_config(config: SmsConfig, path: str) -> None:
    """Escribe solo la sección sms en config.yaml de forma atómica."""
```

### `src/sms_service.py`

```python
class SMSDeliveryError(Exception):
    """Se lanza cuando mmcli falla al enviar un SMS."""
    pass


class SMSService:
    def __init__(self, config: SmsConfig, modem_index: int, dev_mode: bool) -> None:
        ...

    def send_sms(self, phone: str, message: str) -> bool:
        """Envía un SMS. En dev mode simula con log. En prod ejecuta mmcli.
        Returns True si éxito, False si fallo (loggea error internamente)."""

    def send_alert_to_admins(self, message: str) -> None:
        """Envía un mensaje a todos los números en admin_phones."""

    def send_scheduled_report(self, report_text: str) -> None:
        """Envía un reporte a todos los números en admin_phones."""

    def generate_turn_report(self, db: Session, turn_start: str, turn_end: str) -> str:
        """Genera el texto del reporte de turno consultando la BD."""

    def start_scheduler(self) -> None:
        """Lanza la corutina asyncio del planificador."""

    def stop_scheduler(self) -> None:
        """Cancela la corutina del planificador."""
```

### `src/models.py` — modificación en `User`

```python
# Nueva columna
failed_login_attempts = Column(
    Integer, nullable=False, default=0, server_default="0"
)
```

### `src/main.py` — modificación en login

```python
@app.post("/api/auth/login")
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if user.role == "corresponsal":
        raise HTTPException(status_code=403, detail="Corresponsal role does not permit system login")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not verify_password(body.password, user.password_hash):
        # --- Nuevo: contador de intentos fallidos ---
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        db.commit()
        if user.failed_login_attempts >= 3:
            sms_service: SMSService = app.state.sms_service
            alert_msg = (
                f"Alerta de seguridad: El usuario '{user.username}' "
                f"ha acumulado {user.failed_login_attempts} intentos fallidos "
                f"de inicio de sesion."
            )
            sms_service.send_alert_to_admins(alert_msg)
            user.failed_login_attempts = 0
            db.commit()
        raise HTTPException(status_code=401, detail="Invalid username or password")
    # --- Login exitoso: resetear contador ---
    if user.failed_login_attempts != 0:
        user.failed_login_attempts = 0
        db.commit()
    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token, token_type="bearer", role=user.role)
```

---

## Excepciones

| Excepción | Módulo | Cuándo se lanza |
|-----------|--------|-----------------|
| `SMSDeliveryError` | `src/sms_service.py` | Cuando `mmcli --send` falla con código de retorno distinto de 0, o el subprocess lanza una excepción |

---

## Persistencia

### Tabla modificada: `users`

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `failed_login_attempts` | INTEGER | NO | 0 | Contador de intentos fallidos consecutivos |

No se requieren nuevas tablas, índices ni FK.

### Migraciones

1. `database/migrations/2026_06_15_000001_add_failed_login_attempts_to_users.sql`

```sql
ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0;
```

Para entornos nuevos (tests, primer deploy): `Base.metadata.create_all()` ya
incluye la nueva columna porque el modelo se define con `Column(Integer,
nullable=False, default=0, server_default="0")`. La migración SQL es solo
para producción donde la tabla `users` ya existe.

---

## Configuración en config.yaml

Sección nueva que se añade al archivo (se escribe automáticamente vía
`_atomic_write_sections` si no existe):

```yaml
sms:
  admin_phones: []
  scheduled_reports:
    - "06:00"
    - "14:00"
    - "22:00"
```

---

## Alternativas descartadas

### 1. API HTTP externa (Twilio, AWS SNS)

**Descartada porque:**
- La EdgeBox no tiene conectividad a Internet garantizada (el plan de datos 4G
  está pendiente de activación).
- Dependencia externa que introduce latencia, coste recurrente y punto de fallo
  adicional.
- El módem Quectel EC25 ya está instalado y operativo vía ModemManager,
  haciendo redundante un servicio externo.

### 2. Comandos AT directos al puerto serie del módem

**Descartada porque:**
- ModemManager es el gestor oficial del módem en el EdgeBox. Acceder al puerto
  serie (`/dev/ttyUSB2` o `/dev/ttyUSB3`) directamente mientras ModemManager
  lo gestiona puede causar conflictos de acceso concurrente, corrupción de
  estado del módem y comportamiento impredecible.
- ModemManager ya expone una API estable y probada vía `mmcli` para el envío
  de SMS.
- El script `/usr/local/bin/send_sms.sh` ya existe en el EdgeBox y usa `mmcli`,
  validando el enfoque.

### 3. Uso de APScheduler como planificador

**Descartada porque:**
- La regla de arquitectura «Sin dependencias externas» (architecture.md §2) no
  permite añadir APScheduler sin discusión.
- Un planificador basado en `asyncio.create_task()` + verificación periódica
  es suficiente para esta funcionalidad: solo 3 horarios fijos por día, sin
  necesidad de cron jobs complejos.
- Se evita una dependencia extra que debería instalarse en el EdgeBox.

---

## github_labels

`sms`, `gsm`, `modemmanager`, `security-alert`, `notification`, `scheduler`
