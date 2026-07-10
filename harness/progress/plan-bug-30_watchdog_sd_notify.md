# Plan de Bug — watchdog_sd_notify (ID: #30)

## Sintoma
El servicio sip-edge es matado por systemd con SIGABRT aproximadamente cada
30-35 segundos, causando un bucle de reinicio infinito. Los clientes experimentan
ERR_CONNECTION_REFUSED durante los reinicios. El journalctl muestra:

```
Watchdog timeout (limit 30s)!
Killing process uvicorn with signal SIGABRT
```

El watchdog de systemd (`WatchdogSec=30`) nunca recibe `WATCHDOG=1`, o lo recibe
demasiado tarde, y por lo tanto mata el proceso.

## Causa raiz
El fix original (Bug #17, commit `989c67d` de 2026-06-17) implemento
correctamente el modulo `sd_notify.py` y agrego una tarea asincrona
`_watchdog_heartbeat()` en `main.py` que envia `WATCHDOG=1` cada 25s.
Sin embargo, este fix tiene **dos problemas** que combinados causan el timeout:

1. **Tarea creada demasiado tarde en el lifespan**: La tarea `_watchdog_heartbeat()`
   se creaba al final de la funcion `lifespan()`, DESPUES de toda la
   inicializacion de servicios: `ScaleService.start()`, `init_db()`,
   `_find_quectel_modem()` (con subprocess de hasta 5s), `SMSService.start()`,
   `EmergencyModeService.restore_from_db()`, clientes LLM dual, etc.
   
   La inicializacion completa puede tomar entre 5 y 10 segundos.

2. **Primera notificacion diferida 25s**: La tarea ejecutaba
   `await asyncio.sleep(25)` ANTES de enviar la primera notificacion. No habia
   `sd_notify()` inmediato al inicio.

3. **Intervalo de 25s demasiado cercano a WatchdogSec=30**: systemd recomienda
   enviar notificaciones a la **mitad** del intervalo (15s para WatchdogSec=30)
   para tener margen de seguridad. Con 25s solo quedan 5s de margen; cualquier
   retraso en el event loop (por inferencia LLM, procesamiento SMS, etc.) puede
   superar los 30s.

**Resultado combinado**: `tiempo_inicio (5-10s) + sleep(25s) = 30-35s` antes
de la primera notificacion. El watchdog dispara el timeout a los 30s y mata
el proceso con SIGABRT. Incluso si la primera notificacion llega a tiempo,
notificaciones subsiguientes con solo 5s de margen son fragiles bajo carga.

## Archivos implicados
- **`src/main.py`** — Mover la tarea `_watchdog_heartbeat()` al INICIO del
  lifespan (justo despues de `_event_loop = asyncio.get_running_loop()`), 
  anadir `sd_notify()` inmediato antes del loop, cambiar intervalo de 25s a 15s.
- **`src/sd_notify.py`** — Sin cambios (implementado correctamente).
- **`tests/test_sd_notify.py`** — Anadir regression test que verifica:
  - El intervalo es `asyncio.sleep(15)`, no 25
  - `sd_notify()` se llama ANTES del primer sleep

## Fix propuesto
En `src/main.py`, dentro del `lifespan` async context manager:

1. **Reubicar** el bloque watchdog inmediatamente despues de
   `_event_loop = asyncio.get_running_loop()` (linea 178), ANTES de cualquier
   inicializacion de servicio.

2. **Notificacion inmediata**: Agregar `sd_notify()` al inicio de la funcion
   `_watchdog_heartbeat()`, antes del `while True`. Esto asegura que systemd
   reciba al menos un `WATCHDOG=1` en los primeros milisegundos despues de que
   el event loop esta listo.

3. **Cambiar intervalo**: `asyncio.sleep(25)` → `asyncio.sleep(15)`.
   15s es la mitad de `WatchdogSec=30`, siguiendo la recomendacion oficial de
   systemd.

4. **Cleanup**: El codigo de cancelacion (`watchdog_task.cancel()` + `await`)
   permanece despues del `yield` sin cambios. La variable `watchdog_task`
   sigue siendo accesible a traves del `yield` del context manager.

## Plan de verificacion
1. **Regression test**: `test_watchdog_heartbeat_interval_is_15_seconds` en
   `tests/test_sd_notify.py` verifica que el codigo fuente de `main.py`:
   - Contiene `asyncio.sleep(15)` (no 25)
   - La primera llamada a `sd_notify()` ocurre antes del primer `asyncio.sleep`
   
2. **Test suite existente**: Ejecutar `python -m unittest tests.test_sd_notify -v`
   para confirmar que no hay regresiones (los tests de sockets Unix fallan en
   Windows por falta de `AF_UNIX`, esto es pre-existente y esperado).

3. **`./init.ps1`**: Verificar que el harness completa sin errores.

4. **Verificacion en EdgeBox (post-deploy)**:
   ```bash
   sudo journalctl -u sip-edge -f  # NO debe mostrar "watchdog timeout"
   systemctl is-active sip-edge     # debe retornar "active"
   ```
