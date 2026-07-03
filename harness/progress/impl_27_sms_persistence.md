# Implementacion — Feature 27: sms_persistence

- **Inicio:** 2026-07-02
- **Fin:** 2026-07-02
- **Agente:** implementer (deepseek-v4-pro)
- **Estado:** implementacion completa, esperando reviewer

---

## Resumen

Implementada la infraestructura de persistencia y despacho de SMS segun el spec
aprobado. Se crearon las tablas `sms_conversations` y `sms_messages`, el dispatcher
v2 que persiste antes de delegar, la cola asincrona de envio, y se refactorizaron
los handlers de emergency_mode y password_reset.

---

## Archivos creados

| Archivo | Proposito |
|---------|-----------|
| `database/migrations/2026_07_02_000001_create_sms_conversations.sql` | Migracion tabla sms_conversations |
| `database/migrations/2026_07_02_000002_create_sms_messages.sql` | Migracion tabla sms_messages |
| `src/sms_persistence.py` | SmsPersistenceService con operaciones CRUD |
| `src/sms_dispatcher_v2.py` | IncomingSmsDispatcherV2 con persistencia |
| `src/sms_send_queue.py` | SmsSendQueue con thread dedicado y 3 reintentos |
| `tests/test_sms_persistence.py` | 14 tests de persistencia |
| `tests/test_sms_send_queue.py` | 8 tests de cola asincrona |
| `tests/test_sms_dispatcher_v2.py` | 9 tests de dispatcher v2 |

## Archivos modificados

| Archivo | Cambios |
|---------|---------|
| `src/models.py` | Agregados `SmsConversation` y `SmsMessage` (ORM). Agregados `DateTime`, `JSON` a imports |
| `src/sms_service.py` | `send_sms()` persiste en sms_messages antes de mmcli. Agregado `send_sms_sync()`. Agregado `set_persistence_service()` |
| `src/emergency_mode.py` | Constructor acepta `sms_persistence`. `process_incoming_sms()` persiste SMS entrante y vincula conversacion. `activate()` persiste SMS de confirmacion. `deactivate()` y `extend()` persisten SMS de notificacion |
| `src/password_reset.py` | Constructor acepta `sms_persistence`. `handle_incoming_sms()` valida rol admin y prohibe auto-reset. `generate_and_send_pin()` invalida PIN anterior, persiste SMS. `verify_pin()` trackea intentos fallidos (max 3) |
| `src/main.py` | Importa y registra SmsPersistenceService, IncomingSmsDispatcherV2, SmsSendQueue. Inyecta persistencia en sms_service, EmergencyModeService, PasswordResetService. Handlers registrados con workflow_type. AI handler registrado como `ai_query` explicito (no catch-all). Dispatcher v1 NO se inicia |
| `tests/test_sms_service.py` | Agregados 5 tests de persistencia (TestSMSServicePersistence) |
| `tests/test_emergency_mode.py` | Agregados 4 tests de persistencia (TestEmergencyModePersistence) |
| `tests/test_password_reset.py` | Agregados 7 tests de Feature 27 (TestPasswordResetPersistence) |

---

## Trazabilidad

| Requirement | Tests |
|-------------|-------|
| R1 — Tabla sms_conversations | test_create_conversation (T5), migracion T1 |
| R2 — Tabla sms_messages | test_create_message (T5), migracion T2, modelo T3 |
| R3 — Persistir SMS antes de delegar | test_persist_before_dispatch, test_persist_before_dispatch_message_exists (T9), T4, T8 |
| R4 — Crear conversacion al recibir primer SMS | test_conversation_created_on_first_message (T9), test_get_active_conversation (T5), T4, T8 |
| R5 — No handler catch-all AI | test_no_catchall_ai_handler (T9), T8, T17 |
| R6 — Respuesta de ayuda SMS no reconocido | test_unknown_sms_help_response, test_unknown_sms_conversation_completed (T9), T8 |
| R7 — SMS del carrier | test_carrier_sms_no_response, test_carrier_number_detection (T9), T8 |
| R8 — Cola de envio asincrona | test_send_queue_processes_pending (T7), T6 |
| R9 — Timeout configurable | test_send_queue_timeout_configurable (T7), test_get_pending_messages (T5) |
| R10 — Reintentos de envio (max 3) | test_send_queue_retry_mechanism, test_send_queue_retry_success_after_failure (T7), T6 |
| R11 — Envio no bloqueante | test_send_queue_non_blocking (T7), T6, T11 |
| R12 — Emergency persistencia y vinculacion | test_process_incoming_sms_persists, test_activate_persists_confirmation_sms, test_deactivate_persists_notification_sms, test_extend_persists_notification_sms (T14), T13 |
| R13 — Password reset: validacion rol admin | test_non_admin_rejected, test_unknown_phone_rejected (T16), T15 |
| R14 — Password reset: auto-reset prohibido | test_self_reset_rejected (T16), T15 |
| R15 — Password reset: limite 3 intentos PIN | test_max_pin_attempts_cancels_conversation (T16), T15 |
| R16 — Password reset: nuevo request invalida PIN anterior | test_new_request_invalidates_old_pin (T16), T15 |
| R17 — Auditoria completa | test_pin_sms_persisted (T16), test_send_sms_persists_in_dev_mode, test_send_sms_sync_persists (T12), T4, T10, T15 |
| R18 — Refactor send_sms() persiste | test_update_message_status (T5), test_send_sms_persists_in_dev_mode, test_send_sms_persists_before_mmcli, test_send_sms_sync_persists (T12), T10 |

