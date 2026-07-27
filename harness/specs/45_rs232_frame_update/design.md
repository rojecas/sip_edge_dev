# Design — rs232_frame_update

## Decisiones tecnicas

### Archivos a modificar

| Archivo              | Cambio                                                      |
|----------------------|-------------------------------------------------------------|
| `src/rs232.py:43-54` | Reconstruir `csv_line` con el nuevo formato de 16 campos     |
| `tests/test_rs232.py`| Actualizar tests existentes + agregar tests del nuevo formato|

### Archivos NO modificados

- `src/weighings.py:_build_frame_data` — La funcion sigue retornando
  `fecha`/`hora` en isoformat. La transformacion a YYYY/MM/DD y HH:MM ocurre
  dentro de `send_frame()`.
- `src/weighings.py:_send_rs232_frame` — Sin cambios; solo invoca `send_frame`.

### Cambios en `send_frame()` (src/rs232.py:43-54)

El bloque actual:

```python
csv_line = (
    f"{frame_data['id']},"
    f"{frame_data['fecha']},"
    f"{frame_data['hora']},"
    f"{frame_data['vagon']},"
    f"{frame_data['numero_guia']},"
    f"{float(frame_data['pesos']['muestra']):.3f},"
    f"0,0,0,0,0,0,0,"
    f"{float(frame_data['pesos']['vegetal_extrano']):.3f},"
    f"{float(frame_data['pesos']['mineral']):.3f}"
    f"\r\n"
)
```

Se reemplaza por:

```python
fecha_fmt = frame_data["fecha"].replace("-", "/")
hora_fmt = frame_data["hora"][:5]
csv_line = (
    f"{frame_data['id']},"
    f"{fecha_fmt},"
    f"{hora_fmt},"
    f"{frame_data['vagon']},"
    f"1,"
    f"{frame_data['numero_guia']},"
    f"{float(frame_data['pesos']['muestra']):.2f},"
    f"0,0,0,0,0,0,0,"
    f"{float(frame_data['pesos']['vegetal_extrano']):.2f},"
    f"{float(frame_data['pesos']['mineral']):.2f}"
    f"\r\n"
)
```

Cambios puntuales:
1. `fecha` transforma `-` a `/` → `"2026-07-24".replace("-", "/")` = `"2026/07/24"`
2. `hora` trunca a 5 caracteres → `"10:30:00"[:5]` = `"10:30"`
3. Nuevo campo fijo `1` insertado entre vagon y numero_guia
4. Pesos: `.3f` → `.2f`
5. Ceros de reserva: 7 ceros (`"0,0,0,0,0,0,0"`)

### Nuevo layout de 16 campos

| Pos | Campo                | Fuente                                         |
|-----|----------------------|------------------------------------------------|
| 1   | id                   | `frame_data["id"]`                             |
| 2   | fecha YYYY/MM/DD     | `frame_data["fecha"].replace("-", "/")`        |
| 3   | hora HH:MM           | `frame_data["hora"][:5]`                       |
| 4   | vagon                | `frame_data["vagon"]`                          |
| 5   | campo fijo `1`       | literal `"1"`                                  |
| 6   | numero_guia          | `frame_data["numero_guia"]`                    |
| 7   | peso_muestra (.2f)   | `frame_data["pesos"]["muestra"]`               |
| 8   | reserva 1            | `0`                                            |
| 9   | reserva 2            | `0`                                            |
| 10  | reserva 3            | `0`                                            |
| 11  | reserva 4            | `0`                                            |
| 12  | reserva 5            | `0`                                            |
| 13  | reserva 6            | `0`                                            |
| 14  | reserva 7            | `0`                                            |
| 15  | peso_vegetal (.2f)   | `frame_data["pesos"]["vegetal_extrano"]`       |
| 16  | peso_mineral (.2f)   | `frame_data["pesos"]["mineral"]`               |

Terminador: `\r\n` (sin cambios).

## Analisis de impacto en features existentes

### F6 — weighing_capture

| Aspecto                          | Detalle                                                     |
|----------------------------------|-------------------------------------------------------------|
| Archivos impactados              | Ninguno. F6 llama `_build_frame_data` + `_send_rs232_frame` |
| Compatibilidad hacia atras       | No rompe. El formato de trama cambia pero el flujo es igual |
| Tests existentes                 | Sin cambios necesarios. `_build_frame_data` no se modifica  |
| Mitigacion                       | No requiere                                                   |

`_build_frame_data` y `_send_rs232_frame` en `src/weighings.py` no se modifican.
El cambio de formato esta encapsulado en `send_frame()`. El flujo de llamada no
cambia: `create_weighing()` → `_build_frame_data()` → `_send_rs232_frame()` →
`send_frame()`.

### F11 — rs232_transmission

| Aspecto                          | Detalle                                                     |
|----------------------------------|-------------------------------------------------------------|
| Archivos impactados              | `src/rs232.py:43-54`, `tests/test_rs232.py`                  |
| Compatibilidad hacia atras       | Rompe el formato anterior. Adrede                            |
| Tests existentes                 | Deben actualizarse para reflejar el nuevo formato            |
| Mitigacion                       | Todos los tests de `test_rs232.py` se actualizan             |

F11 es la feature que introdujo el formato original de 15 campos. Esta feature
(45) actualiza ese formato. Los tests existentes que verificaban el formato
anterior (`test_csv_format_15_fields`, `test_pesos_three_decimals`) deben
reescribirse para verificar el nuevo formato.

### F44 — rs232_resend

| Aspecto                          | Detalle                                                     |
|----------------------------------|-------------------------------------------------------------|
| Archivos impactados              | Ninguno. F44 llama el mismo flujo que F6                    |
| Compatibilidad hacia atras       | No rompe. El endpoint `/resend` usa el mismo `send_frame()` |
| Tests existentes                 | Sin cambios. El reenvio hereda automaticamente el nuevo fmt |
| Mitigacion                       | No requiere                                                   |

El endpoint `/resend` reutiliza `_build_frame_data()` y `_send_rs232_frame()`,
que a su vez llaman a `send_frame()`. El cambio de formato en `send_frame()`
se aplica automaticamente a ambos endpoints.

### Consumidores de `send_frame()` (rastreo con grep)

| Archivo       | Linea | Contexto                                            |
|---------------|-------|-----------------------------------------------------|
| weighings.py  | 112   | `from src.rs232 import send_frame`                  |
| weighings.py  | 114   | `send_frame(frame_data, format="csv")`              |

Unico sitio de importacion y unica llamada. Consumido por `_send_rs232_frame()`,
que a su vez es llamado desde `create_weighing()` (linea 162) y
`resend_weighing()` (linea 340).

## Persistencia

No aplica. Esta feature no modifica la base de datos.

## Alternativa descartada

**Alternativa:** Modificar `_build_frame_data` en `src/weighings.py` para que
retorne fecha y hora ya formateadas (YYYY/MM/DD, HH:MM) y agregar el campo fijo
`1` al diccionario.

**Descartada porque:**
1. `_build_frame_data` es una funcion de proposito general que construye datos
   para multiples consumidores (API response, RS232, futuro consumidor). Forzar
   el formato de trama en el modelo de datos acopla la capa de dominio a la capa
   de presentacion serial.
2. La transformacion de formato pertenece a la capa de transmision (`rs232.py`),
   no al modelo de datos (`weighings.py`).
3. El campo fijo `1` es un artefacto del protocolo RS-232, no del dominio de
   pesaje. No debe contaminar `_build_frame_data`.

## github_labels

No aplica. Sin etiquetas adicionales.
