# Design Document â€” SMS Persistence, Dispatcher v2 y Cola Asincrona

> Feature 27 â€” Decisiones tÃ©cnicas antes de implementar.

---

## 1. Resumen

Esta feature introduce persistencia en MariaDB para todos los SMS (entrantes y salientes),
un nuevo dispatcher que persiste antes de delegar, y una cola de envÃ­o asÃ­ncrona en thread
separado que elimina el bloqueo de uvicorn. Los handlers de emergency_mode y password_reset
se refactorizan para usar las nuevas tablas.

---

## 2. Archivos a crear

| Archivo | PropÃ³sito |
|---------|-----------|
| `database/migrations/2026_07_02_000001_create_sms_conversations.sql` | MigraciÃ³n tabla `sms_conversations` |
| `database/migrations/2026_07_02_000002_create_sms_messages.sql` | MigraciÃ³n tabla `sms_messages` |
| `src/sms_persistence.py` | Capa de persistencia: operaciones CRUD para sms_conversations y sms_messages |
| `src/sms_dispatcher_v2.py` | Nuevo dispatcher (IncomingSmsDispatcherV2) que persiste antes de delegar |
| `src/sms_send_queue.py` | Cola de envÃ­o asÃ­ncrona en thread separado |

---

## 3. Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `src/models.py` | Agregar modelos ORM `SmsConversation` y `SmsMessage` |
| `src/sms_incoming.py` | Refactorizar `IncomingSmsDispatcher` â†’ marcado como deprecated; la lÃ³gica migra a `sms_dispatcher_v2.py`. Se mantiene por compatibilidad temporal |
| `src/sms_service.py` | `send_sms()` persiste en `sms_messages` antes de mmcli; actualiza status tras resultado |
| `src/emergency_mode.py` | `process_incoming_sms()` usa `sms_persistence` para persistir; `create_request()` persiste SMS de respuesta; `activate()`/`deactivate()`/`extend()` registran SMS enviados |
| `src/password_reset.py` | `handle_incoming_sms()` valida rol admin, no auto-reset; `generate_and_send_pin()` persiste; integra lÃ­mite de 3 intentos PIN; invalida PIN anterior en nuevo request |
| `src/main.py` | Registrar nuevos servicios en `lifespan`: `SmsPersistenceService`, `IncomingSmsDispatcherV2`, `SmsSendQueue`. Orden de handlers: emergency â†’ password_reset â†’ dispatcher v2 (unknown). Eliminar registro del AI handler catch-all |

---

## 4. Firmas nuevas

### `src/sms_persistence.py`

```python
class SmsPersistenceService:
    def __init__(self, db_session_factory) -> None

    def create_conversation(
        self, peer_number: str, workflow_type: str,
        status: str = "active", metadata: dict | None = None,
        expires_at: datetime | None = None,
    ) -> SmsConversation

    def get_or_create_active_conversation(
        self, peer_number: str, workflow_type: str,
    ) -> SmsConversation

    def update_conversation_status(
        self, conversation_id: int, status: str,
    ) -> None

    def update_conversation_last_activity(
        self, conversation_id: int,
    ) -> None

    def create_message(
        self, conversation_id: int, direction: str,
        peer_number: str, body: str,
        handler: str | None = None,
        status: str = "pending",
    ) -> SmsMessage

    def update_message_status(
        self, message_id: int, status: str,
        error_message: str | None = None,
        modem_sms_id: int | None = None,
    ) -> None

    def get_pending_outgoing_messages(
        self, limit: int = 10,
    ) -> list[SmsMessage]

    def get_active_conversation_by_peer(
        self, peer_number: str, workflow_type: str,
    ) -> SmsConversation | None

    def get_conversation_by_request_id(
        self, request_id: int,
    ) -> SmsConversation | None
```

### `src/sms_dispatcher_v2.py`

```python
class IncomingSmsDispatcherV2:
    def __init__(
        self, modem_index: int, dev_mode: bool,
        persistence: SmsPersistenceService,
    ) -> None

    def register_handler(self, handler: SmsHandler,
                         workflow_type: str) -> None
    def enqueue_incoming_sms(self, sender_phone: str, text: str) -> None
    async def start(self) -> None
    async def stop(self) -> None

    # Nuevo: handler catch-all para unknown / carrier
    # Se registra automÃ¡ticamente al crear el dispatcher
```

Diferencias con v1:
- `register_handler` ahora requiere `workflow_type` (str).
- El handler catch-all es interno, NO delegable.
- El dispatcher persiste el SMS antes de llamar handlers.

### `src/sms_send_queue.py`

