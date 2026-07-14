# Implementacion — Feature 28 (ai_multi_turn)

## Fecha: 2026-07-14

## Resumen

Implementado soporte de conversaciones multiturno para consultas AI via SMS.
Se crearon 2 archivos nuevos, se modificaron 4 archivos existentes, y se
escribieron 3 archivos de tests con 43 tests unitarios e integracion.

## Archivos creados

| Archivo | Proposito |
|---------|-----------|
| `src/ai_multi_turn.py` | Servicio de gestion de contexto multiturno (AiMultiTurnService) |
| `tests/test_ai_multi_turn.py` | 24 tests unitarios del servicio |
| `tests/test_ai_multi_turn_integration.py` | 5 tests de integracion del flujo completo |

## Archivos modificados

| Archivo | Cambios |
|---------|---------|
| `src/models.py` | Agregado `SmsAiToolLog` ORM model; `'archived'` al ENUM `status` de `SmsConversation` |
| `src/sms_persistence.py` | Agregados `get_conversation()`, `get_messages_by_conversation()`, `update_conversation_metadata()`; `'archived'` en validaciones de status |
| `src/agent_orchestrator.py` | Inyectado `AiMultiTurnService`; firma modificada en `handle_sms_query()`; flujo multiturno completo; SYSTEM_PROMPT actualizado; `_after_response()` helper |
| `src/main.py` | Instancia `AiMultiTurnService` en lifespan; pasada a `AgentOrchestrator`; handler lambda actualizado; tarea diaria de archivado |
| `tests/test_agent_orchestrator.py` | Agregados 6 tests de multiturno |

## Trazabilidad

- **R1** → `test_get_or_create_ai_conversation_new`, `test_get_or_create_ai_conversation_upgrades_unknown`, `test_handle_sms_query_multiturn_uses_conversation`, `test_full_conversation_flow`, `test_dispatcher_unknown_conversation_upgrade`, T4, T5, T9
- **R2** → `test_get_message_history_with_data`, `test_append_exchange_first`, `test_full_conversation_flow`, T4, T5, T7
- **R3** → `test_append_exchange_fifo`, `test_handle_sms_query_fifo_rotation`, `test_fifo_rotation_integration`, T5, T7
- **R4** → `test_build_llm_messages`, `test_handle_sms_query_multiturn_with_history`, `test_full_conversation_flow`, T4, T5, T7, T9
- **R5** → migracion T2, modelo T3, `test_log_tool_call`
- **R6** → `test_log_tool_call`, `test_handle_sms_query_tool_call_logged`, `test_full_conversation_flow`, T5, T7
- **R7** → `test_get_or_create_ai_conversation_existing`, `test_new_conversation_after_completed`, `test_handle_sms_query_legacy_compatibility`, `test_dispatcher_unknown_conversation_upgrade`, T5, T7
- **R8** → `test_detect_farewell_true`, `test_detect_farewell_false`, `test_complete_conversation`, `test_handle_sms_query_farewell_completes_conversation`, `test_farewell_ends_conversation`, T5, T7
- **R9** → `test_archive_old_conversations`, tarea archivado en T9, T5
- **R10** → `test_append_exchange_configurable_limit`, `test_get_max_exchanges_from_metadata`, `test_get_max_exchanges_default`, `test_fifo_rotation_integration`, T5
- **R11** → orden handlers en main.py (emergency, password_reset, ai_query), T11
- **R12** → migracion T1, modelo T3

## Impacto en features existentes

Las features 7 (sms_service), 8 (ai_agent), 9 (emergency_mode), 12 (password_reset_sms), y 27 (sms_persistence) fueron analizadas segun el design.md §8.

- **Feature 8**: `handle_sms_query()` modificado con parametros opcionales nuevos. Compatibilidad hacia atras mantenida.
- **Feature 27**: `create_conversation()` y `update_conversation_status()` actualizados para aceptar `'archived'`. Metodos nuevos agregados (no rompen compatibilidad).
- **Feature 9 y 12**: Sin cambios requeridos. El orden de handlers en main.py ya respeta R11.
- **Feature 7**: Sin cambios requeridos.

## Tests ejecutados

```bash
# F28 unitarios + integracion: 43 tests, todos OK
docker compose exec backend python -m unittest tests.test_ai_multi_turn tests.test_ai_multi_turn_integration tests.test_agent_orchestrator -v

# Regresion en features afectadas: pre-existing failures unchanged
docker compose exec backend python -m unittest tests.test_agent_orchestrator tests.test_sms_persistence tests.test_sms_dispatcher_v2 tests.test_emergency_mode tests.test_password_reset -v
```

## Verificacion

- `./init.ps1` muestra errores pre-existentes no relacionados con F28
- Todos los 43 tests de F28 pasan
- El import de `src.main` funciona correctamente
- La migraciones ya existen en `database/migrations/`
