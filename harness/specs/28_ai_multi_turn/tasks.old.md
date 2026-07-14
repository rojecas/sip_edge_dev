# Tasks — Conversación Multiturno para Consultas AI via SMS

> Checklist ejecutable para el implementer.
> Cada task referencia al menos un R<n>.

---

## Fase 1 — Migraciones y Modelos

- [ ] T1 — Crear migración `database/migrations/2026_07_14_000001_add_archived_to_sms_conversations.sql` que ALTER TABLE sms_conversations MODIFY COLUMN status para agregar 'archived' al ENUM. Cubre: R12.

- [ ] T2 — Crear migración `database/migrations/2026_07_14_000002_create_sms_ai_tool_log.sql` con la tabla `sms_ai_tool_log` según R5. Cubre: R5.

- [ ] T3 — Agregar modelo ORM `SmsAiToolLog` en `src/models.py` con columnas, FK e índices según R5. Agregar `'archived'` al ENUM `status` de `SmsConversation`. Cubre: R5, R12.

- [ ] T4 — Agregar métodos en `src/sms_persistence.py`:
  - `get_conversation(conversation_id) -> SmsConversation | None`
  - `get_messages_by_conversation(conversation_id, limit=50) -> list[SmsMessage]`
  - `update_conversation_metadata(conversation_id, metadata) -> None`
  Cubre: R1, R2, R4.

## Fase 2 — AiMultiTurnService

- [ ] T5 — Crear `src/ai_multi_turn.py` con la clase `AiMultiTurnService` y los siguientes métodos:
  - `__init__(db_session_factory, persistence)`
  - `get_or_create_ai_conversation(peer_number) -> SmsConversation`
  - `get_message_history(conversation) -> list[dict]`
  - `build_llm_messages(message_history, new_user_text, system_prompt) -> list[dict]`
  - `append_exchange(conversation_id, message_history, user_text, assistant_text, max_exchanges=10) -> None`
  - `log_tool_call(conversation_id, incoming_msg_id, tool_name, tool_args, tool_result, duration_ms) -> None`
  - `detect_farewell(text) -> bool`
  - `complete_conversation(conversation_id) -> None`
  - `archive_old_conversations() -> int`
  - `get_max_exchanges(conversation) -> int`
  - Definir la excepción `AiMultiTurnError`.
  - Definir `FAREWELL_PATTERNS` como constante de módulo.
  Cubre: R1, R2, R3, R4, R6, R7, R8, R9, R10.

- [ ] T6 — Escribir tests unitarios de `src/ai_multi_turn.py` en `tests/test_ai_multi_turn.py`:
  - `test_get_or_create_ai_conversation_new` — crea conversación si no existe. Cubre: R1, R7.
  - `test_get_or_create_ai_conversation_existing` — reusa conversación activa existente. Cubre: R7.
  - `test_get_message_history_empty` — historial vacío cuando no hay metadata. Cubre: R2.
  - `test_get_message_history_with_data` — recupera historial existente. Cubre: R2.
  - `test_append_exchange_first` — agrega primer exchange. Cubre: R2.
  - `test_append_exchange_fifo` — al llegar al límite, elimina el más antiguo. Cubre: R3.
  - `test_append_exchange_configurable_limit` — respeta max_exchanges desde metadata. Cubre: R10.
  - `test_build_llm_messages` — construye arreglo correcto con system + history + user. Cubre: R4.
  - `test_log_tool_call` — registra tool_call en sms_ai_tool_log con todos los campos. Cubre: R6.
  - `test_detect_farewell_true` — detecta "gracias", "bye", "eso es todo". Cubre: R8.
  - `test_detect_farewell_false` — no detecta despedida en consulta normal. Cubre: R8.
  - `test_complete_conversation` — marca conversación como completed. Cubre: R8.
  - `test_archive_old_conversations` — archiva conversaciones > 90 días. Cubre: R9.
  - `test_get_max_exchanges_default` — retorna 10 si no hay clave en metadata. Cubre: R10.
  - `test_get_max_exchanges_from_metadata` — retorna valor de metadata si existe. Cubre: R10.

## Fase 3 — Refactor de AgentOrchestrator

- [ ] T7 — Modificar `src/agent_orchestrator.py`:
  - Inyectar `AiMultiTurnService` en `__init__`.
  - Modificar firma de `handle_sms_query()` para aceptar `message_id: int | None = None` y `conversation_id: int | None = None`.
  - Implementar el nuevo flujo multiturno según §11 de design.md:
    1. Obtener/crear conversación ai_query vía AiMultiTurnService.
    2. Recuperar message_history.
    3. Construir mensajes LLM con historial completo.
    4. Ejecutar tools, loggear en sms_ai_tool_log.
    5. Append exchange al historial.
    6. Detectar despedida y completar conversación si aplica.
  - Actualizar SYSTEM_PROMPT para incluir instrucciones de detección de despedida y contexto multiturno.
  - Mantener compatibilidad hacia atrás: si `message_id` es None, funcionar sin logging en tool_log.
  Cubre: R1, R2, R3, R4, R6, R7, R8, R10.