```python
class SmsSendQueue:
    def __init__(
        self, persistence: SmsPersistenceService,
        sms_service, modem_index: int,
        timeout_seconds: int = 20,
        poll_interval: float = 2.0,
    ) -> None

    def start(self) -> None
    def stop(self) -> None
    def enqueue(self, message_id: int) -> None

    # Internals
    def _worker_loop(self) -> None
    def _send_with_retry(self, msg: SmsMessage) -> bool
```

### Modelos nuevos en `src/models.py`

```python
class SmsConversation(Base):
    __tablename__ = "sms_conversations"
    # Columnas segÃºn R1

class SmsMessage(Base):
    __tablename__ = "sms_messages"
    # Columnas segÃºn R2
```

---

## 5. Excepciones nuevas

| ExcepciÃ³n | MÃ³dulo | PropÃ³sito |
|-----------|--------|-----------|
| `SmsPersistenceError` | `src/sms_persistence.py` | Error base de operaciones de persistencia SMS |
| `SmsSendQueueError` | `src/sms_send_queue.py` | Error de la cola de envÃ­o asÃ­ncrona |

---

## 6. Persistencia

### Tabla nueva: `sms_conversations`

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK |
| peer_number | VARCHAR(20) | NO | | NÃºmero de la contraparte |
| workflow_type | ENUM('emergency','password_reset','ai_query','unknown') | NO | | Tipo de flujo |
| status | ENUM('active','completed','expired','cancelled','failed') | NO | 'active' | Estado de la conversaciÃ³n |
| started_at | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) | Inicio |
| last_activity | DATETIME(3) | NO | | Ãšltima actividad |
| expires_at | DATETIME(3) | YES | NULL | ExpiraciÃ³n programada |
| metadata | JSON | YES | NULL | Datos adicionales (conversaciÃ³n) |

Ãndices:
- `idx_peer_status` ON `(peer_number, status)`
- `idx_expires` ON `(status, expires_at)`

### Tabla nueva: `sms_messages`

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK |
| conversation_id | BIGINT UNSIGNED | NO | | FK â†’ sms_conversations.id |
| direction | ENUM('sent','received') | NO | | DirecciÃ³n |
| peer_number | VARCHAR(20) | NO | | NÃºmero remoto |
| body | TEXT | NO | | Contenido del SMS |
| handler | VARCHAR(32) | YES | NULL | Handler que procesÃ³ (solo received) |
| status | ENUM('pending','sent','failed','timeout','delivered','received') | NO | 'pending' | Estado del mensaje |
| error_message | TEXT | YES | NULL | Mensaje de error si fallÃ³ |
| modem_sms_id | INT | YES | NULL | ID interno de mmcli |
| created_at | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) | Fecha de creaciÃ³n |

FK: `FOREIGN KEY (conversation_id) REFERENCES sms_conversations(id)`

### Migraciones

1. `database/migrations/2026_07_02_000001_create_sms_conversations.sql`
2. `database/migrations/2026_07_02_000002_create_sms_messages.sql`

### Datos semilla

Ninguno. Las tablas se crean vacÃ­as.

---

## 7. Contrato API

Esta feature NO expone nuevos endpoints REST. Sin embargo, refactoriza los siguientes
endpoints existentes que usan SMS internamente:

| Endpoint | Cambio |
|----------|--------|
| `POST /api/emergency/request` | `create_request()` persiste el SMS enviado al supervisor en `sms_messages` |
| `GET /api/emergency/admins` | Sin cambios |
| `POST /api/auth/verify-reset-pin` | Se actualiza para registrar intentos fallidos en la conversaciÃ³n |
| `POST /api/auth/complete-reset` | Sin cambios |

No se requiere contrato API nuevo.

---

## 8. Análisis de impacto en features existentes

> Análisis realizado mediante grep de `send_sms()`, `handle_sms_query`, y
> referencias cruzadas con feature_list.json. Se identificaron 8 features
> impactadas directa o indirectamente.

### Feature 6 — weighing_capture (id=6)

| Item | Archivo | Cambio requerido |
|------|---------|-----------------|
| Flujo de emergencia | `src/weighing_capture.py` | Sin cambios directos. Si la activación de emergencia vía SMS ahora es asíncrona (cola), el tiempo entre solicitud y activación puede aumentar ligeramente (~1-2s adicionales). El frontend ya hace polling de GET /api/emergency/status cada 5s, por lo que no hay impacto visible |

### Feature 7 — sms_service (id=7)

