# Tasks â€” SMS Persistence, Dispatcher v2 y Cola Asincrona

> Checklist ejecutable para el implementer.

---

## Fase 1 â€” Migraciones y Modelos

- [x] T1 â€” Crear migraciÃ³n `database/migrations/2026_07_02_000001_create_sms_conversations.sql` con la tabla `sms_conversations` segÃºn R1. Cubre: R1.
- [x] T2 â€” Crear migraciÃ³n `database/migrations/2026_07_02_000002_create_sms_messages.sql` con la tabla `sms_messages` segÃºn R2. Cubre: R2.
- [x] T3 â€” Agregar modelos ORM `SmsConversation` y `SmsMessage` en `src/models.py` con columnas, tipos, FK e Ã­ndices segÃºn R1 y R2. Cubre: R1, R2.
- [x] T4 â€” Crear `src/sms_persistence.py` con la clase `SmsPersistenceService` y los mÃ©todos CRUD: `create_conversation`, `get_or_create_active_conversation`, `update_conversation_status`, `update_conversation_last_activity`, `create_message`, `update_message_status`, `get_pending_outgoing_messages`, `get_active_conversation_by_peer`, `get_conversation_by_request_id`. Cubre: R3, R4, R12, R17, R18.
- [x] T5 â€” Escribir tests de `src/sms_persistence.py` en `tests/test_sms_persistence.py`:
  - `test_create_conversation` â€” crear y leer conversaciÃ³n. Cubre: R1.
  - `test_create_message` â€” crear y leer mensaje. Cubre: R2.
  - `test_get_active_conversation` â€” recuperar conversaciÃ³n activa por peer+type. Cubre: R4.
  - `test_get_pending_messages` â€” recuperar mensajes pendientes de envÃ­o. Cubre: R9.
  - `test_update_message_status` â€” actualizar status y error_message. Cubre: R18.

## Fase 2 â€” Cola de EnvÃ­o AsÃ­ncrona

- [x] T6 â€” Crear `src/sms_send_queue.py` con la clase `SmsSendQueue` que implementa:
  - Thread dedicado con `queue.Queue` para mensajes pendientes.
  - Polling periÃ³dico de `sms_messages` con `status='pending'`.
  - Llamada a mmcli con timeout configurable (default 20s).
  - Hasta 3 reintentos por mensaje, luego status='failed'.
  - No bloquea el event loop de uvicorn.
  Cubre: R8, R9, R10, R11.
- [x] T7 â€” Escribir tests de `src/sms_send_queue.py` en `tests/test_sms_send_queue.py`:
  - `test_send_queue_processes_pending` â€” encolar y verificar procesamiento. Cubre: R8.
  - `test_send_queue_retry_mechanism` â€” simular fallo y verificar 3 reintentos. Cubre: R10.
  - `test_send_queue_timeout_configurable` â€” verificar timeout configurable. Cubre: R9.
  - `test_send_queue_non_blocking` â€” verificar que no bloquea el hilo principal. Cubre: R11.

## Fase 3 â€” Dispatcher v2

- [x] T8 â€” Crear `src/sms_dispatcher_v2.py` con la clase `IncomingSmsDispatcherV2` que:
  - Recibe SMS entrantes (mmcli o cola dev).
  - Persiste el SMS en `sms_messages` ANTES de delegar (R3).
  - Crea conversaciÃ³n si no existe (R4).
  - Delega a handlers registrados con `workflow_type`.
  - Si ningÃºn handler retorna True, responde con texto de ayuda (R6).
  - Identifica SMS de carrier (nÃºmeros cortos < 6 dÃ­gitos) y los persiste como unknown/completed sin respuesta (R7).
  - NO tiene handler catch-all de AI (R5).
  Cubre: R3, R4, R5, R6, R7.
- [x] T9 â€” Escribir tests de `src/sms_dispatcher_v2.py` en `tests/test_sms_dispatcher_v2.py`:
  - `test_persist_before_dispatch` â€” verificar que el SMS estÃ¡ en BD antes de llamar al handler. Cubre: R3.
  - `test_unknown_sms_help_response` â€” SMS no reconocido recibe texto de ayuda. Cubre: R6.
  - `test_carrier_sms_no_response` â€” SMS de carrier se persiste sin respuesta. Cubre: R7.
  - `test_no_catchall_ai_handler` â€” verificar que NO hay handler catch-all de AI. Cubre: R5.
  - `test_conversation_created_on_first_message` â€” primer SMS crea conversaciÃ³n. Cubre: R4.

## Fase 4 â€” Refactor de sms_service.send_sms()

- [x] T10 â€” Modificar `src/sms_service.py` mÃ©todo `send_sms()` para persistir en `sms_messages` con `direction='sent'` y `status='pending'` ANTES de ejecutar mmcli. Actualizar status a 'sent' o 'failed' tras el resultado. Cubre: R18.
- [x] T11 â€” Modificar `src/sms_service.py` para que `_send_via_mmcli_sync()` sea invocable desde la cola asÃ­ncrona. La cola asÃ­ncrona (SmsSendQueue) reemplaza la ejecuciÃ³n directa. Cubre: R8, R11.
- [x] T12 â€” Actualizar tests de `test_sms_service.py` para verificar persistencia de mensajes enviados. Cubre: R18.

