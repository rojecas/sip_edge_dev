# Cierre — rs232_transmission

## Resumen

Se implementó el módulo de transmisión RS232 al PC externo (`src/rs232.py`) con
la función `send_frame()` que construye y envía una trama CSV de 15 campos a
través del puerto RS232 configurado en `config.yaml`. La función es consumida
por `src/weighings.py` tras cada registro exitoso de pesaje (endpoint
`POST /api/weighings`). Incluye manejo de errores con logging sin interrupción
del flujo de pesaje, soporte para DEV_MODE (omite E/S serial en desarrollo),
y test suite completa con 10 tests cubriendo todos los requirements (R1–R10).

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/rs232.py` | **CREADO** — Módulo con `Rs232Error` y `send_frame()` para transmisión RS232 |
| `src/weighings.py` | MODIFICADO — Añadido `frame_data["id"] = record.id` y cambiado `format="json"` a `format="csv"` en `_send_rs232_frame()` |
| `tests/test_rs232.py` | **CREADO** — 8 tests unitarios para `send_frame()` (formato, configuración, errores, DEV_MODE, CRLF) |
| `tests/test_weighings.py` | MODIFICADO — Añadido `test_create_weighing_sends_rs232` (R1, R5); actualizado test existente para mockear `send_frame` |

## Decisiones técnicas

- **Import local de `serial`**: Mismo patrón que `src/scale.py`. Se importa dentro de `send_frame()` para evitar dependencia top-level cuando no hay hardware serial.
- **Apertura/cierre por trama**: El puerto se abre y cierra en cada transmisión (no persistente). Justificado porque la transmisión es un evento discreto (cada ~minutos) y evita fugas de descriptor de archivo.
- **Parámetro `format` aceptado pero ignorado**: Solo existe formato CSV. Se preserva por compatibilidad con el punto de llamada existente en `weighings.py`.
- **`id` inyectado en `_send_rs232_frame`**: No en `_build_frame_data()` para no cambiar el contrato de esta función para otros consumidores (UI, logging).
- **DEV_MODE**: Detectado via `os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes")`, mismo patrón que `main.py` y `scale.py`.

### Alternativa descartada

**Conexión serial persistente:** Se descartó mantener el puerto RS232 abierto permanentemente (como hace `ScaleService` con RS485) porque la transmisión es un evento discreto. El overhead de abrir/cerrar por trama (< 200 bytes) es despreciable en este contexto industrial, y evita interferencias con tests de conectividad u otros procesos.

## Verificación

- [x] `./init.ps1` verde — todos los bloques [OK], exit code 0
- [x] 310 tests pasan: `python -m unittest discover -s tests -v` → OK (310 tests, 0 failures)
- [x] Trazabilidad R<n> ↔ tests completa (ver tabla abajo)
- [x] Code review aprobado (ver `harness/progress/review_rs232_transmission.md`)
- [x] GitHub issue #10 creado y cerrado

## Trazabilidad R<n> ↔ tests

| R<n> | Requisito | Test(s) |
|------|-----------|---------|
| R1 | POST /api/weighings invoca send_frame | `test_create_weighing_sends_rs232` (test_weighings.py) |
| R2 | 15 campos CSV en orden literal | `test_csv_format_15_fields` (test_rs232.py) |
| R3 | Vagon sin modificación | `test_vagon_unmodified` (test_rs232.py) |
| R4 | Carga config desde config.yaml | `test_config_loaded_and_used` (test_rs232.py) |
| R5 | enviado_pc = True tras envío exitoso | `test_create_weighing_sends_rs232` (test_weighings.py) |
| R6 | Error serial → logging, no relanza | `test_error_on_port_unavailable` (test_rs232.py), `test_create_weighing_rs232_stub_import_error` (test_weighings.py) |
| R7 | DEV_MODE omite E/S serial | `test_dev_mode_skips_serial` (test_rs232.py) |
| R8 | Trama termina con CRLF | `test_crlf_termination` (test_rs232.py) |
| R9 | Guía desde numero_guia | `test_guia_from_numero_guia` (test_rs232.py) |
| R10 | Pesos con 3 decimales | `test_pesos_three_decimals` (test_rs232.py) |

## Lecciones / pitfalls

- El script `github_sync.py` falla con `UnicodeDecodeError` en Windows al leer `feature_list.json` con caracteres UTF-8 no ASCII (í, ó, etc.). Se trabajó alrededor usando `gh` CLI directamente.
- La feature no tenía `github_issue` porque el leader omitió crearlo al transicionar a `in_progress`. Se creó retroactivamente en el paso de registro.

## Release

- [x] La feature está lista para release-manager register (pendiente en tracker)
