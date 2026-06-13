# Design — system_config

> Feature: Configuración del Sistema y Persistencia
> Date: 13-Jun-2026

---

## Decisiones Técnicas

### Estructura de archivos

```
src/
  config.py               # Modelos Pydantic para config.yaml
  config_service.py       # Carga, validación, guardado atómico
  routers/
    __init__.py
    config.py             # Endpoints FastAPI /api/config
  main.py                 # Modificar: incluir router y lifespan loader
  dependencies.py         # Dep. FastAPI: get_config, require_admin
config.yaml               # Archivo de configuración (creado en runtime)

templates/
  admin/
    config.html           # Página Admin de configuración (HTML5 + HTMX)
    config_form.html      # Partial HTMX: formulario de configuración hardware
    config_sms.html       # Partial HTMX: destinatarios y horarios SMS

tests/
  test_config.py          # Tests de modelos Pydantic
  test_config_service.py  # Tests de carga/guardado/validación
  test_config_api.py      # Tests de endpoints
```

### config.yaml — Estructura

```yaml
scale:
  port: /dev/ttyUSB0
  baudrate: 9600
  parity: N
  data_bits: 8
  stop_bits: 1
  timeout_ms: 1500

gsm:
  port: /dev/ttyUSB1
  baudrate: 115200
  timeout_ms: 3000

reports:
  schedule: ["06:00", "14:00", "22:00"]
  recipients:
    - "+57XXXXXXXXX"
    - "+57YYYYYYYYY"
```

### Modelos Pydantic (`src/config.py`)

```python
class ScaleConfig(BaseModel):
    port: str = "/dev/ttyUSB0"
    baudrate: int = Field(default=9600, ge=300, le=115200)
    parity: Literal["N", "E", "O"] = "N"
    data_bits: Literal[7, 8] = 8
    stop_bits: Literal[1, 2] = 1
    timeout_ms: int = Field(default=1500, ge=500, le=3000)

class GSMConfig(BaseModel):
    port: str = "/dev/ttyUSB1"
    baudrate: int = Field(default=115200, ge=300, le=115200)
    timeout_ms: int = Field(default=3000, ge=500, le=5000)

class ReportsConfig(BaseModel):
    schedule: list[str] = Field(default=["06:00", "14:00", "22:00"])
    recipients: list[str] = Field(default=[])

class SystemConfig(BaseModel):
    scale: ScaleConfig = ScaleConfig()
    gsm: GSMConfig = GSMConfig()
    reports: ReportsConfig = ReportsConfig()
```

Validación adicional: `schedule` ítems validados con regex `^([01]\d|2[0-3]):[0-5]\d$`.
Validación adicional: `recipients` ítems validados con regex `^\+\d{7,15}$`.

### ConfigService (`src/config_service.py`)

Clase singleton `ConfigService`:

- `load() -> SystemConfig`: Lee `config.yaml`. Si no existe, crea con defaults.
- `save(config: SystemConfig)`: Valida y escribe atómicamente.
- `get_config() -> SystemConfig`: Devuelve instancia en memoria (cargada en startup).

Singleton accedido vía `Depends(get_config_service)` en FastAPI.

Atomicidad: `save()` escribe a `config.yaml.tmp` y luego `os.replace()`.

### Endpoints FastAPI (`src/routers/config.py`)

| Método | Ruta                       | Auth | Descripción                 |
|--------|----------------------------|------|-----------------------------|
| GET    | `/admin/config`            | Admin| Página HTML de configuración|
| GET    | `/api/config`              | Admin| Obtener config actual (JSON)|
| PUT    | `/api/config`              | Admin| Guardar config completa     |
| POST   | `/api/config/test-scale`   | Admin| Probar conexión báscula     |
| POST   | `/api/config/test-gsm`     | Admin| Probar conexión módem GSM   |

### Frontend (HTMX)

- `config.html`: Layout Admin con navegación. Incluye tabs/secciones para Hardware
  y SMS. Cada sección carga su partial.
- `config_form.html`: Formulario con campos de báscula + GSM. Botones "Test Báscula"
  y "Test GSM" disparan `hx-post` a los endpoints de prueba. Botón "Guardar" dispara
  `hx-put` a `/api/config`. Errores de validación se muestran inline vía HTMX sin
  recargar la página.
- `config_sms.html`: Lista de destinatarios SMS + horarios. Permite añadir/quitar
  números y horarios.

Feedback visual: Verde (éxito), Rojo (error), Amarillo (procesando) según RNF del ERS.

### Test de conectividad

- **Báscula**: Abrir puerto serial con `pyserial` (no incluido en requirements aún,
  se añade en esta feature). Enviar comando configurable. Timeout del config.
  Manejar `SerialException`, `OSError`. El resultado es JSON `{success, message, data?}`.
- **GSM**: Abrir puerto serial, enviar `AT\r\n`, esperar `OK`. Manejar timeouts.
  Resultado similar en JSON.

> **Nota sobre pyserial**: Se requiere `pyserial==3.5` como dependencia nueva.
> Se añade a `requirements.txt` en esta feature.

### Alternativa descartada: SQLite/DB para config

Se consideró guardar la configuración en MariaDB en lugar de `config.yaml`.
Se descartó porque:
- La config DEBE estar disponible antes de que la BD esté lista (startup).
- `config.yaml` es legible y editable manualmente en emergencia.
- No requiere migraciones para cambios de esquema de configuración.

### Lifespan de FastAPI (`src/main.py`)

Se añade un `@asynccontextmanager` en el lifespan de FastAPI que:
1. Instancia `ConfigService` y carga `config.yaml`.
2. Sincroniza reloj vía `subprocess.run(["timedatectl", "set-ntp", "true"])`.
3. Almacena el servicio en `app.state.config_service`.

### Dependencias (`src/dependencies.py`)

```python
def get_config_service(request: Request) -> ConfigService:
    return request.app.state.config_service

def require_admin(...) -> User:  # Placeholder hasta feature auth_rbac
    pass  # En esta feature, todas las rutas Admin son abiertas
```

La protección real (R12) se implementa completamente en la feature `auth_rbac`.
En esta feature se deja el endpoint con anotación `# TODO: require_admin` y un
guard básico que loguea el acceso.

### github_labels

`config, admin, frontend`