## Fase 5 â€” Refactor de emergency_mode

- [x] T13 â€” Modificar `emergency_mode.py`:
  - `process_incoming_sms()`: persistir SMS entrante en `sms_messages` y conversaciÃ³n en `sms_conversations` con workflow_type='emergency'. Vincular conversation_id a emergency_mode_log.request_id.
  - `create_request()`: persistir SMS enviado al supervisor en `sms_messages`.
  - `activate()`: persistir SMS de confirmaciÃ³n enviado en `sms_messages`.
  - `deactivate()`: persistir SMS de notificaciÃ³n en `sms_messages`.
  - `extend()`: persistir SMS de notificaciÃ³n en `sms_messages`.
  Cubre: R12.
- [x] T14 â€” Actualizar tests de `test_emergency_mode.py` para verificar persistencia SMS en cada acciÃ³n. Cubre: R12.

## Fase 6 â€” Refactor de password_reset

- [x] T15 â€” Modificar `password_reset.py`:
  - `handle_incoming_sms()`: validar que `sender_phone` pertenece a usuario con rol admin. Si no, responder error y retornar True. Persistir SMS en sms_messages.
  - Validar que el admin no solicita reset de su propia contraseÃ±a. Si lo hace, rechazar.
  - `generate_and_send_pin()`: si existe un PIN activo para el mismo usuario, invalidar conversaciÃ³n anterior (cancelled), crear nueva conversaciÃ³n, notificar al remitente.
  - Agregar contador de intentos fallidos de PIN por conversaciÃ³n (almacenado en metadata de sms_conversations). Al alcanzar 3, invalidar PIN y marcar conversaciÃ³n como cancelled.
  Cubre: R13, R14, R15, R16.
- [x] T16 â€” Escribir/actualizar tests de `test_password_reset.py`:
  - `test_non_admin_rejected` â€” remitente no admin recibe error. Cubre: R13.
  - `test_self_reset_rejected` â€” admin no puede resetear su propia contraseÃ±a. Cubre: R14.
  - `test_max_pin_attempts` â€” 3 intentos fallidos cancela conversaciÃ³n. Cubre: R15.
  - `test_new_request_invalidates_old_pin` â€” nuevo PIN invalida el anterior. Cubre: R16.
  - `test_pin_sms_persisted` â€” SMS de PIN se persiste en sms_messages. Cubre: R17.

## Fase 7 â€” IntegraciÃ³n en main.py

- [x] T17 â€” Modificar `src/main.py`:
  - Importar y registrar `SmsPersistenceService`, `IncomingSmsDispatcherV2`, `SmsSendQueue`.
  - En `lifespan()`, crear servicios en orden: persistence â†’ sms_service â†’ send_queue â†’ dispatcher_v2.
  - Registrar handlers en dispatcher_v2: emergency (workflow_type='emergency'), password_reset (workflow_type='password_reset').
  - Registrar handler ai_query explicito (workflow_type='ai_query') en vez del catch-all. El handler ai_query persiste el SMS, llama al LLM, y persiste la respuesta. Si el LLM falla, status='failed' sin reintentar.
  - Iniciar send_queue.start() y dispatcher_v2.start().
  - NO iniciar el dispatcher v1 (IncomingSmsDispatcher del mÃ³dulo sms_incoming.py).
  Cubre: R5.
- [x] T18 â€” Verificar que `./init.ps1` pasa con todos los bloques [OK]. Cubre: R1-R18.

- [x] T19 — Ejecutar tests de regresion en features afectadas:
  - tests/test_sms_service.py — Feature 7
  - tests/test_emergency_mode.py — Feature 9
  - tests/test_password_reset.py — Feature 12
  - tests/test_agent_orchestrator.py — Feature 8
  - tests/test_backup.py — Feature 10
  Cubre: Regresion en Features 7, 8, 9, 10, 12, 13, 26.




## Trazabilidad (documentar en progress/impl_27_sms_persistence.md)

El implementer DEBE documentar en `progress/impl_27_sms_persistence.md`:

```markdown
## Trazabilidad
- R1 â†’ test_create_conversation, migraciÃ³n T1
- R2 â†’ test_create_message, migraciÃ³n T2, modelo T3
- R3 â†’ test_persist_before_dispatch, T4, T8
- R4 â†’ test_conversation_created_on_first_message, T4, T8
- R5 â†’ test_no_catchall_ai_handler, T8, T17
- R6 â†’ test_unknown_sms_help_response, T8
- R7 â†’ test_carrier_sms_no_response, T8
- R8 â†’ test_send_queue_processes_pending, T6
- R9 â†’ test_send_queue_timeout_configurable, T6
- R10 â†’ test_send_queue_retry_mechanism, T6
- R11 â†’ test_send_queue_non_blocking, T6, T11
- R12 â†’ process_incoming_sms persiste, T13, T14
- R13 â†’ test_non_admin_rejected, T15
- R14 â†’ test_self_reset_rejected, T15
- R15 â†’ test_max_pin_attempts, T15
- R16 â†’ test_new_request_invalidates_old_pin, T15
- R17 â†’ test_pin_sms_persisted, T4, T10, T15
- R18 â†’ sms_service.send_sms persiste, T10, T12
```