- [ ] T8 — Actualizar tests de `tests/test_agent_orchestrator.py`:
  - `test_handle_sms_query_multiturn_uses_conversation` — verifica que se crea/usa conversación ai_query. Cubre: R1.
  - `test_handle_sms_query_multiturn_with_history` — envía historial completo al LLM. Cubre: R4.
  - `test_handle_sms_query_farewell_completes_conversation` — despedida marca completed. Cubre: R8.
  - `test_handle_sms_query_tool_call_logged` — tool_calls se registran en sms_ai_tool_log. Cubre: R6.
  - `test_handle_sms_query_fifo_rotation` — múltiples exchanges rotan FIFO. Cubre: R3.
  - `test_handle_sms_query_legacy_compatibility` — sin message_id funciona sin tool_log. Cubre: R7.
  Cubre adicional: R2, R10.

## Fase 4 — Integración en main.py

- [ ] T9 — Modificar `src/main.py`:
  - Importar `AiMultiTurnService`.
  - Crear instancia de `AiMultiTurnService` en lifespan (después de SmsPersistenceService).
  - Inyectar `ai_multi_turn_service` en `AgentOrchestrator.__init__`.
  - Actualizar handler lambda AI para pasar `message_id` y `conversation_id`:
    ```python
    lambda phone, text, message_id=None, conversation_id=None:
        app.state.agent_orchestrator.handle_sms_query(
            phone, text, message_id, conversation_id,
        )
    ```
  - Iniciar tarea asyncio de archivado diario.
  Cubre: R1, R4, R9.

- [ ] T10 — Escribir test de integración en `tests/test_ai_multi_turn_integration.py`:
  - `test_full_conversation_flow` — 3 rounds de preguntas, verificar historial crece, tool_calls se loggean. Cubre: R1, R2, R4, R6.
  - `test_farewell_ends_conversation` — enviar "gracias" completa la conversación. Cubre: R8.
  - `test_fifo_rotation_integration` — enviar 11 mensajes, verificar solo 10 exchanges en historial. Cubre: R3, R10.
  - `test_new_conversation_after_completed` — después de despedida, nuevo mensaje crea nueva conversación. Cubre: R7.

## Fase 5 — Verificación y Regresión

- [ ] T11 — Verificar que los handlers de emergency y password_reset tienen prioridad:
  - Confirmar que el orden de registro en main.py es: 1. emergency, 2. password_reset, 3. ai_query.
  - Verificar que el dispatcher no cambia de orden.
  - Test: enviar "manual on" desde número con conversación ai_query activa → se procesa como emergencia.
  Cubre: R11.

- [ ] T12 — Ejecutar tests de regresión en features afectadas:
  ```bash
  docker compose exec backend python -m unittest tests.test_agent_orchestrator -v
  docker compose exec backend python -m unittest tests.test_sms_persistence -v
  docker compose exec backend python -m unittest tests.test_sms_dispatcher_v2 -v
  docker compose exec backend python -m unittest tests.test_emergency_mode -v
  docker compose exec backend python -m unittest tests.test_password_reset -v
  ```
  Cubre: Regresión en Features 7, 8, 9, 12, 27.

- [ ] T13 — Verificar `./init.ps1` pasa con todos los bloques [OK].
  Cubre: R1-R12.

## Trazabilidad (documentar en progress/impl_28_ai_multi_turn.md)

El implementer DEBE documentar en `progress/impl_28_ai_multi_turn.md`:

```markdown
## Trazabilidad
- R1 → test_handle_sms_query_multiturn_uses_conversation, T5, T7, T9
- R2 → test_get_message_history_with_data, test_append_exchange_first, T5, T7
- R3 → test_append_exchange_fifo, test_handle_sms_query_fifo_rotation, T5, T7
- R4 → test_build_llm_messages, test_handle_sms_query_multiturn_with_history, T5, T7
- R5 → migración T2, modelo T3, test_log_tool_call T6
- R6 → test_log_tool_call, test_handle_sms_query_tool_call_logged, T5, T7
- R7 → test_get_or_create_ai_conversation_existing, test_new_conversation_after_completed, T5, T7
- R8 → test_detect_farewell_true, test_farewell_ends_conversation, T5, T7
- R9 → test_archive_old_conversations, tarea archivado T9, T5
- R10 → test_append_exchange_configurable_limit, test_get_max_exchanges_from_metadata, T5
- R11 → orden handlers en main.py, test T11
- R12 → migración T1, modelo T3
```
