# Design — system_config

> Decisiones tecnicas para la feature de configuracion del sistema.

## Archivos creados / modificados

| Archivo          | Accion    | Proposito                                                |
|-----------------|-----------|----------------------------------------------------------|
| `src/config.py` | **CREAR** | Modelo de dominio: dataclasses congelados + serializacion YAML |
| `src/main.py`   | MODIFICAR | Registrar rutas `/api/config` y `/api/config/test/{port}` |
| `tests/test_config.py` | **CREAR** | Tests unitarios del modelo de dominio y endpoints |
| `config.yaml`   | **CREAR** (runtime) | Archivo de persistencia generado en arranque si no existe |

## Modelo de dominio (`src/config.py`)

### Dataclasses

```python
@dataclass(frozen=True)
class SerialPortConfig:
    path: str
    baudrate: int
    parity: str          # "N", "E", "O", "M", "S"
    data_bits: int       # 5, 6, 7, 8
    stop_bits: float     # 1.0, 1.5, 2.0

@dataclass(frozen=True)
class GsmConfig:
    modem_index: int     # >= 0

@dataclass(frozen=True)
class SystemConfig:
    rs485: SerialPortConfig
    rs232: SerialPortConfig
    gsm: GsmConfig
    last_updated: str    # ISO 8601 timestamp
```

### Constantes de validacion

```python
VALID_BAUDRATES = {300, 600, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200}
VALID_DATA_BITS = {5, 6, 7, 8}
VALID_PARITY = {"N", "E", "O", "M", "S"}
VALID_STOP_BITS = {1.0, 1.5, 2.0}
VALID_TEST_PORTS = {"rs485", "rs232", "gsm"}
```

### Funciones publicas

```python
def load_config(path: str) -> SystemConfig
def save_config(config: SystemConfig, path: str) -> None
def validate_config(config: SystemConfig) -> None   # lanza ValueError
```

- `load_config`: Lee YAML del archivo. Si no existe o es invalido, devuelve
  `default_config()` y registra el error via `logging.warning()`.
- `save_config`: Serializa a YAML, escribe a temp file, `os.replace()`.
- `validate_config`: Comprueba que todos los valores estan en los conjuntos
  validos. Lanza `ValueError` con mensaje descriptivo si alguna validacion falla.

### Dependencias

- `pyyaml` (ya en `requirements.txt` como `pyyaml==6.0.2`)
- `dataclasses`, `datetime`, `logging`, `os`, `tempfile` (stdlib)
- `serial` para tests de conectividad — PERO `serial` NO se usa en el modelo de
  dominio. Se usa SOLO en los endpoints de test dentro de `main.py`. Esto
  requiere anadir `pyserial` a `requirements.txt` o usar el import condicional
  en los tests.

**Decision:** El test de conectividad serial en los endpoints `POST
/api/config/test/rs485` y `POST /api/config/test/rs232` requiere `pyserial`.
Anadimos `pyserial` a `requirements.txt`. Esto es aceptable porque es una
dependencia requerida por el hardware real (EdgeBox-RPI-200) y el proyecto ya
usa dependencias externas. La regla de "sin dependencias externas" de
architecture.md aplica a la logica de dominio pura; la capa de conectividad de
hardware inherentemente requiere `pyserial`.

**GSM test:** El endpoint `POST /api/config/test/gsm` usa `subprocess.run()`
para ejecutar `mmcli -m <modem_index>`. No requiere dependencias adicionales.

### Excepciones

| Excepcion      | Contexto                                      |
|---------------|-----------------------------------------------|
| `ValueError`   | Validacion de campos invalidos (baudrate, parity, etc.) |
| `OSError`      | Fallo al escribir archivo o ejecutar mmcli    |
| `FileNotFoundError` | mmcli no encontrado en el sistema        |

Las excepciones de validacion (`ValueError`) se capturan en los endpoints y se
convierten en respuestas HTTP 422. Los errores de hardware (`OSError`,
`FileNotFoundError`) se capturan en los endpoints de test y se devuelven como
`{"status": "fail", "detail": "..."}` con status 200.

