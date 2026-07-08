## Resumen

Infraestructura de persistencia y despacho de SMS. Crea las tablas `sms_conversations` y `sms_messages` en MariaDB para almacenar todos los SMS entrantes y salientes con estado de envio. Refactoriza IncomingSmsDispatcher para persistir antes de delegar a handlers. Agrega cola de envio asincrona en thread separado. Los handlers de emergencia y password reset se actualizan para usar las nuevas tablas. El dispatcher v2 elimina el catch-all del AI handler.

## Archivos creados

| Archivo | Proposito |
|---------|-----------|
| `database/migrations/2026_07_02_000001_create_sms_conversations.sql` | Tabla sms_conversations |
| `database/migrations/2026_07_02_000002_create_sms_messages.sql` | Tabla sms_messages |
| `src/sms_persistence.py` | SmsPersistenceService (CRUD operaciones) |
| `src/sms_dispatcher_v2.py` | IncomingSmsDispatcherV2 con persistencia |
| `src/sms_send_queue.py` | SmsSendQueue con thread dedicado y 3 reintentos |
| `tests/test_sms_persistence.py` | 14 tests de persistencia |
| `tests/test_sms_send_queue.py` | 8 tests de cola asincrona |
| `tests/test_sms_dispatcher_v2.py` | 9 tests de dispatcher v2 |

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/models.py` | Agregados modelos ORM SmsConversation y SmsMessage |
| `src/sms_service.py` | send_sms() persiste antes de mmcli, send_sms_sync() agregado |
| `src/emergency_mode.py` | Constructor acepta sms_persistence, persistencia en process/activate/deactivate |
| `src/password_reset.py` | Constructor acepta sms_persistence, persistencia en flujo completo |
| `src/main.py` | Registro de SmsPersistenceService, DispatcherV2, SmsSendQueue en startup |
| `tests/*.py` | Tests de persistencia agregados en sms_service, emergency_mode, password_reset |

## Trazabilidad

- R1-R2 (tablas): migraciones + modelos + test_create_conversation/message
- R3-R6 (dispatcher v2): test_persist_before_dispatch, test_unknown_sms_help_response
- R8-R14 (cola asincrona): test_send_queue_processes_pending, test_send_queue_retry
- R15-R20 (emergency + password): tests de persistencia en handlers

## Verificacion

- [x] Backend: ~60 tests nuevos + tests existentes
- [x] Review: APPROVED
- [x] Feature registrada en tracker.json
- [x] feature_list.json status = done
- [x] GitHub issue #20 creado
- [x] Release v1.2.0

## Decisiones tecnicas

- Se uso thread dedicado para cola de envio asincrona (SmsSendQueue) para no bloquear uvicorn ni el watchdog
- Maximo 3 reintentos por SMS, timeout configurable por SMS
- Password reset: valida que sender_phone pertenece a admin, prohibe auto-reset, max 3 intentos fallidos de PIN
- SMS del carrier (TIGO, saldo) se persisten como workflow_type=unknown sin respuesta
- Emergency: conversation_id vinculado a emergency_mode_log.request_id

## Lecciones

- modem_sms_id debia poblarse tanto para entrantes como salientes - se corrigio en sesion posterior (commit 431e56c)
- El dispatcher v1 convive con v2 durante migracion; dispatcher v1 no se inicia en el nuevo startup
- La cola asincrona requiere `_delete_orphan_sms()` para limpiar SMS huerfanos si mmcli --send falla
