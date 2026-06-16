# Design — rs232_transmission

> Decisiones técnicas para la transmisión de datos a PC vía RS232.

## Archivos creados / modificados

| Archivo                 | Accion    | Proposito                                              |
|------------------------|-----------|--------------------------------------------------------|
| `src/rs232.py`          | **CREAR** | Módulo con `send_frame()` para transmisión RS232       |
| `src/weighings.py`      | MODIFICAR | Añadir `id` al frame_data en `_send_rs232_frame()`     |
| `tests/test_rs232.py`   | **CREAR** | Tests unitarios de `send_frame()`                      |
| `tests/test_weighings.py` | MODIFICAR | Añadir test de integración RS232 tras creación de pesaje |

## Nueva función: `send_frame()` en `src/rs232.py`

### Firma

```python
def send_frame(
    frame_data: dict,
    format: str = "csv",
    config_path: str = "config.yaml",
) -> None:
```

### Parámetros

| Parámetro     | Tipo   | Default         | Descripción |
|--------------|--------|-----------------|-------------|
| `frame_data` | `dict` | —               | Diccionario con datos del pesaje producido por `_build_frame_data()` (con `id` añadido por `_send_rs232_frame()`) |
| `format`     | `str`  | `"csv"`         | Ignorado. Solo existe formato CSV. Se acepta por compatibilidad con el punto de llamada existente. |
| `config_path`| `str`  | `"config.yaml"` | Ruta al archivo de configuración. Permite inyectar rutas alternativas en tests. |

### Comportamiento

1. Si `DEV_MODE` está activo (`os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes")`), retorna inmediatamente sin hacer E/S. (Cubre R7)
2. Carga la configuración del sistema con `load_config(config_path)`. (Cubre R4)
3. Extrae la configuración del puerto RS232 de `SystemConfig.rs232`.
4. Construye la línea CSV con 15 campos:
   - `Id` → `frame_data["id"]` (formateado como entero)
   - `Fecha` → `frame_data["fecha"]`
   - `Hora` → `frame_data["hora"]`
   - `Vagon` → `frame_data["vagon"]` (sin modificar)
   - `Guía` → `frame_data["numero_guia"]`
   - `Peso_muestra` → `frame_data["pesos"]["muestra"]` (con 3 decimales)
   - 7 campos fijos: `0,0,0,0,0,0,0`
   - `Peso_vegetal` → `frame_data["pesos"]["vegetal_extrano"]` (con 3 decimales)
   - `Peso_mineral` → `frame_data["pesos"]["mineral"]` (con 3 decimales)
5. Concatena los campos con coma y añade `\r\n` al final. (Cubre R2, R3, R8, R9, R10)
6. Abre el puerto serial con `serial.Serial()` usando los parámetros configurados.
7. Escribe la trama codificada en ASCII.
8. Cierra el puerto serial.
9. Si alguna operación serial falla, lanza una excepción `Rs232Error`.

### Excepciones

| Excepción                           | Contexto                                      |
|-------------------------------------|-----------------------------------------------|
| `Rs232Error`                        | Error base para fallos de transmisión RS232. Hereda de `Exception`. |
| `Rs232Error` (con mensaje)          | No se puede abrir el puerto, error de escritura, timeout, permisos insuficientes. |

La excepción es capturada por `_send_rs232_frame()` en `weighings.py`, que la
registra vía `logging.error()` y no la relanza. (Cubre R6)

### Uso de `pyserial`

El proyecto ya tiene `pyserial` como dependencia (usada en `src/scale.py`). Se
importa dentro de `send_frame()` con `import serial` para mantener el patrón de
imports localizados (similar a `scale.py`).

### DEV_MODE

La detección sigue el mismo patrón que en `src/main.py` y `src/scale.py`:

```python
dev_mode = os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes")
if dev_mode:
    return
```

(Cubre R7)

### Formato de la trama CSV (ejemplo)

Para un pesaje con:
- `id=42`, `fecha=2026-06-15`, `hora=10:30:00`
- `vagon=ABC-123`, `numero_guia=G-789`
- `peso_muestra=1.500`, `peso_vegetal_extrano=0.200`, `peso_mineral=0.800`

La trama generada será:

