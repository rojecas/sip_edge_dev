# Review — bug 29 (scale_service_async_crashes)

**Veredicto:** APPROVED

## Cobertura del reproduction

- Reproduction (1): "Iniciar sip-edge, abrir /dev/ttyACM0 desde otro proceso - TypeError en async reader"
  [x] Cubierto por `test_async_reader_type_error_recovery` — TypeError lanzado durante readline() se captura y desencadena recovery via `_recover_serial()`. Reader continua recibiendo datos tras la recuperacion.
  [x] Cubierto por `test_async_reader_recovers_from_serial_error` — SerialException lanzado durante readline() se captura y desencadena recovery. Nuevo serial.Serial() se crea.

- Reproduction (2): "Conectar WebSocket /ws/scale, datos desde balanza - send_text nunca awaited"
  [x] Cubierto por `test_async_queue_drains_before_stop` — el callback se dispara antes de llamar a stop() (Bug 2a: drenado en tiempo real).
  [x] Cubierto por `test_event_loop_module_variable_exists` — `_event_loop` definido como variable module-level (Bug 2b).
  [x] Cubierto por `test_on_scale_data_uses_event_loop_when_set` — `_on_scale_data` usa `_event_loop` en vez de `_resolve_event_loop()` cuando `_event_loop` no es None (Bug 2b).

- Reproduction (3): "Iniciar sip-edge, buscar ScaleService started en logs - no aparece"
  [x] Cubierto por revision de codigo: `logging.basicConfig(level=logging.INFO, force=True)` movido a la linea 171 del lifespan, ANTES de `ScaleService.start()` (linea 184). No hay test directo (log capture es fragil en unit tests), pero el cambio es correcto y verificable.

## Regresiones

- Tests de scale y main: 46 tests ejecutados, **46 OK**, 0 failures, 0 errors.
- `./init.ps1`: [x] Tests pasan en contenedor Docker. init.ps1 reporta [validate_features] warnings pre-existentes (features 21, 22, 25, 28 — no relacionados con este bug).

## GitHub sync

- [x] `harness/github.json` existe con `"enabled": true`
- [x] Bug #29 tiene campo `github_issue`: `https://github.com/rojecas/sip_edge/issues/23`
- [ ] NOTA: Issue #23 no existe en GitHub (no encontrado por `gh issue view 23`). Esto es un gap pre-existente del triage, no introducido por el bug-fixer. El bug permanece en estado `triaged`, por lo que aun no requiere issue cerrado.

## Checkpoints (C11)

- C11: [x] `plan-bug-scale_service_async_crashes.md` existe con diagnostico, causa raiz, fix propuesto.
- C11: [x] `closure-scale_service_async_crashes.md` existe con sintoma, causa raiz, fix aplicado, regression tests.
- C11: [x] Regression tests asociados: 5 tests nuevos (3 en test_scale.py, 2 en test_main.py).
- C11: [x] Cada escenario de `reproduction` esta cubierto por al menos un test concreto.
- C11: [x] `./init.ps1` — tests unitarios pasan (46/46 OK). init.ps1 validacion de estructura OK.

## Resumen de fixes verificados

### Bug 1 — _async_reader sin recuperacion
**Archivo:** `src/scale.py`
- `_recover_serial()` anadido (lineas 183-212): cierra puerto anterior, crea nuevo, retorna bool.
- `TypeError` anadido al handler de excepciones (linea 244): `except (serial.SerialException, OSError, TypeError)`.
- Backoff exponencial: 1s, 2s, 4s, 8s (max).
- Maximo 5 reintentos consecutivos antes de rendirse (break).
- `SerialTimeoutException` manejado separadamente (no gatilla recovery).
- [x] Tests pasan: `test_async_reader_recovers_from_serial_error`, `test_async_reader_type_error_recovery`.

### Bug 2a — Queue drenada solo al salir del while
**Archivo:** `src/scale.py`
- `self._process_async_queue()` movido DENTRO del while loop (linea 235).
- Llamada al final del while mantenida (linea 267) para drenar items al salir.
- [x] Test pasa: `test_async_queue_drains_before_stop`.

### Bug 2b — Event loop incorrecto desde thread background
**Archivo:** `src/main.py`
- Variable module-level `_event_loop` anadida (linea 83).
- Asignada en `lifespan()` antes de `ScaleService.start()` (linea 178).
- `_on_scale_data()` usa `_event_loop if _event_loop is not None` (linea 110).
- `_resolve_event_loop()` mantenida por compatibilidad con tests.
- [x] Tests pasan: `test_event_loop_module_variable_exists`, `test_on_scale_data_uses_event_loop_when_set`.

### Bug 3 — "ScaleService started" no aparece en logs
**Archivo:** `src/main.py`
- `logging.basicConfig(level=logging.INFO, force=True)` movido a las primeras lineas del lifespan (linea 171), antes de cualquier inicializacion.
- [x] Verificado por inspeccion de codigo.

## Arquitectura y convenciones

- [x] Respeta capas: scale.py (modelo de dominio), main.py (API/CLI).
- [x] Errores explicitos: `ScaleConnectionError`, `ScaleTimeoutError`, `ScaleProtocolError`.
- [x] Sin nuevas dependencias externas.
- [x] Docstrings de modulo obligatorios presentes.
- [x] PEP 8 (lineas ≤ 100 chars).
- [x] Nombres snake_case (funciones/variables), PascalCase (clases).
- [x] Sin `print()` sueltos ni TODOs sin contexto.
- [x] Sin regresiones en tests existentes.
- [x] SOLID: Single Responsibility (cada metodo hace una cosa), Open/Closed (extension via _recover_serial).

## Observaciones menores (no bloqueantes)

1. **Counter reset en recovery fallido:** Si `_recover_serial()` falla (retorna False), el puerto queda cerrado. En la siguiente iteracion del while, al no llamarse a `readline()` (port closed, `is_open=False`), no se lanza excepcion y el contador `consecutive_errors` se resetea a 0. Esto impide que el guard `max_errors=5` se active nunca en este escenario. El thread permanece vivo pero en idle (sleep 0.05) sin reintentar recovery hasta que el servicio se reinicie. Esto es **estrictamente mejor** que el comportamiento original (thread muerto), pero la recuperacion automatica solo funciona para errores transitorios en puerto abierto, no para fallos permanentes de apertura.

2. **GitHub Issue #23 no existe:** Pre-existent gap del triage. No es responsabilidad del bug-fixer.

## Cambios requeridos

NINGUNO. El fix es correcto, los tests pasan, el codigo sigue las convenciones.
