# Review — fix sms_race_fix

**Veredicto:** APPROVED

## Cobertura del reproduction
- Bug 1 (Race condition): SMS duplicado por ventana pending→sending → cubierto por `test_send_sms_creates_with_sending_status` y `test_send_sms_sync_creates_with_sending_status`
- Bug 2 (Conversación cruzada): Mensajes caían en conversación 'unknown' → cubierto por `test_persist_sms_with_conversation_id`, `test_persist_sms_without_conversation_id` y `test_handle_sms_query_passes_conversation_id_to_send_sms`

## Regresiones
- Tests existentes: todos pasan (84 tests en test_sms_service, test_agent_orchestrator, test_ai_multi_turn, test_ai_multi_turn_integration)
- `./init.ps1`: verde

## Criterios de aceptacion

| Criterio | Estado |
|----------|--------|
| Race condition eliminada: no hay ventana pending→sending en send_sms/send_sms_sync | ✅ |
| conversation_id se propaga desde agent_orchestrator hasta _persist_sms (8 llamadas) | ✅ |
| _persist_sms con conversation_id no crea conversación 'unknown' nueva | ✅ |
| Comportamiento legacy (sin conversation_id) se mantiene | ✅ |
| Tests cubren ambos bugs | ✅ |
| No se tocaron archivos que no debían (sms_send_queue, emergency_mode, password_reset, main) | ✅ |
| 84/84 tests pasan | ✅ |

## Checklist de cambios

### Bug 1 — Race condition (src/sms_service.py)
- [x] `_persist_sms()` acepta parámetro `status` (line 66, default "pending")
- [x] `send_sms()` pasa `status="sending"` a `_persist_sms()` (lines 141-143)
- [x] `send_sms()` YA NO llama `_update_persisted_status(msg_id, "sending")` (confirmado ausente)
- [x] `send_sms_sync()` pasa `status="sending"` a `_persist_sms()` (lines 191-193)
- [x] Mensaje nace como 'sending', nunca pasa por 'pending' — SmsSendQueue no lo roba

### Bug 2 — Conversación cruzada (src/sms_service.py + src/agent_orchestrator.py)
- [x] `_persist_sms()` acepta `conversation_id: int | None = None` (line 65)
- [x] Cuando `conversation_id` no es None, se usa directamente (lines 79-80), sin crear 'unknown'
- [x] `send_sms()` acepta `conversation_id` (line 108) y lo pasa a `_persist_sms()` (line 142)
- [x] `send_sms_sync()` acepta `conversation_id` (line 160) y lo pasa a `_persist_sms()` (line 192)
- [x] agent_orchestrator.py: 8/8 llamadas a `self._sms.send_sms()` pasan `conversation_id=conv.id if conv else None`

### Archivos NO tocados
- [x] src/sms_send_queue.py — no modificado
- [x] src/emergency_mode.py — no modificado
- [x] src/password_reset.py — no modificado
- [x] src/main.py — no modificado

## Cambios requeridos
Ninguno.

## Release
- [x] El fix esta listo para continuar en testing de F28 (ai_multi_turn)
