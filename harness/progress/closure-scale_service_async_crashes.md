# Closure — Bug #29: scale_service_async_crashes

## Sintoma
Tres bugs independientes en ScaleService que impedian el funcionamiento
correcto del lector asincrono de balanza y del WebSocket de peso en vivo:

1. **Bug 1:** Error serial (SerialException, TypeError) mata el thread
   `_async_reader` con `break`, sin recuperacion. El servicio de balanza
   queda inoperativo hasta reiniciar sip-edge.
2. **Bug 2a:** `_process_async_queue()` se ejecuta solo al salir del while
   loop. Los datos parseados nunca se desencolan en vivo — el callback
   nunca se dispara durante operacion normal.
3. **Bug 2b:** `_on_scale_data()` se invoca desde thread background.
   `_resolve_event_loop()` retorna `new_event_loop()` que no es el loop
   de uvicorn. `run_coroutine_threadsafe(ws.send_text(), wrong_loop)`
   nunca ejecuta el send_text.
4. **Bug 3:** `logging.basicConfig()` se ejecuta DESPUES de
   `ScaleService.start()`. El mensaje "ScaleService started" no aparece
   en logs.

## Causa raiz

### Bug 1 — Sin recuperacion ante errores seriales
`_async_reader` hacia `break` inmediato sin intentar re-abrir el puerto.

### Bug 2a — Queue drenada solo al salir del loop
`_process_async_queue()` estaba fuera del while, no dentro.

### Bug 2b — Event loop incorrecto desde thread background
`asyncio.get_running_loop()` lanza RuntimeError desde thread no-asyncio.
`new_event_loop()` crea loop ajeno a uvicorn.

### Bug 3 — logging.basicConfig tarde
`logging.basicConfig()` estaba despues de `ScaleService.start()`.

## Archivos modificados
- `src/scale.py` — Anadido `_recover_serial()`, retry con backoff,
  `_process_async_queue()` dentro del while, `TypeError` en handler de
  recuperacion, `SerialTimeoutException` handler separado,
  `time.sleep(0.05)` restaurado fuera del try/except.
- `src/main.py` — Anadido `_event_loop` module-level, asignacion en
  lifespan antes de ScaleService.start(), `_on_scale_data()` usa
  `_event_loop`, `logging.basicConfig()` movido antes de start().
- `tests/test_scale.py` — 3 regression tests nuevos
- `tests/test_main.py` — 2 regression tests nuevos

## Fix aplicado

### Bug 1
`_recover_serial()` intenta cerrar el puerto actual y re-abrirlo con
los mismos parametros. Backoff exponencial 1s-8s. Maximo 5 reintentos
consecutivos antes de rendirse. TypeError se trata igual que
SerialException/OSError.

### Bug 2a
`_process_async_queue()` se llama en cada iteracion del while loop,
justo despues de encolar datos parseados. La llamada al final del while
se mantiene para drenar items al salir.

### Bug 2b
Variable module-level `_event_loop` almacena el loop de uvicorn.
Se asigna en la funcion `lifespan()` antes de crear ScaleService.
`_on_scale_data()` usa `_event_loop if _event_loop is not None`.

### Bug 3
`logging.basicConfig(level=logging.INFO, force=True)` movido a las
primeras lineas del lifespan, antes de `ScaleService.start()`.

## Regression tests
- `test_async_reader_recovers_from_serial_error` — verifica que
  SerialException desencadena recovery via `_recover_serial()`
- `test_async_reader_type_error_recovery` — verifica que TypeError
  desencadena recovery
- `test_async_queue_drains_before_stop` — verifica que callback se
  dispara dentro del while (antes de stop())
- `test_event_loop_module_variable_exists` — verifica `_event_loop`
  definido
- `test_on_scale_data_uses_event_loop_when_set` — verifica que
  `_on_scale_data` usa `_event_loop`

## Resultado de verificacion
- `tests.test_scale` — 33 tests OK
- `tests.test_main` — 13 tests OK
- Ambos suites: 46 tests OK, 0 failures, 0 errors
