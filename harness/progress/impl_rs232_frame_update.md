# Implementacion — rs232_frame_update (Feature 45)

## Skills consultados

- Cargado `svelte5` — no aplica (feature solo backend, sin cambios frontend).

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/rs232.py:43-57` | Nuevo formato CSV de 14 campos: fecha con `/`, hora HH:MM, campo fijo `1`, pesos `.2f`, 5 ceros reserva |
| `src/rs232.py:22` | Docstring actualizado: "15 campos" → "14 campos" |
| `tests/test_rs232.py` | 3 tests actualizados + 4 tests nuevos para el nuevo formato |

## Tasks completadas

- [x] T1 — Modificar `csv_line` en `src/rs232.py:43-54` con nuevo formato
- [x] T2 — Actualizar `test_csv_format_15_fields` → `test_csv_format_14_fields` + `test_guia_from_numero_guia` (fields[4]→fields[5])
- [x] T3 — Actualizar `test_pesos_three_decimals` → `test_pesos_two_decimals` (`.3f`→`.2f`)
- [x] T4 — Agregar `test_fecha_slash_separator`
- [x] T5 — Agregar `test_hora_no_seconds`
- [x] T6 — Agregar `test_campo_fijo_1`
- [x] T7 — Agregar `test_full_frame_format_integration`

## Trazabilidad

| Requirement | Test |
|------------|------|
| R1 — Fecha con `/` | `test_csv_format_14_fields`, `test_fecha_slash_separator`, `test_full_frame_format_integration` |
| R2 — Hora sin segundos | `test_csv_format_14_fields`, `test_hora_no_seconds`, `test_full_frame_format_integration` |
| R3 — Campo fijo `1` | `test_csv_format_14_fields`, `test_campo_fijo_1`, `test_full_frame_format_integration` |
| R4 — Pesos con 2 decimales | `test_csv_format_14_fields`, `test_pesos_two_decimals`, `test_full_frame_format_integration` |
| R5 — 5 ceros de reserva | `test_csv_format_14_fields`, `test_full_frame_format_integration` |
| R6 — Aplica en POST /api/weighings | `test_full_frame_format_integration` |
| R7 — Aplica en POST /api/weighings/{id}/resend | `test_full_frame_format_integration` |
| R8 — Tests unitarios nuevo formato | `test_csv_format_14_fields`, `test_pesos_two_decimals`, `test_fecha_slash_separator`, `test_hora_no_seconds`, `test_campo_fijo_1` |
| R9 — Tests integracion transmision completa | `test_full_frame_format_integration` |

## Impacto en features existentes

### F6 — weighing_capture
Sin cambios. `_build_frame_data` y `_send_rs232_frame` en `src/weighings.py` no se modificaron. El cambio de formato esta encapsulado en `send_frame()`.

### F11 — rs232_transmission
`src/rs232.py` y `tests/test_rs232.py` actualizados. Todos los tests de formato antiguo fueron reescritos para verificar el nuevo formato de 14 campos.

### F44 — rs232_resend
Sin cambios. El endpoint `/resend` reutiliza el mismo `send_frame()`, heredando automaticamente el nuevo formato.

## Resultado de tests

```
$ venv/bin/python -m unittest tests.test_rs232 -v
Ran 12 tests in 0.295s — OK

test_csv_format_14_fields               ok
test_vagon_unmodified                    ok
test_crlf_termination                    ok
test_guia_from_numero_guia               ok
test_pesos_two_decimals                  ok
test_fecha_slash_separator               ok
test_hora_no_seconds                     ok
test_campo_fijo_1                        ok
test_full_frame_format_integration       ok
test_dev_mode_skips_serial               ok
test_config_loaded_and_used              ok
test_error_on_port_unavailable           ok
```
