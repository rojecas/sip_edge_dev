# Design Document — Conversación Multiturno para Consultas AI via SMS

> Feature 28 — Decisiones técnicas antes de implementar.
> **Validado por spec-validator el 2026-07-14.**

---

## 1. Resumen

Esta feature extiende el manejo de consultas AI vía SMS (Feature 8) para
soportar conversaciones multiturno, reutilizando la infraestructura de
`sms_conversations`/`sms_messages` de Feature 27. El historial conversacional
se almacena en la columna `metadata` de `sms_conversations` como
`message_history` (JSON array de exchanges texto plano). Una nueva tabla
`sms_ai_tool_log` registra todas las invocaciones de herramientas SQL del
LLM para auditoría.

No se crea una nueva API endpoint. La modificación principal es en
`AgentOrchestrator.handle_sms_query()` y su integración en `main.py`.

---

## 2. Archivos a crear

| Archivo | Propósito |
|---------|-----------|
| `database/migrations/2026_07_14_000001_add_archived_to_sms_conversations.sql` | ALTER TABLE sms_conversations MODIFY COLUMN status ENUM(...) agregando 'archived' |
| `database/migrations/2026_07_14_000002_create_sms_ai_tool_log.sql` | Migración tabla `sms_ai_tool_log` |
| `src/ai_multi_turn.py` | Servicio de gestión de contexto multiturno para consultas AI |

---

## 3. Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `src/models.py` | Agregar modelo ORM `SmsAiToolLog`; agregar `'archived'` al ENUM `status` de `SmsConversation` |
| `src/agent_orchestrator.py` | Modificar `handle_sms_query()` para aceptar `message_id` y `conversation_id` e integrar `AiMultiTurnService` para gestión de contexto multiturno, tool logging y farewell detection |
| `src/main.py` | Actualizar handler lambda AI para pasar `message_id` y `conversation_id` a `handle_sms_query()`; inicializar `AiMultiTurnService`; agregar tarea diaria de archivado |
| `src/sms_persistence.py` | Agregar métodos `get_conversation()`, `get_messages_by_conversation()`, `update_conversation_metadata()` |

---

## 4. Firmas nuevas

### `src/ai_multi_turn.py`

```python
class AiMultiTurnError(Exception):
    """Error base del servicio de conversación multiturno AI."""


FAREWELL_PATTERNS: list[str] = [
    "gracias", "bye", "adiós", "chao", "eso es todo",
    "es todo", "nada más", "no más", "terminamos",
    "suficiente", "ok gracias",
]


class AiMultiTurnService:
    def __init__(
        self,
        db_session_factory,
        persistence: SmsPersistenceService,
    ) -> None:
        ...

    def get_or_create_ai_conversation(
        self, peer_number: str, conversation_id: int | None = None,
    ) -> SmsConversation:
        """Retorna la conversación ai_query activa para peer_number,
        o crea una nueva si no existe.

        Si conversation_id es provisto por el dispatcher (ver §14),
        DEBE verificar si la conversación asociada tiene
        workflow_type='unknown' y actualizarla a 'ai_query'.
        """

    def get_message_history(
        self, conversation: SmsConversation,
    ) -> list[dict]:
        """Retorna message_history desde metadata como lista de dicts
        con formato [{"user": "...", "assistant": "..."}, ...]."""

    def build_llm_messages(
        self,
        message_history: list[dict],
        new_user_text: str,
        system_prompt: str,
    ) -> list[dict]:
        """Construye el arreglo de mensajes para el LLM combinando
        el system prompt, el historial, y el nuevo mensaje del usuario."""

    def append_exchange(
        self,
        conversation_id: int,
        message_history: list[dict],
        user_text: str,
        assistant_text: str,
        max_exchanges: int = 10,
    ) -> None:
        """Agrega un exchange al historial, aplicando FIFO si se
        supera el límite. Persiste el metadata actualizado en BD."""

    def log_tool_call(
        self,
        conversation_id: int,
        incoming_msg_id: int,
        tool_name: str,
        tool_args: dict,
        tool_result: dict,
        duration_ms: int,
    ) -> None:
        """Registra un tool_call en sms_ai_tool_log."""

    def detect_farewell(self, text: str) -> bool:
        """Detecta si un texto contiene despedida. Retorna True si
        coincide con FAREWELL_PATTERNS (keyword matching, no LLM)."""

    def complete_conversation(
        self, conversation_id: int,
    ) -> None:
        """Marca la conversación como completed."""

    def archive_old_conversations(self) -> int:
        """Archiva conversaciones ai_query completadas sin actividad
        por 90+ días. Retorna el número de conversaciones archivadas."""

    def get_max_exchanges(self, conversation: SmsConversation) -> int:
        """Lee max_exchanges de metadata o retorna default 10."""
```

