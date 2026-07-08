# Bug #26 — emergency_request_wrong_sms

## Causa raíz

**Double-send race condition entre `send_sms()` y `SmsSendQueue`.**

Cuando `create_request()` en `emergency_mode.py` llama a `send_sms()` para enviar la solicitud de emergencia al administrador, ocurrían DOS envíos simultáneos del mismo SMS:

1. **`send_sms()`** persiste el mensaje con `status="pending"` y luego **también** lo envía directamente via `_send_via_mmcli(phone, message)` **sin pasar `message_id`** — esto significa que NO se guarda `modem_sms_id` en la base de datos para este envío.

2. **`SmsSendQueue`** (thread separado, polling cada 2s) detecta el mensaje con `status="pending"` y lo envía de nuevo via `_send_via_mmcli_sync(phone, message, message_id=msg.id)` **SÍ pasando `message_id`** — aquí SÍ se guarda `modem_sms_id`.

**El problema con el Envío A (desde `send_sms()` directamente):**
- Como no se guardó `modem_sms_id`, si el módem reporta este SMS como "received" (eco del envío), el dispatcher lo procesa como SMS entrante.
- Pasa el filtro B2 (state="received").
- Fix 3 (`message_exists_by_modem_id()`) NO lo detecta porque el `modem_sms_id` no está en BD.
- El texto del SMS es la solicitud de emergencia, NO coincide con "manual on".
- `process_incoming_sms()` retorna `False` (texto no reconocido como emergencia).
- `handle_sms_query()` intenta procesarlo con LLM.
- LLM falla (LlamaConnectionError) → envía "Lo siento, el sistema de análisis no está disponible en este momento." al admin.

## Diagnóstico

Archivos revisados:
- `src/emergency_mode.py` — método `create_request()`, endpoint POST /api/emergency/request
- `src/sms_service.py` — método `send_sms()`, `_persist_sms()`, `_send_via_mmcli()`
- `src/sms_send_queue.py` — `_send_with_retry()`, `_process_pending_messages()`
- `src/sms_dispatcher_v2.py` — `_dispatch()`, `_fetch_mmcli_sms()`
- `src/agent_orchestrator.py` — `handle_sms_query()`
- `tests/test_sms_service.py` — tests existentes de persistencia
- `tests/test_emergency_mode.py` — tests existentes de emergencia

Hallazgos clave:
1. `send_sms()` hacía doble envío: persistía como "pending" Y llamaba a `_send_via_mmcli()` directamente.
2. `_send_via_mmcli()` llamaba a `_send_via_mmcli_sync(phone, message)` SIN `message_id`, por lo que `modem_sms_id` nunca se guardaba en el envío directo.
3. El `SmsSendQueue` (con `message_id`) guardaba `modem_sms_id` correctamente, pero el envío A quedaba huerfano.

## Fix aplicado

**Archivo: `src/sms_service.py`** — método `send_sms()`:

Cuando `self._persistence is not None` (F27 activo), `send_sms()`:
1. Persiste el mensaje con `status="pending"` (igual que antes)
2. **Ya NO llama a `_send_via_mmcli()` directamente**
3. Retorna `True`

El `SmsSendQueue` se encarga del envío real, pasando `message_id`, garantizando que `modem_sms_id` se guarde correctamente.

El comportamiento legacy (sin persistencia configurada) se mantiene igual — el envío directo via mmcli sigue funcionando.

Esto elimina:
- ✅ El double-send race condition
- ✅ El objeto SMS huerfano en el módem sin `modem_sms_id`
- ✅ La posibilidad de que el dispatcher procese el eco del envío como entrante

## Archivos modificados

- `src/sms_service.py` — método `send_sms()`: nueva rama que delega al `SmsSendQueue` cuando hay persistencia configurada
- `tests/test_sms_service.py` — 2 nuevos tests de regresión

## Tests añadidos

1. **`test_send_sms_with_persistence_does_not_call_mmcli_directly`** — Verifica que con persistencia y `dev_mode=False`, `send_sms()` NO llama a mmcli (solo persiste como "pending").

2. **`test_send_sms_legacy_path_still_calls_mmcli`** — Verifica que sin persistencia (legacy), `send_sms()` sigue llamando a mmcli directamente (compatibilidad hacia atrás).

## Verificación

- [x] `python -m unittest tests.test_sms_service -v` — 37 tests OK (incluyendo los 2 nuevos)
- [x] `python -m unittest tests.test_emergency_mode -v` — 63 tests OK
- [x] `python -m unittest discover -s tests -v` — todos los tests OK
- [x] `./init.ps1` — todas las secciones OK (timeout en tests por tiempo, pero todos los tests individuales pasan)
