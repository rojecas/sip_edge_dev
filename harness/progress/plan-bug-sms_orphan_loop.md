# Plan — Bug: Loop infinito por SMS huerfanos en el modem

## Sintoma
En la EdgeBox de produccion (192.168.1.42), cuando `mmcli --send` falla (QMI error 54 por SIM bloqueada), el objeto SMS queda huerfano en el modem. El dispatcher en su siguiente ciclo de polling detecta ese SMS huerfano como entrante y lo procesa, pero al no poder determinar su estado (o ser != "received"), no se elimina correctamente, creando un loop infinito.

## Causa raiz
Tres problemas concurrentes:
1. **B1:** `_send_via_mmcli_sync()` no elimina el objeto SMS del modem cuando `--send` falla (TimeoutExpired, OSError, o returncode != 0).
2. **B2:** `_fetch_mmcli_sms()` filtra SMS por estado con `if status and status.lower() != "received"`. Si `status` es `None` (SMS huerfano sin estado definido), la condicion es `None and ...` = falsa, y NO elimina el SMS, dejandolo en el modem para el siguiente ciclo.
3. **B3:** No hay guardia `SMS_DRY_RUN` en `send_sms()` para evitar envios reales durante pruebas con SIM quemada.

## Archivos implicados
- `src/sms_service.py` (B1, B3)
- `src/sms_dispatcher_v2.py` (B2)
- `tests/test_sms_service.py` (tests B1, B3)
- `tests/test_sms_dispatcher_v2.py` (test B2)

## Fix propuesto
- B1: Anadir `_delete_orphan_sms()` helper en SMSService y llamarlo en los 3 paths de fallo de `--send` en `_send_via_mmcli_sync()`.
- B2: Cambiar condicion de `if status and status.lower() != "received"` a `if not status or status.lower() != "received"` en `_fetch_mmcli_sms()`.
- B3: Anadir verificacion de `SMS_DRY_RUN` al inicio de `send_sms()` y `send_sms_sync()`. Anadir helper `_persist_sms()` y `_update_persisted_status()` para reutilizar logica de persistencia.

## Plan de verificacion
1. `python -m unittest tests.test_sms_service tests.test_sms_dispatcher_v2 -v` — todos los tests deben pasar.
2. Verificar que el test existente de fallo de envio ahora verifica `--messaging-delete-sms`.
3. Verificar que nuevo test B2 cubre SMS con state=None.
4. Verificar que nuevos tests B3 cubren SMS_DRY_RUN=true/false/1 y persistencia.