### `src/agent_orchestrator.py` — Firma modificada

```python
class AgentOrchestrator:
    def handle_sms_query(
        self,
        sender_phone: str,
        text: str,
        message_id: int | None = None,
        conversation_id: int | None = None,
    ) -> bool:
        """Ahora usa AiMultiTurnService para gestionar el contexto
        conversacional. Acepta message_id y conversation_id opcionales."""
```

### `src/sms_persistence.py` — Métodos nuevos

```python
class SmsPersistenceService:
    def get_conversation(
        self, conversation_id: int,
    ) -> SmsConversation | None:
        """Recupera una conversación por ID."""

    def get_messages_by_conversation(
        self, conversation_id: int,
        limit: int = 50,
    ) -> list[SmsMessage]:
        """Recupera los mensajes de una conversación."""

    def update_conversation_metadata(
        self, conversation_id: int,
        metadata: dict,
    ) -> None:
        """Actualiza la columna metadata de una conversación."""
```

### Modelo nuevo en `src/models.py`

```python
class SmsAiToolLog(Base):
    """Registro de tool_calls ejecutados durante consultas AI."""
    __tablename__ = "sms_ai_tool_log"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    conversation_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("sms_conversations.id"), nullable=False, index=True)
    incoming_msg_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("sms_messages.id"), nullable=False, index=True)
    tool_name = Column(String(64), nullable=False)
    tool_args = Column(JSON, nullable=False)
    tool_result = Column(JSON, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
```

---

## 5. Excepciones nuevas

| Excepción | Módulo | Propósito |
|-----------|--------|-----------|
| `AiMultiTurnError` | `src/ai_multi_turn.py` | Error base del servicio de conversación multiturno AI |

---

## 6. Persistencia

### Tabla nueva: `sms_ai_tool_log`

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK |
| conversation_id | BIGINT UNSIGNED | NO | | FK → sms_conversations.id |
| incoming_msg_id | BIGINT UNSIGNED | NO | | FK → sms_messages.id |
| tool_name | VARCHAR(64) | NO | | Nombre de la herramienta SQL ejecutada |
| tool_args | JSON | NO | | Argumentos de la llamada |
| tool_result | JSON | NO | | Resultado devuelto por la herramienta |
| duration_ms | INT | NO | | Tiempo de ejecución en milisegundos |
| created_at | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) | Fecha de creación |

FK: `FOREIGN KEY (conversation_id) REFERENCES sms_conversations(id)`
FK: `FOREIGN KEY (incoming_msg_id) REFERENCES sms_messages(id)`

Índices:
- `idx_sms_ai_tool_log_conv` ON `(conversation_id)`
- `idx_sms_ai_tool_log_msg` ON `(incoming_msg_id)`
- `idx_sms_ai_tool_log_created` ON `(created_at)`

### Tabla modificada: `sms_conversations`

Campo `status`: Agregar valor `'archived'` al ENUM existente:
```
ENUM('active','completed','expired','cancelled','failed','archived')
```

### Migraciones

1. `database/migrations/2026_07_14_000001_add_archived_to_sms_conversations.sql`
   — ALTER TABLE sms_conversations MODIFY COLUMN status...
2. `database/migrations/2026_07_14_000002_create_sms_ai_tool_log.sql`
   — CREATE TABLE sms_ai_tool_log

### Datos semilla

Ninguno. Las tablas se crean vacías.

---

## 7. Contrato API

No se exponen nuevos endpoints REST. El flujo AI multiturno opera
internamente a través del dispatcher de SMS existente.

### Endpoints existentes afectados

| Endpoint | Cambio |
|----------|--------|
| `POST /api/agent/query` | Sin cambios directos. Este endpoint es para consultas desde el frontend admin, no desde SMS. No recibe beneficios del multiturno |
| SMS entrantes → dispatcher v2 → handler ai_query | El handler ahora pasa `message_id` y `conversation_id` a `handle_sms_query()`. La respuesta sigue siendo enviada por SMS vía `sms_service.send_sms()` |

---

## 8. Análisis de impacto en features existentes

> Análisis realizado mediante grep de `handle_sms_query`, `send_sms`,
> `message_history`, y referencias cruzadas con feature_list.json.
> Se identificaron 5 features impactadas directa o indirectamente.

### Feature 8 — ai_agent (id=8)