| Item | Archivo | Cambio requerido |
|------|---------|-----------------|
| Método `send_sms()` | `src/sms_service.py` | **Cambio de interfaz semántico.** `send_sms()` retorna `bool`. Actualmente retorna `True` si mmcli envió exitosamente. Con cola asíncrona, retorna `True` si el mensaje se encoló exitosamente (no si se entregó). Los llamantes deben ajustar su expectativa. Se agrega `send_sms_sync()` para casos legacy que requieran confirmación inmediata |
| Método `_send_via_mmcli()` | `src/sms_service.py` | Se mantiene como método interno invocable por `SmsSendQueue`. La cola asíncrona reemplaza la ejecución directa desde los handlers |
| Reportes programados | `src/sms_service.py:168,179` | `send_sms()` llamado desde reportes (turno, anomalías). Estos ahora encolan. No hay cambio funcional: el SMS se envía eventualmente |

### Feature 8 — ai_agent (id=8)

| Item | Archivo | Cambio requerido |
|------|---------|-----------------|
| Handler catch-all AI | `src/main.py:247-250` | **NO se elimina.** Se reemplaza por handler explícito `ai_query` registrado en dispatcher v2 con `workflow_type='ai_query'`. El nuevo handler persiste el SMS, llama al LLM, y persiste la respuesta. Si el LLM falla (LlamaConnectionError), persiste el error y NO re-intenta: status='failed', la conversación queda `completed` |
| `handle_sms_query()` | `src/agent_orchestrator.py:154` | **No se modifica.** El método sigue funcionando igual. El cambio está en el dispatcher (quién lo llama y cómo). El método recibe sender_phone y text, y llama a send_sms() para responder. Como send_sms() ahora encola, handle_sms_query no espera confirmación de entrega |
| Llamadas a `send_sms()` | `src/agent_orchestrator.py:173,181,191,193,232,243,253,256,278` | **8 llamadas.** Ninguna verifica el valor de retorno de send_sms(). Cambio transparente. Cubiertas por tests existentes |
| Dependencia transitiva | Feature 8 depende de Feature 6, 7, 12 | Feature 7 está modificada, Feature 12 también. Los tests de integración de Feature 8 deben re-ejecutarse |

### Feature 9 — emergency_mode (id=9)

| Item | Archivo | Cambio requerido |
|------|---------|-----------------|
| Método `process_incoming_sms()` | `src/emergency_mode.py` | Usar `SmsPersistenceService` para persistir SMS entrantes y de respuesta. Vincular `conversation_id` a `emergency_mode_log.request_id` |
| Método `create_request()` | `src/emergency_mode.py` | Persistir SMS de solicitud al supervisor en `sms_messages`. `send_sms()` ahora encola: la confirmación HTTP al kiosco llega antes de que el SMS se envíe físicamente (esto ya ocurría antes porque mmcli se ejecutaba en el mismo thread; la diferencia es que ahora el tiempo HTTP es ~1ms en vez de ~20s) |
| Método `activate()` | `src/emergency_mode.py` | Registrar SMS de confirmación en `sms_messages` (direction='sent') |
| Método `deactivate()` | `src/emergency_mode.py` | Registrar SMS de notificación en `sms_messages` (direction='sent') |
| Método `extend()` | `src/emergency_mode.py` | Registrar SMS de notificación en `sms_messages` (direction='sent') |
| Dependencia transitiva | Feature 9 depende de Feature 2, 3, 7. Feature 7 modificada. Feature 13 (frontend) consume endpoints de emergencia | El frontend hace polling de GET /api/emergency/status cada 5s. La activación asíncrona NO afecta el polling porque el endpoint lee `self._active` (en memoria), no espera a que el SMS se envíe |

### Feature 10 — backup_system (id=10)

| Item | Archivo | Cambio requerido |
|------|---------|-----------------|
| Notificaciones SMS | `src/backup.py` (vía `sms_service.send_sms()`) | Los backups usan send_sms() para notificar resultados. Con cola asíncrona, no hay cambio funcional: el SMS se envía eventualmente. NI hay dependencia del valor de retorno |

### Feature 12 — password_reset_sms (id=12)

| Item | Archivo | Cambio requerido |
|------|---------|-----------------|
| Método `handle_incoming_sms()` | `src/password_reset.py` | Validar rol admin del remitente. Si no es admin, responder error y retornar True. Validar que admin no resetea su propia contraseña. Persistir SMS en `sms_messages` |
| Método `generate_and_send_pin()` | `src/password_reset.py` | Persistir SMS de PIN en `sms_messages` (direction='sent'). Si nuevo request para mismo usuario, invalidar PIN anterior (cancelled) y crear nueva conversación |
| Contador de intentos de PIN | `src/password_reset.py` | Agregar lógica de máximo 3 intentos fallidos por conversación (almacenado en metadata de sms_conversations). Al alcanzar límite, invalidar PIN y marcar conversación como 'cancelled' |

