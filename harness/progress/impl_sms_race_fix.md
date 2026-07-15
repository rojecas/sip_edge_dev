# Implementación — Fix SMS Race Condition + Conversación Cruzada

> Sesión: 2026-07-15
> Feature: F28 (ai_multi_turn) — debugging durante fase testing
> Prompt: `plan-bug-sms_duplicate_race.md` (inline en prompt del leader)

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/sms_service.py` | `_persist_sms()`: añade `conversation_id` y `status` params. Si `conversation_id != None`, usa la conversación directamente. Usa `status` en vez de hardcoded `"pending"`. |
| `src/sms_service.py` | `send_sms()`: añade `conversation_id` param. Pasa `status='sending'` a `_persist_sms()`. Elimina `_update_persisted_status(msg_id, "sending")` (ya no necesario — el mensaje nace como `sending`). |
| `src/sms_service.py` | `send_sms_sync()`: añade `conversation_id` param. Pasa `status='sending'` a `_persist_sms()`. |
| `src/agent_orchestrator.py` | 8 llamadas a `self._sms.send_sms()`: añadido `conversation_id=conv.id if conv else None` en todas. |
| `tests/test_sms_service.py` | Reemplaza test Bug #26 obsoleto (`test_send_sms_with_persistence_does_not_call_mmcli_directly`) por `test_send_sms_creates_with_sending_status`. Añade 3 tests nuevos: `test_persist_sms_with_conversation_id`, `test_persist_sms_without_conversation_id`, `test_send_sms_sync_creates_with_sending_status`. |
| `tests/test_agent_orchestrator.py` | Añade `test_handle_sms_query_passes_conversation_id_to_send_sms`. |

## Archivos NO tocados (como especificado)

| Archivo | Razón |
|---------|-------|
| `src/sms_send_queue.py` | La cola sigue buscando `status='pending'`. Como `send_sms()` ahora crea con `'sending'`, la cola nunca ve esos mensajes. |
| `src/emergency_mode.py` | Ya gestiona conversaciones manualmente. |
| `src/password_reset.py` | Sin cambios necesarios. |
| `src/main.py` | El lambda ya pasa `conversation_id` al handler, no a `send_sms`. |

## Trazabilidad de tests

### Bug 1: Race condition → SMS duplicado

| Test | Verifica |
|------|----------|
| `test_send_sms_creates_with_sending_status` | `send_sms()` crea el mensaje con `status='sending'`, NO `'pending'`. Así SmsSendQueue nunca lo roba. |
| `test_send_sms_sync_creates_with_sending_status` | `send_sms_sync()` también crea con `status='sending'`. |

### Bug 2: Conversación cruzada

| Test | Verifica |
|------|----------|
| `test_persist_sms_with_conversation_id` | `_persist_sms(conversation_id=42)` usa esa conversación y NO crea `'unknown'`. |
| `test_persist_sms_without_conversation_id` | `_persist_sms()` sin `conversation_id` mantiene comportamiento legacy (busca/crea `'unknown'`). |
| `test_handle_sms_query_passes_conversation_id_to_send_sms` | `handle_sms_query()` pasa `conversation_id` de la conversación `ai_query` activa a `send_sms()`. |

### Tests de regresión (pasan sin cambios)

- Todos los tests existentes de `TestSMSServicePersistence`, `TestSMSServiceProdMode`, `TestSMSServiceErrorHandling`, `TestSMSServiceDryRun`, `TestSchedulerBehavior`, `TestSMSServiceModemSmsId`.
- Todos los tests existentes de `TestHandleAnomaly`, `TestHandleSmsQuery`, `TestHandleSmsQueryMultiTurn`, `TestAgentOrchestratorConstruction`.
- Todos los tests de `TestAiMultiTurnService` y `TestFullConversationFlow`.

## Resultado de verificación

```bash
$ docker compose exec backend python -m unittest tests.test_sms_service tests.test_agent_orchestrator tests.test_ai_multi_turn tests.test_ai_multi_turn_integration -v
Ran 84 tests in 1.417s
OK
```

84/84 tests pasan. Cero fallos. Cero regresiones.

## Resumen de cambios

- **Race condition:** `send_sms()` y `send_sms_sync()` ahora crean mensajes directamente como `'sending'`. La cola (`SmsSendQueue`) solo busca `'pending'`, así que nunca los toca. No hay ventana de race.
- **Conversación cruzada:** `send_sms()` y `send_sms_sync()` aceptan `conversation_id` explícito. El `agent_orchestrator` pasa el `conv.id` de la conversación `ai_query` activa. Los mensajes enviados caen en la conversación correcta, no en una nueva `'unknown'`.