| Item | Archivo | Cambio requerido |
|------|---------|-----------------|
| Método `handle_sms_query()` | `src/agent_orchestrator.py` | **Cambio de firma:** acepta `message_id` y `conversation_id` opcionales. El flujo interno se modifica para usar `AiMultiTurnService`: obtiene/crea conversación ai_query, recupera message_history, construye mensajes LLM con historial, ejecuta tools con logging en sms_ai_tool_log, detecta despedida, actualiza message_history. Compatibilidad hacia atrás: parámetros nuevos son `Optional` con default `None` |
| Llamadas a `send_sms()` internas | `src/agent_orchestrator.py` | Sin cambios: el método ya llama a `send_sms()` y esa capa no cambia |
| System prompt | `src/agent_orchestrator.py` | Se actualiza para incluir instrucciones sobre detección de despedida y formato de historial multiturno |
| Handler en main.py | `src/main.py:348-351` | El lambda se actualiza para pasar `message_id` y `conversation_id` a `handle_sms_query()` |

**Compatibilidad hacia atrás:** Sí. Los nuevos parámetros son opcionales.
Si `message_id` o `conversation_id` son `None`, el método funciona sin
contexto multiturno (modo legacy). Esto permite que llamadas existentes
(desde tests o desde `POST /api/agent/query`) sigan funcionando.

### Feature 7 — sms_service (id=7)

| Item | Archivo | Cambio requerido |
|------|---------|-----------------|
| Servicio SMS | `src/sms_service.py` | Sin cambios. `send_sms()` sigue funcionando igual. La respuesta AI se envía a través de los mismos canales |

### Feature 27 — sms_persistence (id=27)

| Item | Archivo | Cambio requerido |
|------|---------|-----------------|
| ENUM status | `src/models.py: SmsConversation` | Agregar `'archived'` al ENUM `status`. Se requiere migración ALTER TABLE |
| Métodos `get_conversation()`, `get_messages_by_conversation()`, `update_conversation_metadata()` | `src/sms_persistence.py` | **Cambio aditivo.** Se agregan 3 nuevos métodos públicos. No se modifican métodos existentes. Compatibilidad total hacia atrás |
| Método `get_or_create_active_conversation()` | `src/sms_persistence.py` | Sin cambios directos. El nuevo `AiMultiTurnService` lo usa para obtener/crear conversaciones ai_query, pero debe manejar el caso donde el dispatcher creó la conversación con `workflow_type='unknown'` (ver §14) |

**Compatibilidad hacia atrás:** Total. Solo se agregan métodos nuevos.

### Feature 9 — emergency_mode (id=9)

| Item | Archivo | Cambio requerido |
|------|---------|-----------------|
| Prioridad sobre AI | `src/sms_dispatcher_v2.py` (no se modifica) | El dispatcher ya registra emergency ANTES que ai_query (orden en main.py: 1. emergency, 2. password_reset, 3. ai_query). F28 no cambia este orden. El dispatcher evalúa handlers en orden: si emergency devuelve True, ai_query ni se ejecuta |

**Cambio requerido:** Ninguno en emergency_mode.py. El orden de handlers
en main.py ya garantiza R11.

### Feature 12 — password_reset_sms (id=12)

| Item | Archivo | Cambio requerido |
|------|---------|-----------------|
| Prioridad sobre AI | `src/sms_dispatcher_v2.py` (no se modifica) | Igual que emergency: password_reset está registrado antes que ai_query en main.py |

**Cambio requerido:** Ninguno en password_reset.py.

### Dependencias transitivas

| Feature | Depende de | Impacto |
|---------|-----------|---------|
| 17 (frontend_analytics) | 8 | Sin cambios. El frontend admin usa `POST /api/agent/query` que no se modifica |
| 33 (sql_tools_v2) | 8 | Sin cambios. Las tool_definitions no se modifican, solo se auditan en sms_ai_tool_log |

---

## 9. Alternativa descartada: Servicio monolítico sin AiMultiTurnService

**Alternativa:** Extender directamente `AgentOrchestrator.handle_sms_query()`
con la lógica multiturno dentro del mismo método, sin crear un servicio
separado.

**Descartada por:** (1) El método ya tiene más de 180 líneas con el flujo
de tool_calls y manejo de errores. Agregar 100+ líneas de gestión de
contexto convertirá el método en inmantenible. (2) La lógica de
message_history, FIFO, archive cleanup y tool_logging son responsabilidades
distintas que merecen su propia clase con tests unitarios independientes.
(3) `AiMultiTurnService` puede ser probado en aislamiento sin necesidad de
un LLM real.

