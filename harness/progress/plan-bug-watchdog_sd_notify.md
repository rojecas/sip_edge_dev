# Plan de Bug — watchdog_sd_notify (ID: 17)

## Sintoma
El servicio sip-edge se reinicia en un ciclo infinito cada ~30 segundos.
En los logs del sistema (`journalctl -u sip-edge`) se observa:
"Watchdog timeout (limit 30s)!" seguido de "Killing process uvicorn with signal SIGABRT".

## Causa raiz
La unidad systemd `/etc/systemd/system/sip-edge.service` tiene configurado
`WatchdogSec=30`, que activa el watchdog de systemd. Este mecanismo requiere
que el proceso envie notificaciones periodicas `WATCHDOG=1` a traves del socket
Unix `$NOTIFY_SOCKET` (protocolo `sd_notify`). Como uvicorn/FastAPI no implementa
este protocolo, systemd nunca recibe la senial de vida y asume que el proceso
esta colgado, procediendo a matarlo con SIGABRT cada 30s y reiniciarlo via
`Restart=always`.

## Archivos implicados
- **`src/sd_notify.py`** — Nuevo modulo: implementacion pura Python del protocolo
  sd_notify (leyendo `$NOTIFY_SOCKET` y enviando datagramas `WATCHDOG=1`).
- **`src/main.py`** — Modificar: en el ciclo de vida (lifespan), iniciar una tarea
  asyncio en background que ejecute sd_notify cada 25s.
- **`tests/test_sd_notify.py`** — Nuevo test: verifica el comportamiento del modulo
  sd_notify (simulando socket Unix y envio de datagramas).

## Fix propuesto
1. Crear `src/sd_notify.py` con una funcion `notify()` que:
   - Lee la variable de entorno `NOTIFY_SOCKET`.
   - Si no existe, retorna silenciosamente (no es un error).
   - Si existe, envia el mensaje `WATCHDOG=1` como datagrama Unix (`socket.SOCK_DGRAM`)
     al socket indicado.
   - Maneja errores de conexion silenciosamente (graceful degradation).

2. En `src/main.py`, dentro del `lifespan` async context manager:
   - Antes del `yield`, crear una tarea asyncio que ejecute un loop infinito:
     `await asyncio.sleep(25)` seguido de `sd_notify.notify()`.
   - Almacenar la tarea para poder cancelarla despues del `yield`.
   - Despues del `yield`, cancelar la tarea en el bloque de shutdown.

## Plan de verificacion
1. Test unitario: `test_sd_notify_notify_sends_datagram` — simula un socket Unix
   y verifica que `notify()` envia el mensaje correcto.
2. Test unitario: `test_sd_notify_no_socket` — verifica que sin `NOTIFY_SOCKET`
   la funcion no lanza error.
3. Test unitario: `test_sd_notify_bad_socket` — verifica que con socket invalido
   la funcion no lanza error.
4. Ejecutar `./init.ps1` para verificar que no hay regresiones.
