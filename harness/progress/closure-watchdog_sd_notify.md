# Closure — Bug #17: watchdog_sd_notify

## Sintoma
El servicio sip-edge se reinicia en un ciclo infinito cada ~30s. En los logs
(`journalctl -u sip-edge`) se observa: "Watchdog timeout (limit 30s)!" seguido
de "Killing process uvicorn with signal SIGABRT". El servicio se reinicia
via `Restart=always`, causando inestabilidad permanente.

## Causa raiz
La unidad systemd tiene `WatchdogSec=30` activado, pero uvicorn/FastAPI no
implementa el protocolo `sd_notify()`. Systemd espera que el proceso envie
notificaciones `WATCHDOG=1` a traves del socket Unix `$NOTIFY_SOCKET`. Como
nunca se envian, systemd mata el proceso cada 30s pensando que esta colgado.

## Archivos modificados

| Archivo | Accion | Descripcion |
|---------|--------|-------------|
| `src/sd_notify.py` | **Creado** | Modulo Python puro que implementa el protocolo sd_notify: lee `$NOTIFY_SOCKET`, envia datagrama `WATCHDOG=1\n`. Solo stdlib (`os`, `socket`). |
| `src/main.py` | **Modificado** | En el `lifespan` context manager, se anade una tarea `asyncio` que llama `sd_notify()` cada 25s (5s de margen antes del timeout de 30s). La tarea se cancela en el shutdown. |
| `tests/test_sd_notify.py` | **Creado** | 7 tests unitarios que cubren: envio correcto de datagrama, ausencia de `$NOTIFY_SOCKET`, socket vacio, socket inexistente, sockets abstractos (`@`), logging de errores, e importabilidad desde main.py. |
| `harness/feature_list.json` | **Modificado** | Bug #17 estaba fuera del objeto raiz (JSON malformado). Se movio al array `features` y se convirtio `reproduction` de array a string (requisito del validador). |

## Fix aplicado

### `src/sd_notify.py`
Funcion `notify()` que:
1. Lee `NOTIFY_SOCKET` de entorno. Si no existe, retorna `False` silenciosamente.
2. Convierte prefijo `@` a `\0` para sockets abstractos Linux.
3. Abre socket `AF_UNIX` / `SOCK_DGRAM`, conecta, envia `WATCHDOG=1\n`.
4. Captura `OSError` y registra debug log, nunca lanza excepcion.

### `src/main.py` (lifespan)
- Antes del `yield`: se crea `asyncio.Task` con loop infinito:
  `await asyncio.sleep(25)` → `sd_notify()`
- Despues del `yield`: se cancela la tarea con `task.cancel()` + `await task`.

### `tests/test_sd_notify.py`
Cubre todos los escenarios de `reproduction` mas casos borde.

## Resultado de `./init.ps1`
```
[OK]    Entorno listo. Puedes empezar a trabajar.
```
Todos los tests pasan (incluyendo los 7 nuevos de `test_sd_notify`).

## Despliegue en EdgeBox (pendiente)
Para completar el fix en produccion, ejecutar:
```bash
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42
cd /home/sipedge/sip_edge && git pull
echo sipedge1234 | sudo -S systemctl restart sip-edge
```

## Verificacion posterior al despliegue
```bash
systemctl is-active sip-edge  # debe retornar "active"
curl http://192.168.1.42:8000/health  # debe retornar HTTP 200
sudo journalctl -u sip-edge --no-pager -n 20  # NO debe mostrar watchdog timeout
```

## Notas
- Se eligio un intervalo de 25s (5s de margen antes del timeout de 30s).
- Implementacion pura Python stdlib (`os`, `socket`, `asyncio`).
- No se modifico `WatchdogSec` en la unidad systemd (se mantiene en 30s).
- La funcion `notify()` es graceful: si no hay `$NOTIFY_SOCKET`, no hace nada.