---

## Impacto en features existentes

### Feature 7 — sms_service
- `send_sms()` ahora persiste en `sms_messages` antes de llamar a mmcli
- Agregado `send_sms_sync()` para compatibilidad
- Agregado `set_persistence_service()` para inyeccion opcional
- **Compatibilidad:** Sin persistencia inyectada, `send_sms()` funciona igual que antes (legacy mode)
- **Tests:** 27/27 tests OK

### Feature 8 — ai_agent
- Handler AI registrado como `ai_query` explicito en dispatcher v2 (no catch-all)
- `agent_orchestrator.handle_sms_query()` NO fue modificado
- Dispatcher v2 persiste SMS antes de delegar al handler AI
- **Tests:** 7/7 tests OK

### Feature 9 — emergency_mode
- `process_incoming_sms()` persiste SMS entrante y crea conversacion emergency
- `activate()`, `deactivate()`, `extend()` persisten SMS de respuesta
- Constructor acepta `sms_persistence` opcional (None = legacy mode)
- `activate()` acepta `conversation_id` opcional para vinculacion
- **Tests:** 63/63 tests OK

### Feature 10 — backup_system
- Sin cambios directos. `send_sms()` usado por backups ahora persiste (transparente)
- **Tests:** No ejecutados (fuera del alcance de regresion del spec)

### Feature 12 — password_reset_sms
- `handle_incoming_sms()` valida rol admin y prohibe auto-reset
- `generate_and_send_pin()` invalida PIN anterior, persiste SMS
- `verify_pin()` trackea intentos fallidos (max 3)
- **Tests:** 56/56 tests OK

### Feature 13 — frontend_login_kiosk
- Sin cambios en frontend. API de emergencia mantiene misma interfaz
- **Tests:** No ejecutados (no hay cambios de codigo)

### Feature 26 — emergency_request_wrong_sms (bug)
- Bug resuelto: AI handler ya no es catch-all. SMS no reconocidos reciben ayuda en vez de caer al AI
- Handler `ai_query` registrado explicitamente con `workflow_type='ai_query'`

---

## Decisiones tecnicas

1. **Columna `metadata` renombrada a `conv_metadata`:** SQLAlchemy reserva `metadata` como atributo de clase. Se uso `conv_metadata = Column("metadata", JSON)` para mapear a la columna DB `metadata`.

2. **`send_sms()` backward-compatible:** Si `SmsPersistenceService` no esta inyectado, `send_sms()` funciona en modo legacy (sin persistencia). Esto permite transicion gradual.

3. **Dispatcher v1 NO se inicia:** `IncomingSmsDispatcher` (v1) se mantiene en codigo por referencias de tests pero no se instancia en `main.py`. El dispatcher v2 reemplaza completamente al v1.

4. **PIN attempts en metadata:** El contador de intentos fallidos de PIN se almacena en `sms_conversations.conv_metadata` como JSON `{"pin_attempts": N}`. Al alcanzar 3, se invalida el PIN y se marca la conversacion como `cancelled`.

5. **Verificacion de tests:** Todos los tests unitarios y de regresion pasan (31 nuevos + 153 de regresion).

---

## Verificacion

```bash
docker compose exec backend python -m unittest discover -s tests -p "test_sms*.py" -q
# Resultado: Ran 72 tests in 6.341s — OK

docker compose exec backend python -m unittest tests.test_emergency_mode -q
# Resultado: Ran 63 tests in 35.120s — OK

docker compose exec backend python -m unittest tests.test_password_reset -q
# Resultado: Ran 56 tests in 33.977s — OK

docker compose exec backend python -m unittest tests.test_agent_orchestrator -q
# Resultado: Ran 7 tests — OK
```
