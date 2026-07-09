# Plan de Fix — Bug #29: scale_service_async_crashes

## Sintoma
Tres sintomas independientes del mismo modulo (ScaleService + WebSocket):

1. **Bug 1:** Al ocurrir un error serial (SerialException, OSError, o TypeError por
   None en serial.read()), `_async_reader` hace `break` y el hilo muere. Nunca se
   recupera automaticamente — el servicio de balanza queda inoperativo hasta
   reiniciar sip-edge.
2. **Bug 2a:** `_async_reader` coloca datos parseados en `_async_queue` pero
   `_process_async_queue()` solo se ejecuta DESPUES del while loop (line 205).
   Los datos nunca se desencolan en vivo — el callback nunca se dispara
   durante operacion normal.
3. **Bug 2b:** `_on_scale_data()` se invoca desde el hilo background del reader.
   `_resolve_event_loop()` llama a `asyncio.get_running_loop()` que lanza
   RuntimeError desde un hilo no-asyncio, cayendo a `asyncio.new_event_loop()`.
   El `run_coroutine_threadsafe(ws.send_text(), wrong_loop)` programa en el
   loop incorrecto — send_text nunca se ejecuta.
4. **Bug 3:** `logging.basicConfig()` esta en line 176 de lifespan, DESPUES de
   `ScaleService.start()` (line 161). El logger.info("ScaleService started...")
   en scale.py:128 se ejecuta sin handler configurado — el mensaje no aparece.

## Causa raiz

### Bug 1 — Sin recuperacion ante errores seriales (scale.py:198-201)
```python
except (serial.SerialException, OSError) as e:
    if self._running:
        logger.error("Async serial read error: %s", e)
    break
```
El `break` termina el while loop inmediatamente. No hay logica de
reintento ni re-apertura del puerto.

### Bug 2a — Queue drenada solo al salir del loop (scale.py:205)
```python
self._process_async_queue()  # line 205 — FUERA del while
```
La funcion que invoca al callback se ejecuta solo cuando el hilo
termina. Debe ejecutarse dentro de cada iteracion del while.

### Bug 2b — Event loop incorrecto desde thread background (main.py:81-106)
`_on_scale_data` es llamada desde el hilo de `_async_reader`. No hay
un event loop corriendo en ese hilo, por lo que `get_running_loop()`
falla con RuntimeError. `new_event_loop()` crea un loop aislado que
no es el loop de uvicorn donde estan los WebSockets registrados.

### Bug 3 — logging.basicConfig tarde (main.py:161 vs 176)
Configuracion de logging ocurre despues de que ScaleService.start()
ya intento loggear.

## Archivos implicados
- `src/scale.py` — Bugs 1 y 2a
- `src/main.py` — Bugs 2b y 3
- `tests/test_scale.py` — Regression tests

## Fix propuesto

### Bug 1 — Retry con backoff en _async_reader
- Reemplazar `break` con logica de recuperacion:
  - Loguear el error con contexto
  - Intentar cerrar el puerto actual si sigue abierto
  - Esperar con backoff exponencial (1s, 2s, 4s, max 8s)
  - Re-intentar abrir el puerto (`serial.Serial(...)`)
  - Si re-apertura exitosa, resetear backoff y continuar loop
  - Maximo 5 reintentos consecutivos antes de rendirse

### Bug 2a — Drenar queue dentro del while
- Mover `self._process_async_queue()` dentro del while loop,
  justo despues de `self._async_queue.put(parsed)`, para que se
  ejecute en cada iteracion donde se produjeron datos.

### Bug 2b — Pasar event loop explicitamente
- Agregar un module-level variable `_event_loop` en `src/main.py`
  que almacene la referencia al loop de uvicorn.
- En el lifespan, ANTES de iniciar ScaleService, guardar
  `main._event_loop = asyncio.get_running_loop()`.
- Modificar `_on_scale_data()` para usar `main._event_loop` en
  lugar de `_resolve_event_loop()`.
- Hacer que `_resolve_event_loop()` caiga en desuso (mantener por
  compatibilidad pero no usarla en el flujo principal).

### Bug 3 — Mover logging.basicConfig al inicio del lifespan
- Mover `logging.basicConfig(level=logging.INFO, force=True)` a
  las primeras lineas del lifespan, ANTES de `ScaleService.start()`.

## Plan de verificacion
1. Ejecutar tests existentes: `python -m unittest discover -s tests -v`
   (dentro del contenedor Docker)
2. Regression test nuevo: `test_async_reader_serial_error_recovery` — verifica
   que ante un SerialException, el reader se recupera y continua recibiendo
   datos.
3. Regression test nuevo: `test_async_queue_drains_in_real_time` — verifica
   que `_process_async_queue()` se ejecuta dentro del while (el callback
   recibe datos antes de hacer stop()).
4. Regression test nuevo: `test_async_reader_typeerror_recovery` — verifica
   que TypeError en readline no mata el thread.
5. Ejecutar `./harness/init.ps1` completo.