### Feature 13 — frontend_login_kiosk (id=13)

| Item | Archivo | Cambio requerido |
|------|---------|-----------------|
| Vista Kiosko | `frontend/` (sin cambios en frontend) | El kiosco usa POST /api/emergency/request y GET /api/emergency/status. La respuesta HTTP a POST request retorna inmediatamente (sin esperar envío SMS). El frontend ya maneja esto correctamente porque la respuesta actual dice "Solicitud enviada. Esperando autorizacion por SMS." |
| Polling de status | `frontend/` | Cada 5s consulta GET /api/emergency/status. Sin cambios |

### Feature 26 — emergency_request_wrong_sms (bug, id=26, triaged)

| Item | Archivo | Cambio requerido |
|------|---------|-----------------|
| Handler AI catch-all | `src/main.py:247-250` | Reemplazar por handler explícito `ai_query` registrado en dispatcher v2. El bug se arregla porque: (1) el handler AI ya no es catch-all, (2) si el LLM falla, se persiste el error sin re-intentar, (3) SMS no reconocidos reciben ayuda en vez de caer al AI |

---

## 9. Riesgos de regresión

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| `send_sms()` cambia semántica de retorno: True ahora significa "encolado", no "entregado" | Alta | Media — los llamantes existentes verifican `if not send_sms(...)` o ignoran el retorno. Si algún caller depende del bool para decidir si reintentar, puede reintentar innecesariamente | Agregar `send_sms_sync()` para compatibilidad. Documentar el cambio en el docstring. Verificar cada uno de los 18 llamantes de send_sms() en src/ |
| La cola asíncrona falla en iniciar (thread no arranca) | Baja | Alta — todos los SMS salientes quedan en status='pending' sin enviarse | Log de error al iniciar thread. Health check que exponga el estado de la cola. El servicio debe fallar al inicio si la cola no puede arrancar |
| La cola asíncrona acumula mensajes si mmcli falla recurrentemente | Media | Media — los mensajes se acumulan en BD con status='pending', sin reintentar después de 3 intentos | Monitoreo periódico de sms_messages con status='pending' más antiguos de N minutos. Alerta en log |
| Dispatcher v1 y v2 coexistiendo accidentalmente (ambos procesan mismo SMS) | Media | Alta — duplicación de procesamiento, emergencias activadas dos veces | main.py NO debe iniciar dispatcher v1. Verificar explícitamente en startup que solo dispatcher v2 esté vivo |
| Eliminación del handler catch-all AI bloquea consultas de corresponsales | Alta (si no se implementa bien) | Crítica — Feature 8 deja de funcionar | El handler `ai_query` explícito reemplaza al catch-all. Verificar en tests que un SMS de corresponsal llega al handler AI |

---

## 10. Pruebas de regresión requeridas

Antes de declarar la feature como `done`, ejecutar:

```bash
# Tests unitarios de features afectadas
docker compose exec backend python -m unittest tests.test_sms_service -v
docker compose exec backend python -m unittest tests.test_emergency_mode -v
docker compose exec backend python -m unittest tests.test_password_reset -v
docker compose exec backend python -m unittest tests.test_agent_orchestrator -v
docker compose exec backend python -m unittest tests.test_backup -v

# Tests de la nueva feature
docker compose exec backend python -m unittest tests.test_sms_persistence -v
docker compose exec backend python -m unittest tests.test_sms_dispatcher_v2 -v
docker compose exec backend python -m unittest tests.test_sms_send_queue -v

# Verificación completa
./init.ps1
```

---

## 11. Orden de inicialización en main.py

```
lifespan:
  1. Cargar config
  2. init_db()
  3. Crear SmsPersistenceService(db_session_factory)
  4. Crear SMSService (sin cambios)
  5. Crear SmsSendQueue(persistence, sms_service, modem_index)
  6. Crear IncomingSmsDispatcherV2(modem_index, dev_mode, persistence)
     → Registrar handler: emergency → workflow_type=emergency
     → Registrar handler: password_reset → workflow_type=password_reset
     → Registrar handler: ai_query → workflow_type=ai_query (EXPLÍCITO, no catch-all)
     → (Handler unknown es interno del dispatcher v2)
  7. Iniciar sms_send_queue.start()
  8. Iniciar sms_dispatcher_v2.start()
  9. Inicializar EmergencyModeService, PasswordResetService (como antes)
```

El dispatcher v1 NO se inicia. Se mantiene el archivo `sms_incoming.py` por
referencias de tests existentes, pero el código nuevo no lo importa.

---

## 12. github_labels (opcional)

```json
["sms", "persistence", "async", "refactor"]
```

