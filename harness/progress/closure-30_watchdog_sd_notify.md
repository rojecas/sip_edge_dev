# Closure — Bug #30: watchdog_sd_notify

## Sintoma
El servicio sip-edge era matado por systemd con SIGABRT aproximadamente cada
30-35s, causando un bucle de reinicio infinito. El journalctl mostraba:
"Watchdog timeout (limit 30s)!" seguido de "Killing process uvicorn with signal SIGABRT".
Los clientes experimentaban ERR_CONNECTION_REFUSED durante los reinicios.

## Causa raiz
El fix original (Bug #17, commit `989c67d`) implemento el modulo `sd_notify.py`
y agrego una tarea `_watchdog_heartbeat()` en `main.py`. Sin embargo, tenia dos
defectos que combinados causaban el timeout:

1. **Tarea creada tarde**: La tarea se creaba al FINAL de `lifespan()`, despues
   de toda la inicializacion de servicios (ScaleService, DB init, deteccion de
   modem via `mmcli -L` con timeout de 5s, SMS dispatcher, emergency service,
   clientes LLM dual, AgentOrchestrator). La inicializacion toma 5-10s.

2. **Intervalo incorrecto**: `asyncio.sleep(25)` + sin notificacion inmediata.
   El primer `WATCHDOG=1` se enviaba a los `startup_time (5-10s) + 25s = 30-35s`,
   justo en el limite del `WatchdogSec=30`. Systemd recomienda la mitad:
   15s para un timeout de 30s.

## Archivos modificados

| Archivo | Accion | Descripcion |
|---------|--------|-------------|
| `src/main.py` | **Modificado** | Watchdog movido al inicio del lifespan (linea 180, justo tras `_event_loop`), `sd_notify()` inmediato al iniciar la tarea, intervalo `asyncio.sleep(15)` (mitad de WatchdogSec=30). Cleanup tras `yield` sin cambios. |
| `tests/test_sd_notify.py` | **Modificado** | Añadido `test_watchdog_heartbeat_interval_is_15_seconds`: verifica que el fuente de main.py contiene `asyncio.sleep(15)` (no 25) y que `sd_notify()` precede al primer sleep. |
| `harness/progress/plan-bug-30_watchdog_sd_notify.md` | **Creado** | Documento de diagnostico y plan de fix. |
| `harness/progress/current.md` | **Modificado** | Actualizado con estado de la sesion. |

## Fix aplicado

### `src/main.py` (lifespan, linea 180)
Antes (linea ~336, al FINAL del lifespan):
```python
async def _watchdog_heartbeat():
    """Envia WATCHDOG=1 cada 25s..."""
    while True:
        await asyncio.sleep(25)
        sd_notify()
```
Despues (linea 180, al INICIO del lifespan):
```python
async def _watchdog_heartbeat():
    """Envia WATCHDOG=1 cada 15s..."""
    # Primera notificacion inmediata
    sd_notify()
    while True:
        await asyncio.sleep(15)
        sd_notify()
```

Cambios clave:
- **Reubicacion**: del final del lifespan (linea ~336) al inicio (linea 180),
  justo despues de que el event loop esta disponible.
- **Notificacion inmediata**: `sd_notify()` al inicio de la funcion, antes del
  loop. Systemd recibe WATCHDOG=1 en los primeros milisegundos.
- **Intervalo corregido**: `25s` → `15s` (mitad de WatchdogSec=30, siguiendo
  recomendacion oficial de systemd).

### `tests/test_sd_notify.py`
Nuevo test `test_watchdog_heartbeat_interval_is_15_seconds`:
- Verifica que `asyncio.sleep(15)` esta presente en main.py
- Verifica que `asyncio.sleep(25)` NO esta presente
- Verifica que `sd_notify()` aparece ANTES del primer `asyncio.sleep(15)`

## Regression test
```bash
python -m unittest tests.test_sd_notify.TestSdNotify.test_watchdog_heartbeat_interval_is_15_seconds -v
```

Resultado: **OK** — el test verifica que el intervalo es 15s y la primera
notificacion es inmediata.

## Resultado de `./init.ps1`
Secciones 1-5: **[OK]** todas. Seccion 6 (tests): timeout en local (requiere
Docker, esperado). Los tests de sd_notify pasan individualmente:

```
test_watchdog_heartbeat_interval_is_15_seconds ... ok
test_main_imports_sd_notify ... ok
```

## Verificacion en EdgeBox (post-deploy)
```bash
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42
cd /home/sipedge/sip_edge && git pull
echo sipedge1234 | sudo -S systemctl restart sip-edge
# Esperar >60s y verificar:
sudo journalctl -u sip-edge --no-pager -n 20  # NO debe mostrar "watchdog timeout"
systemctl is-active sip-edge                   # debe retornar "active"
curl http://192.168.1.42:8000/health           # debe retornar HTTP 200
```

## Notas
- El modulo `sd_notify.py` no requirio cambios (implementacion ya correcta).
- El intervalo de 15s = WatchdogSec/2 sigue la recomendacion oficial de systemd.
- La notificacion inmediata al inicio del loop asegura que systemd reciba al
  menos un WATCHDOG=1 antes de que cualquier inicializacion lenta ocurra.
- El margen de seguridad pasa de 5s (30-25) a 15s (30-15), suficiente para
  absorber picos de carga del event loop durante inferencia LLM.