---

## 10. Orden de inicialización en main.py

```
lifespan:
  1-4. (sin cambios — config, db, persistence, sms_service, etc.)
  5. Crear AiMultiTurnService(db_session_factory, persistence)
  6. AgentOrchestrator recibe ai_multi_turn_service como dependencia
  7. Registrar handlers en dispatcher (sin cambios en orden)
     → 1. emergency, 2. password_reset, 3. ai_query (ahora pasa
        message_id y conversation_id)
  8. Iniciar tarea diaria de archivado (asyncio.create_task)
```

---

## 11. Flujo de handle_sms_query con multiturno

```
handle_sms_query(phone, text, message_id, conversation_id):
  1. Obtener/crear conversación ai_query para peer_number
     → AiMultiTurnService.get_or_create_ai_conversation(phone,
         conversation_id)
     Si conversation_id fue provisto por el dispatcher y la
     conversación tiene workflow_type='unknown', actualizarla a
     'ai_query' (ver §14).
  2. Recuperar message_history de la metadata
     → AiMultiTurnService.get_message_history(conversation)
  3. Construir mensajes LLM: system_prompt + historial + nuevo mensaje
     → AiMultiTurnService.build_llm_messages(...)
  4. (sin cambios) Enviar al LLM con tool_definitions
  5. SI hay tool_calls:
     a. Ejecutar cada tool, medir duration_ms
     b. Loggear en sms_ai_tool_log
        → AiMultiTurnService.log_tool_call(...)
     c. Segunda vuelta LLM (parafraseo)
  6. Obtener respuesta textual del LLM
  7. Append exchange a message_history (FIFO si aplica)
     → AiMultiTurnService.append_exchange(...)
  8. SI el sistema detecta despedida en el texto del usuario
     (keyword matching contra FAREWELL_PATTERNS):
     → AiMultiTurnService.complete_conversation()
  9. Enviar respuesta SMS (sin cambios)
```

---

## 12. Tarea de archivado diario

```python
async def _archive_old_ai_conversations(ai_multi_turn_service):
    """Ejecuta archivado una vez al día."""
    while True:
        try:
            count = ai_multi_turn_service.archive_old_conversations()
            if count > 0:
                logger.info("Archivadas %d conversaciones AI antiguas", count)
        except Exception:
            logger.exception("Error en archivado de conversaciones AI")
        await asyncio.sleep(86400)  # 24 horas
```

---

## 13. github_labels (opcional)

```json
["ai", "multi-turn", "conversation", "sms"]
```

---

## 14. Integración con Dispatcher v2 — Manejo de conversación pre-creada

> **Agregado durante validación del spec-validator (2026-07-14).**

El `IncomingSmsDispatcherV2` (F27) persiste el SMS entrante y crea una
conversación con `workflow_type='unknown'` antes de delegar a los handlers.
Al llamar al handler AI, el dispatcher pasa `conversation_id` con el ID de
esta conversación pre-creada.

`get_or_create_ai_conversation()` DEBE manejar este caso de la siguiente
manera:

1. **Si `conversation_id` es provisto:**
   - Recuperar la conversación por ID.
   - Si `workflow_type == 'unknown'`: actualizar a `'ai_query'` y retornar.
   - Si `workflow_type == 'ai_query'` y `status == 'active'`: reutilizar.
   - Si `status != 'active'`: crear nueva conversación.

2. **Si `conversation_id` NO es provisto** (modo legacy, ej. `POST /api/agent/query`):
   - Buscar conversación ai_query activa por `peer_number`.
   - Si existe, reutilizar.
   - Si no existe, crear nueva.

Este mecanismo evita la creación de conversaciones duplicadas (una
"unknown" creada por el dispatcher + una "ai_query" creada por el handler).

### Validación del flujo completo con el dispatcher

```
1. SMS llega al modem → mmcli lo recibe
2. DispatcherV2._dispatch():
   a. Crea conversación con workflow_type='unknown', status='active'
   b. Crea sms_message (direction='received', status='received')
   c. Recorre handlers en orden: emergency → password_reset → ai_query
   d. Para cada handler: handler(phone, text, msg.id, conv.id)
3. Handler ai_query (lambda) → handle_sms_query(phone, text, msg.id, conv.id)
4. AiMultiTurnService.get_or_create_ai_conversation(phone, conv.id):
   a. Recupera conversación por conv.id → ve workflow_type='unknown'
   b. Actualiza workflow_type='ai_query' (reusa la conversación del dispatcher)
   c. Retorna la conversación
5. El resto del flujo multiturno procede normalmente
```