## Endpoints en `src/main.py`

### `GET /api/config`

Devuelve `SystemConfig` serializado a JSON via `dataclasses.asdict()`.

Response 200:
```json
{
  "rs485": {"path": "/dev/ttyACM0", "baudrate": 115200, "parity": "N", "data_bits": 8, "stop_bits": 1.0},
  "rs232": {"path": "/dev/ttyACM1", "baudrate": 115200, "parity": "N", "data_bits": 8, "stop_bits": 1.0},
  "gsm": {"modem_index": 0},
  "last_updated": "2026-06-13T14:30:00"
}
```

### `PUT /api/config`

Acepta body JSON con la misma estructura que el GET (sin `last_updated` — el
sistema lo asigna). Valida via `validate_config()`. Si pasa, persiste con
`save_config()`.

Response 200: configuracion actualizada.
Response 422: `{"detail": "<mensaje de error>"}`

### `POST /api/config/test/{port}`

Donde `port` ∈ {rs485, rs232, gsm}.

- `rs485`/`rs232`: Abre puerto serial con `serial.Serial(...)`, cierra
  inmediatamente. Envuelto en try/except `serial.SerialException`.
- `gsm`: Ejecuta `subprocess.run(["mmcli", "-m", str(modem_index)],
  capture_output=True, timeout=10)`. Si exit_code == 0 => ok.

Response 200:
```json
{"status": "ok"}
```
o
```json
{"status": "fail", "detail": "could not open port /dev/ttyACM0: Permission denied"}
```

Si `port` no es valido → Response 404:
```json
{"detail": "Unknown port 'unknown'. Valid: rs485, rs232, gsm"}
```

## Alternativa descartada

**Alternativa:** Usar Pydantic `BaseModel` con validadores para el modelo de
configuracion en lugar de dataclasses congelados.

**Justificacion del descarte:** El proyecto ya tiene `pydantic` en
requirements.txt, pero architecture.md exige "Inmutabilidad por defecto.
Dataclasses con `frozen=True`". Las dataclasses congeladas de stdlib son
suficientes para este modelo simple. Pydantic anadiria complejidad innecesaria
(validators con `@field_validator`, `model_dump()` vs `dataclasses.asdict()`)
sin ventaja real para este dominio plano. Ademas, `conventions.md` manda
mantener homogeneidad con el resto del proyecto, y las dataclasses son el
patron establecido.

**Alternativa descartada para test GSM:** Usar comandos AT raw (`AT+CSQ`)
enviados por puerto serial en lugar de `mmcli`.

**Justificacion:** El modem Quectel EC25 en el EdgeBox-RPI-200 es gestionado
por ModemManager via D-Bus. Abrir el puerto serial directamente para comandos
AT interferiria con ModemManager y podria causar conflictos de acceso. La
herramienta `mmcli` es la interfaz oficial y robusta. La documentacion del
dispositivo (`docs/Comandos de ModemManager para Quectel EC25.md`) confirma
este enfoque.

## Dependencia de `pyserial`

Se necesita `pyserial` para las pruebas de conectividad serial (R10, R11).
Se anade `pyserial==3.5` a `requirements.txt`. NO se usa en el modelo de
dominio (`src/config.py`); solo en los endpoints de `src/main.py`.

## Tests

Archivo: `tests/test_config.py`

Se usan `tempfile.TemporaryDirectory()` para aislar `config.yaml`. NO se usan
mocks de sistema de archivos. Para los tests de endpoints se usa
`fastapi.testclient.TestClient`.

Los tests de conectividad (test de puerto serial y GSM) NO intentan abrir
puertos reales ni ejecutar `mmcli` real. En su lugar:
- Se testea que el endpoint responde con 200 cuando el puerto existe (caso
  "fail" — el puerto no existe en CI/Docker).
- Se testea que el endpoint responde con 404 para puertos invalidos.
- Para GSM: se usa `unittest.mock.patch` sobre `subprocess.run` para simular
  exit_code 0 y exit_code != 0, verificando que `mmcli -m 0` se invoca
  correctamente.

## `github_labels`

No se requieren etiquetas adicionales.
