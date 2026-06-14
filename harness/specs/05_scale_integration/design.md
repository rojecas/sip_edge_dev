# Design — Integracion Serial con Bascula DINI ARGEO DFWLI-2

## Archivos nuevos

| Archivo | Proposito |
|---------|-----------|
| `src/scale.py` | `ScaleService` singleton, `ScaleConnectionError`, `ScaleTimeoutError`, `ScaleProtocolError`, parsing de respuesta extendida/corta |
| `tests/test_scale.py` | Tests unitarios con mock de serial port |

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/config.py` | Anadir dataclass `ScaleConfig`; modificar `load_config` para retornar `tuple[SystemConfig, SessionConfig, ScaleConfig]`; anadir `save_scale_config`; actualizar `default_config` si aplica; anadir `DEFAULT_SCALE_TIMEOUT` |
| `src/main.py` | Inicializar `ScaleService` singleton en lifespan; registrar endpoint `PUT /api/setup/scale` (admin-only) |

## ScaleConfig

Nuevo dataclass en `src/config.py`:

```python
DEFAULT_SCALE_TIMEOUT = 3

@dataclass(frozen=True)
class ScaleConfig:
    timeout_seconds: int
```

Seccion en `config.yaml`:
```yaml
scale:
  timeout_seconds: 3
```

### Cambios en `load_config`

- Firma cambia de `load_config(path: str) -> tuple[SystemConfig, SessionConfig]` a
  `load_config(path: str) -> tuple[SystemConfig, SessionConfig, ScaleConfig]`
- Se anade logica de lectura de `data["scale"]["timeout_seconds"]` con validacion
  1–10 y default 3.

### Funcion nueva: `save_scale_config`

```python
def save_scale_config(config: ScaleConfig, path: str) -> None
```

Mismo patron que `_save_session_config_atomic`: carga YAML existente,
actualiza `existing["scale"]`, escribe atomicamente.

## ScaleService

Singleton en `src/scale.py`. NO es un dataclass (maneja estado mutable: serial
connection, hilo, cola).

```python
import queue
import threading
import serial

class ScaleConnectionError(Exception):
    """No se puede abrir/cerrar el puerto serial."""

class ScaleTimeoutError(Exception):
    """No se recibio respuesta dentro del timeout."""

class ScaleProtocolError(Exception):
    """Respuesta inesperada o mal formada desde la balanza."""


class ScaleService:
    def __init__(self, config: ScaleConfig, serial_config: SerialPortConfig):
        ...

    def start(self) -> None:
        """Abre puerto serial e inicia hilo async listener."""

    def stop(self) -> None:
        """Detiene hilo async y cierra puerto serial."""

    def send_command(self, command: str, value: str = None) -> dict:
        """Envia comando, espera respuesta, devuelve dict parseado.
        Commands: REXT, TARE, TMAN, ZERO, CLEAR.
        Lanza ScaleTimeoutError si timeout.
        Lanza ScaleProtocolError si respuesta no reconocible.
        Hilo-safe mediante threading.Lock para escritura.
        """

    def async_listener(self, callback) -> None:
        """Registra callback para datos espontaneos (boton PRINT).
        El hilo en background lee del serial y pone en queue;
        un worker thread saca de queue e invoca callback.
        """
```

### Response parsing

```python
def parse_extended_response(line: str) -> dict:
    """Parsea: 01ST,1, 0.0,PT 20.8, 0,kg\r\n
    Retorna: {address, status_code, is_stable, net_weight,
              tare_indicator, tare_weight, piece_count, unit}
    """

def parse_short_response(line: str) -> dict:
    """Parsea: 01ST,GS, 0.0,kg\r\n
    Retorna: {address, status_code, is_stable, weight, unit}
    """
```

`is_stable` es `True` si `status_code == "ST"`, `False` en cualquier otro
caso (US, OL, UL, TL).

### Serial connection (from user prompt)

- Address: "00"
- Port: from `SystemConfig.rs485.path` (`/dev/ttyACM0`)
- Baudrate: from `SystemConfig.rs485.baudrate` (115200)
- Config: 8N1 (8 data bits, no parity, 1 stop bit)
- These come from `SystemConfig.rs485`, already in config.yaml

### Hilo async listener

- `start()` crea un thread daemon que continuamente lee lineas del serial
  hasta que `stop()` es llamado.
- Las lineas entrantes se ponen en una `queue.Queue`.
- Un segundo thread (o el mismo) desencola e invoca el callback registrado
  via `async_listener(callback)`.

## Endpoint

### `PUT /api/setup/scale`

```python
class ScaleTimeoutRequest(BaseModel):
    timeout_seconds: int = Field(ge=1, le=10)

@app.put("/api/setup/scale")
async def put_scale_config(
    body: ScaleTimeoutRequest,
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_role("admin")),
):
    config = ScaleConfig(timeout_seconds=body.timeout_seconds)
    save_scale_config(config, CONFIG_PATH)
    app.state.scale_config = config
    if hasattr(app.state, "scale_service") and app.state.scale_service is not None:
        app.state.scale_service.update_timeout(config.timeout_seconds)
    return {"timeout_seconds": config.timeout_seconds}
```

## Inicializacion (lifespan en `src/main.py`)

```python
from src.scale import ScaleService

@asynccontextmanager
async def lifespan(app: FastAPI):
    config, session, scale_cfg = load_config(CONFIG_PATH)
    app.state.config = config
    app.state.session = session
    app.state.scale_config = scale_cfg
    app.state.scale_service = ScaleService(scale_cfg, config.rs485)
    app.state.scale_service.start()
    init_db()
    ...
    yield
    app.state.scale_service.stop()
```

## Persistencia

Esta feature NO toca la base de datos. Solo modifica `config.yaml`.

## Alternativa descartada

**Protocolo asincrono puro con asyncio.** Se descarto porque `pyserial`
no es compatible con `asyncio` de forma nativa sin librerias extra
(`pyserial-asyncio`). La especificacion exige solo stdlib + pyserial.
Usar threading + queue es el patron estandar para serial I/O en Python
sin dependencias adicionales.

## GitHub labels

`scale`, `serial`, `rs485`, `dini-argeo`, `dfwli-2`, `hardware-integration`
