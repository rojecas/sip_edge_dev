# Spec Review Report — Feature 28 (ai_multi_turn)

> **Validator:** spec-validator
> **Fecha:** 2026-07-14
> **Feature:** 28 — Conversación Multiturno para Consultas AI via SMS
> **Estado final:** spec-reviewed

---

## 1. Resumen de auditoría

Se auditó el spec completo (`requirements.md`, `design.md`, `tasks.md`) de
la feature F28 contra los 11 acceptance criteria definidos en
`feature_list.json`. Se verificó trazabilidad, calidad EARS, integridad del
diseño y cobertura de tests.

**Resultado:** 11/11 acceptance criteria cubiertos por R1-R11 (más R12
como soporte de implementación). Se encontraron 2 gaps que fueron
corregidos.

---

## 2. Hallazgos

### Gap 1 — R8: "CUANDO el LLM detecta" vs implementación real (CORREGIDO)

**Severidad:** Media (inconsistencia spec/design)

El requirement R8 original decía "CUANDO el LLM detecta que el mensaje del
usuario expresa una despedida", pero el diseño (`FAREWELL_PATTERNS`) usa
keyword matching (`detect_farewell(text: str) -> bool`), no inferencia del
LLM. La redacción original era inconsistente con el diseño propuesto.

**Corrección aplicada:** Se cambió "CUANDO el LLM detecta" por "CUANDO el
sistema detecta" en R8. Se agregó nota de validación explicando la
decisión de diseño. `requirements.md` fue renombrado a
`requirements.old.md` y se escribió la versión corregida.

### Gap 2 — Integración con Dispatcher v2: conversación pre-creada como 'unknown' (CORREGIDO)

**Severidad:** Alta (riesgo de conversaciones duplicadas)

El `IncomingSmsDispatcherV2` (F27) crea la conversación con
`workflow_type='unknown'` antes de delegar a handlers. El diseño original
de `get_or_create_ai_conversation(peer_number)` no contemplaba este caso:
buscaba una conversación con `workflow_type='ai_query'` y no la encontraba,
creando una nueva conversación duplicada.

Verificado en el código actual:
- `sms_dispatcher_v2.py:279` — `get_or_create_active_conversation(peer_number=sender_phone, workflow_type="unknown")`
- `sms_dispatcher_v2.py:314` — `handler(sender_phone, trimmed_text, msg.id, conv.id)` — el dispatcher YA pasa `conversation_id`
- `main.py:349` — lambda acepta `message_id` y `conversation_id` pero no los pasa a `handle_sms_query` (bug latente)

**Corrección aplicada:**
- `design.md`: Nueva §14 "Integración con Dispatcher v2" que documenta el
  flujo completo y la estrategia de actualización de `workflow_type`.
- `design.md`: `get_or_create_ai_conversation` acepta ahora
  `conversation_id: int | None = None` como parámetro opcional.
- `design.md`: §11 (flujo) actualizado para reflejar el manejo de la
  conversación pre-creada.
- `tasks.md`: T5 actualizado con la firma correcta y nota IMPORTANTE sobre
  el dispatcher.
- `tasks.md`: T6 agregado test `test_get_or_create_ai_conversation_upgrades_unknown`.
- `tasks.md`: T10 agregado test `test_dispatcher_unknown_conversation_upgrade`.
- `design.md` fue renombrado a `design.old.md` y se escribió versión corregida.
- `tasks.md` fue renombrado a `tasks.old.md` y se escribió versión corregida.

---

## 3. Observaciones (no bloqueantes)

### OBS-1 — R4 con múltiples sub-acciones

R4 contiene tres acciones bajo un mismo "CUANDO" (Recuperar, Construir,
Enviar). Son acciones cohesivas bajo un único trigger. No se requiere
partir en sub-requirements.

### OBS-2 — R8 con dos DEBE

R8 tiene "DEBE marcar" y "DEBE responder". Se considera aceptable porque
ambas acciones son consecuencia directa de la misma detección de despedida.

### OBS-3 — Actualización de last_activity

El `last_activity` de `sms_conversations` se actualiza cuando el dispatcher
v2 recibe un nuevo SMS y persiste el `sms_message`. Las respuestas del
asistente almacenadas en `message_history` (JSON en metadata) NO generan un
nuevo `sms_message` (la respuesta se envía por SMS pero no se persiste como
fila en `sms_messages` en el flujo AI multiturno). El reviewer debe
verificar que la lógica de archivado (R9: 90 días desde `last_activity`)
sigue siendo correcta con este comportamiento.

---

## 4. Trazabilidad: Acceptance Criteria → R<n>

| AC # | Acceptance Criterion | R<n> |
|------|---------------------|------|
| 1 | AI queries usan sms_conversaciones con workflow_type=ai_query | R1 |
| 2 | message_history en metadata, texto plano, sin tool_calls | R2, R3, R10 |
| 3 | FIFO al llegar al límite de 10 exchanges | R3 |
| 4 | Recuperar message_history + append + enviar al LLM con tools | R4 |
| 5 | Tabla sms_ai_tool_log con columnas especificadas | R5 |
| 6 | Tool_calls en sms_ai_tool_log, NO en message_history | R6 |
| 7 | Una sola conversación AI activa por peer_number | R7 |
| 8 | Detección de despedida → completed | R8 |
| 9 | Archivado a 90 días | R9 |
| 10 | Límite de exchanges configurable (default 10) | R10 |
| 11 | Emergency/password_reset prioridad sobre AI | R11 |

---

## 5. Archivos modificados

| Archivo | Acción |
|---------|--------|
| `harness/specs/28_ai_multi_turn/requirements.md` | Reescrito (corrección R8) |
| `harness/specs/28_ai_multi_turn/requirements.old.md` | Backup del original |
| `harness/specs/28_ai_multi_turn/design.md` | Reescrito (nueva §14 dispatcher, firma actualizada) |
| `harness/specs/28_ai_multi_turn/design.old.md` | Backup del original |
| `harness/specs/28_ai_multi_turn/tasks.md` | Reescrito (T5 actualizado, nuevos tests) |
| `harness/specs/28_ai_multi_turn/tasks.old.md` | Backup del original |
| `harness/feature_list.json` | Status: spec_ready → spec-reviewed |
| `harness/progress/spec_review_28_ai_multi_turn.md` | Este informe (nuevo) |

---

## 6. Archivos que el implementer debe modificar

Lista consolidada de todos los archivos que deben tocarse durante la
implementación, según lo declarado en design.md y verificado contra el
código actual:

| Archivo | Acción | Validado |
|---------|--------|----------|
| `database/migrations/2026_07_14_000001_add_archived_to_sms_conversations.sql` | Crear | Nueva migración |
| `database/migrations/2026_07_14_000002_create_sms_ai_tool_log.sql` | Crear | Nueva migración |
| `src/ai_multi_turn.py` | Crear | Nuevo módulo |
| `tests/test_ai_multi_turn.py` | Crear | Nuevo test |
| `tests/test_ai_multi_turn_integration.py` | Crear | Nuevo test |
| `src/models.py` | Modificar | +SmsAiToolLog, +'archived' en ENUM |
| `src/agent_orchestrator.py` | Modificar | Firma + AiMultiTurnService |
| `src/main.py` | Modificar | Lambda, AiMultiTurnService init, archivado |
| `src/sms_persistence.py` | Modificar | +3 métodos |

---