```
42,2026-06-15,10:30:00,ABC-123,G-789,1.500,0,0,0,0,0,0,0,0.200,0.800\r\n
```

## Modificaciones en `src/weighings.py`

### Cambio en `_send_rs232_frame()`

Añadir el campo `id` al `frame_data` antes de llamar a `send_frame()`, ya que
`_build_frame_data()` no incluye el identificador del registro:

```python
def _send_rs232_frame(frame_data: dict, record: Weighing) -> None:
    try:
        from src.rs232 import send_frame
        frame_data["id"] = record.id  # <-- añadir para la trama CSV
        send_frame(frame_data, format="csv")
        record.enviado_pc = True
    except ImportError:
        pass
    except Exception as e:
        logger.error("RS232 send failed: %s", e)
```

El cambio es mínimo: se añade `frame_data["id"] = record.id` y se cambia el
parámetro `format` de `"json"` a `"csv"` (aunque `send_frame` ignora el valor).

**Motivo de no modificar `_build_frame_data()`:** La función es usada por el
flujo de captura de pesaje (feature #6) para otros propósitos (interfaz de
usuario, logging). Añadir `id` allí cambiaría el contrato de la función para
todos los consumidores. Es más quirúrgico añadirlo en `_send_rs232_frame`, que
es el único punto donde se necesita `id` para la trama RS232.

## Persistencia

No se requieren cambios en la base de datos. El modelo `Weighing` ya tiene el
campo `enviado_pc` (`Boolean`, default `False`) desde la feature #6
(weighing_capture). No hay migraciones, tablas nuevas ni columnas nuevas.

## Alternativa descartada

**Alternativa 1:** Abrir una conexión serial persistente al puerto RS232 durante
todo el ciclo de vida de la aplicación (similar a como `ScaleService` maneja el
puerto RS485).

**Justificación del descarte:** La transmisión RS232 al PC externo es un evento
discreto (ocurre solo tras cada confirmación de pesaje, que puede ser cada pocos
minutos). Mantener el puerto abierto permanentemente:
- Consume un descriptor de archivo innecesariamente.
- Puede interferir con otros procesos que necesiten el puerto RS232 (ej. test de
  conectividad desde `POST /api/config/test/rs232`).
- Añade complejidad de lifecycle (reconexión, estado compartido, limpieza en
  shutdown) sin beneficio real.
- El overhead de abrir/cerrar el puerto para una trama corta (< 200 bytes) es
  despreciable en este contexto industrial.

**Alternativa descartada 2:** Modificar `_build_frame_data()` para incluir `id`.

**Justificación del descarte:** `_build_frame_data()` es llamada desde
`create_weighing()` y su diccionario se usa para logging y potencialmente otros
consumidores (interfaz de usuario, WebSocket). Añadir `id` al diccionario
cambiaría la forma del dato para todos ellos sin necesidad. Es más limpio
inyectar `id` exclusivamente en el punto de entrada a la transmisión RS232
(`_send_rs232_frame`), manteniendo el principio de responsabilidad única.

## Tests

Archivo nuevo: `tests/test_rs232.py`

Clase `TestSendFrame` con los siguientes escenarios:

| Test                                    | Cubre |
|-----------------------------------------|-------|
| `test_csv_format_15_fields`             | R2    |
| `test_vagon_unmodified`                 | R3    |
| `test_crlf_termination`                 | R8    |
| `test_guia_from_numero_guia`            | R9    |
| `test_pesos_three_decimals`             | R10   |
| `test_dev_mode_skips_serial`            | R7    |
| `test_config_loaded_and_used`           | R4    |
| `test_error_on_port_unavailable`        | R6    |
| `test_send_frame_after_weighing`        | R1, R5 |

Los tests que requieren E/S serial usarán `unittest.mock.patch` para simular
`serial.Serial`. Los tests de formato de trama verificarán la cadena CSV sin
necesidad de hardware real. Los tests de DEV_MODE manipularán `os.environ`.

Modificación en `tests/test_weighings.py`:

- Añadir `test_create_weighing_sends_rs232` que verifica que tras crear un
  pesaje exitoso, el campo `enviado_pc` se establece a `True`. Usará
  `TestClient` y verificará el estado final del registro en BD.

## `github_labels`

No se requieren etiquetas adicionales.
