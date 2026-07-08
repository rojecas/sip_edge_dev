# Plan - Bug #26: emergency_request_wrong_sms

## Síntoma
Al solicitar modo manual desde la vista Kiosko (POST /api/emergency/request), el administrador recibe en su teléfono el mensaje "Lo siento, el sistema de análisis no está disponible en este momento." en lugar del mensaje esperado de solicitud de emergencia.

## Causa raíz

**Double-send race condition entre `send_sms()` y `SmsSendQueue`:**

Cuando `create_request()` llama a `send_sms()`, el flujo actual es:

1. `send_sms()` persiste el SMS en `sms_messages` con `status="pending"` (via `_persist_sms()`)
2. `send_sms()` envía el SMS directamente via `_send_via_mmcli()` → `_send_via_mmcli_sync(phone, message)` **SIN `message_id`**
3. `SmsSendQueue` (thread separado, poll cada 2s) detecta el mensaje pendiente y también lo envía via `_send_via_mmcli_sync(phone, message, message_id=msg.id)` **CON `message_id`**

Esto produce DOS envíos del mismo SMS:
- **Envío A (desde `send_sms()` directamente):** Crea objeto SMS en el módem, lo envía, pero **NO guarda `modem_sms_id`** porque no pasa `message_id`.
- **Envío B (desde `SmsSendQueue`):** Crea otro objeto SMS en el módem, lo envía, y **SÍ guarda `modem_sms_id`** porque pasa `message_id`.

**Problema con el Envío A:**
Como no se guardó `modem_sms_id`, si el módem reporta este SMS como "received" (en lugar de "sent") —o si ocurre cualquier eco—, el dispatcher lo procesa como SMS entrante:
1. Pasa filtro B2 (state="received")
2. Fix 3 (`message_exists_by_modem_id()`) NO lo detecta porque `modem_sms_id` no está en BD
3. El texto del SMS es la solicitud de emergencia, NO coincide con "manual on"
4. `process_incoming_sms()` retorna `False` (texto no reconocido)
5. `handle_sms_query()` intenta procesarlo con LLM
6. LLM falla (LlamaConnectionError) → envía "Lo siento..." al número del admin

## Archivos implicados
- `src/sms_service.py` — método `send_sms()`: debe delegar el envío real al `SmsSendQueue` cuando hay persistencia configurada
- `tests/test_sms_service.py` — nuevos tests de regresión

## Fix propuesto

**En `src/sms_service.py`, método `send_sms()`:**

Cuando `self._persistence is not None` (F27 está activo), `send_sms()` NO debe llamar a `_send_via_mmcli()` directamente. Debe:
1. Persistir el mensaje con `status="pending"` (ya lo hace)
2. Retornar `True`

El `SmsSendQueue` se encarga del envío real, con `message_id` correcto, garantizando que `modem_sms_id` se guarde.

El comportamiento legacy (sin persistencia) se mantiene igual.

## Plan de verificación
1. Test unitario que verifique que `send_sms()` NO llama a `_send_via_mmcli()` cuando hay persistencia
2. Test de integración que verifique que el mensaje se persiste como "pending" y el `SmsSendQueue` lo envía correctamente
3. Ejecutar `python -m unittest discover -s tests -v` → todos los tests pasan
4. Ejecutar `./init.ps1` → OK
