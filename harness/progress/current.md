# Sesión Debug Scale DFW06L + Fix Boot Contention — 2026-07-22

## Diagnóstico inicial
El usuario reportó que la comunicación con la balanza estaba rota tras fixes del 17-jul.
Se descubrieron **dos regresiones** y **un problema de contención en boot**.

## Regresión 1 — WebSocket auto-capture (src/main.py:108)
- `parse_short_response()` (DFW06L) devuelve clave `"weight"`
- `_on_scale_data()` leía `data.get("net_weight", 0.0)` — clave inexistente en formato DFW06L
- Fix: `data.get("weight") or data.get("net_weight", 0.0)` (commit aa59639)

## Regresión 2 — Thread _async_reader moría instantáneamente (src/scale.py:135)
- **Causa raíz**: commit df5cd54 (F33, graceful degradation) eliminó `self._running = True`
- Sin flag True, el `while self._running:` del thread salía inmediatamente
- El comando se escribía al puerto pero nadie leía la respuesta → 503 timeout
- Fix: restaurar `self._running = True` antes de iniciar el thread (commit aa59639)
- Verificado con strace: escritura OK, sin `read()` en fd del puerto

## Contención de puerto en boot — ModemManager vs ScaleService
- Tras reboot, ModemManager sondeaba `/dev/ttyACM*` con acceso exclusivo
- El servicio arrancaba antes de que ModemManager liberara → Errno 16
- Entraba en graceful degradation sin balanza hasta reinicio manual

### Fix A — Regla udev (deploy/99-scale-ports.rules)
SUBSYSTEM=="tty", KERNEL=="ttyACM*", ENV{ID_MM_DEVICE_IGNORE}="1"
- ModemManager ya no toca /dev/ttyACM0 (RS485) ni /dev/ttyACM1 (RS232)
- Verificado: `udevadm test` muestra ID_MM_DEVICE_IGNORE=1
- Verificado post-reboot: cero probes de ModemManager en ttyACM

### Fix B — Reintentos con backoff (src/scale.py:start())
- ScaleService.start() reintenta hasta 5 veces con backoff exponencial
- Intervalos: 1s → 2s → 4s → 8s → 8s (máx ~23s total)
- Detecta Errno 16 tanto por `errno` como por mensaje de excepción
- Red de seguridad si otro proceso bloquea el puerto transitoriamente
- Commit 6484117

## Verificación post-reboot (13:45)
- ✅ ScaleService started on /dev/ttyACM0 — sin errores, sin reintentos
- ✅ READ: weight: -2.4 kg, respuesta <1s
- ✅ Cero probes de ModemManager en ttyACM*
- ✅ Puerto en uso exclusivo por uvicorn (PID 1284)

## Archivos modificados
- src/main.py — _on_scale_data: data.get("weight") fallback
- src/scale.py — self._running = True + retry backoff
- deploy/99-scale-ports.rules — udev rule (nuevo)
- docs/database.md — auto-regenerado

## Próxima sesión
- Features pendientes: F32 (sample_imaging), F34 (alert_monitor), F35 (sms_scheduling_v2)
- F33 (sql_tools_v2) en testing
- Cerrar 6 archivos closure-*.md faltantes
