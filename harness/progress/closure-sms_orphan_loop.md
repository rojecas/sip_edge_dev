# Closure — Bug: Loop infinito por SMS huerfanos en el modem

## Sintoma
En la EdgeBox de produccion, cuando `mmcli --send` falla (QMI error 54 por SIM bloqueada), el objeto SMS queda huerfano en el modem. El dispatcher en su siguiente ciclo de polling detecta ese SMS huerfano como entrante, creando un loop infinito de reintentos.

## Causa raiz
Tres problemas concurrentes:
1. **B1:** `_send_via_mmcli_sync()` no limpiaba el objeto SMS del modem cuando `--send` fallaba.
2. **B2:** `_fetch_mmcli_sms()` filtraba con `if status and status.lower() != "received"`. SMS huerfanos sin estado (`state=None`) pasaban el filtro y se quedaban en el modem.
3. **B3:** No existia guardia `SMS_DRY_RUN` para evitar envios reales durante pruebas.

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/sms_service.py` | B1: Anadido `_delete_orphan_sms()` helper + llamado en 3 paths de fallo de `--send`. B3: Anadido `SMS_DRY_RUN` guardia en `send_sms()` y `send_sms_sync()`. Creados helpers `_persist_sms()` y `_update_persisted_status()`. |
| `src/sms_dispatcher_v2.py` | B2: Cambiado `if status and status.lower() != "received"` a `if not status or status.lower() != "received"`. |
| `tests/test_sms_service.py` | B1: `test_send_sms_returns_false_when_send_fails` ahora verifica `--messaging-delete-sms`. B3: Anadida clase `TestSMSServiceDryRun` con 6 tests. |
| `tests/test_sms_dispatcher_v2.py` | B2: Anadida clase `TestSmsDispatcherV2B2` con 2 tests. Anadidos `import asyncio` e `import subprocess`. |

## Fix aplicado

### B1 — Eliminar SMS huerfano del modem cuando `--send` falla
- Nuevo metodo `_delete_orphan_sms(sms_index)` en `SMSService`.
- Llamado desde 3 lugares en `_send_via_mmcli_sync()`: `except subprocess.TimeoutExpired`, `except OSError`, e `if result.returncode != 0`.

### B2 — No procesar SMS sin estado
- Cambio de una linea: `if not status or status.lower() != "received"` en lugar de `if status and status.lower() != "received"`.

### B3 — Guardia SMS_DRY_RUN
- `send_sms()` y `send_sms_sync()` verifican `SMS_DRY_RUN` al inicio, antes de cualquier logica.
- Nuevos helpers `_persist_sms()` y `_update_persisted_status()` encapsulan logica de persistencia.

## Regression tests
- `TestSMSServiceErrorHandling.test_send_sms_returns_false_when_send_fails` verifica que `--messaging-delete-sms` es llamado con el indice correcto tras fallo de envio.
- `TestSmsDispatcherV2B2.test_sms_without_state_is_deleted_and_not_processed` verifica que SMS sin estado se elimina y no se procesa.
- `TestSmsDispatcherV2B2.test_sms_with_received_state_is_processed` verifica que SMS con state='received' se procesa normalmente.
- `TestSMSServiceDryRun` (6 tests) cubre: SMS_DRY_RUN=true/false/1, send_sms_sync, persistencia en dry run.

## Resultado de tests
```
Ran 44 tests in 0.501s
OK
```

## Nota
Los warnings de `harness/init.ps1` son pre-existentes (validacion de schema de features legacy). No estan relacionados con este fix.
