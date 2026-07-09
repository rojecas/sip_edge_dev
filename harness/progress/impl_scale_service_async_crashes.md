# Implementation — Bug #29: scale_service_async_crashes

## Trazabilidad de cambios

### Bug 1 — `_async_reader` kills thread on serial errors
**Archivo:** `src/scale.py`
**Cambio:** Reemplazar `break` con logica de recuperacion
- Anadido metodo `_recover_serial()` que cierra el puerto anterior y crea uno nuevo
- Anadido contador `consecutive_errors` con maximo 5 reintentos
- Backoff exponencial 1s, 2s, 4s, 8s (max)
- `TypeError` anadido al handler de recuperacion (bug observado en produccion)
- `SerialTimeoutException` manejo separado (NO desencadena recovery, solo log debug)

### Bug 2a — Queue never drained in real-time
**Archivo:** `src/scale.py`
**Cambio:** Mover `_process_async_queue()` DENTRO del while loop
- Antes: `_process_async_queue()` solo se llamaba al salir del while (line 205)
- Ahora: se llama en cada iteracion, justo despues de `self._async_queue.put(parsed)`
- Se mantiene la llamada al final del while para drenar items restantes al salir

### Bug 2b — Wrong event loop from background thread
**Archivo:** `src/main.py`
**Cambio:** Pasar event loop explicitamente
- Anadida variable module-level `_event_loop` que almacena el loop de uvicorn
- En `lifespan()`, se guarda `_event_loop = asyncio.get_running_loop()` ANTES de iniciar ScaleService
- `_on_scale_data()` usa `_event_loop` si no es None, con fallback a `_resolve_event_loop()`
- `_resolve_event_loop()` se mantiene por compatibilidad (tests existentes la usan)

### Bug 3 — Log "ScaleService started" missing
**Archivo:** `src/main.py`
**Cambio:** Mover `logging.basicConfig()` antes de `ScaleService.start()`
- Antes: `ScaleService.start()` en line 161, `logging.basicConfig()` en line 176
- Ahora: `logging.basicConfig()` se ejecuta al inicio del lifespan, antes de cualquier inicializacion

### Restauracion del sleep en loop
**Archivo:** `src/scale.py`
**Cambio:** Restaurar `time.sleep(0.05)` al final del while loop
- En la refactorizacion inicial, el sleep se movio solo al `except Exception:` handler
- Esto causaba un tight-loop que impedia el dispatch correcto del callback en el thread principal
- Restaurado como `time.sleep(0.05)` fuera del try/except, al final del while

## Archivos modificados
- `src/scale.py` — Bugs 1, 2a, sleep restoration
- `src/main.py` — Bugs 2b, 3
- `tests/test_scale.py` — 3 regression tests (Bug 1 x2, Bug 2a x1)
- `tests/test_main.py` — 2 regression tests (Bug 2b x2)

## Regression tests
| Test | Bug | Verifica |
|------|-----|----------|
| `test_async_reader_recovers_from_serial_error` | Bug 1 | SerialException → recovery → new serial creado |
| `test_async_reader_type_error_recovery` | Bug 1 | TypeError → recovery → reader continua |
| `test_async_queue_drains_before_stop` | Bug 2a | Callback se dispara antes de stop() |
| `test_event_loop_module_variable_exists` | Bug 2b | `_event_loop` definido en module |
| `test_on_scale_data_uses_event_loop_when_set` | Bug 2b | `_on_scale_data` usa `_event_loop` en vez de `_resolve_event_loop` |
