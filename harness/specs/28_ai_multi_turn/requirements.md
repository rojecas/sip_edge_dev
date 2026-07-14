# Requirements — Conversación Multiturno para Consultas AI via SMS

> Feature 28 — Extiende F8 (ai_agent) y F27 (sms_persistence) para soporte
> de conversaciones multiturno AI vía SMS.
> Redactado en EARS (Easy Approach to Requirements Syntax).
> **Validado por spec-validator el 2026-07-14.**

---

## R1 — Vinculación a conversación ai_query

CUANDO el dispatcher de SMS entrantes delega un mensaje al handler AI
(`workflow_type='ai_query'`), el sistema DEBE usar o crear una conversación
en `sms_conversations` con `workflow_type='ai_query'`, asociando todos los
mensajes de la misma conversación al mismo `conversation_id`.

> **Nota de validación:** El dispatcher v2 (F27) crea la conversación inicial
> con `workflow_type='unknown'`. El handler AI DEBE actualizar el
> `workflow_type` a `'ai_query'` y el `status` a `'active'` en lugar de
> crear una conversación duplicada.

---

## R2 — message_history en metadata

El sistema DEBE almacenar el historial conversacional en la columna
`metadata` de `sms_conversations` bajo la clave `message_history`, como un
array JSON de exchanges, donde cada exchange es un objeto con dos campos:
`{"user": "...", "assistant": "..."}`, conteniendo únicamente el texto plano
del mensaje del usuario y la respuesta textual del asistente. El sistema NO
DEBE incluir `tool_calls` ni `tool_results` en `message_history`.

---

## R3 — FIFO en límite de exchanges

CUANDO `message_history` alcanza el límite máximo de exchanges (por defecto
10), el sistema DEBE eliminar el exchange más antiguo del array antes de
agregar el nuevo exchange, manteniendo siempre como máximo el número de
exchanges configurado.

---

## R4 — Recuperación de contexto en nuevo mensaje

CUANDO llega un nuevo SMS de un `peer_number` que tiene una conversación
`ai_query` activa, el sistema DEBE:
- Recuperar `message_history` de la columna `metadata` de la conversación.
- Construir el arreglo de mensajes para el LLM combinando el historial
  recuperado y el nuevo mensaje del usuario.
- Enviar el historial completo al LLM junto con las `tool_definitions`.

---

## R5 — Tabla sms_ai_tool_log

El sistema DEBE crear la tabla `sms_ai_tool_log` con las columnas: `id`
(BIGINT UNSIGNED AUTO_INCREMENT PK), `conversation_id` (BIGINT UNSIGNED NOT
NULL FK → sms_conversations.id), `incoming_msg_id` (BIGINT UNSIGNED NOT NULL
FK → sms_messages.id), `tool_name` (VARCHAR(64) NOT NULL), `tool_args`
(JSON NOT NULL), `tool_result` (JSON NOT NULL), `duration_ms` (INT NOT NULL),
`created_at` (DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)).

---

## R6 — Auditoría de tool_calls en sms_ai_tool_log

CUANDO el LLM ejecuta `tool_calls` durante una consulta AI multiturno, el
sistema DEBE registrar en `sms_ai_tool_log` los campos: `tool_name`,
`tool_args` (el JSON de argumentos), `tool_result` (el JSON del resultado de
la herramienta SQL), `duration_ms` (tiempo de ejecución en milisegundos) y
las referencias a `conversation_id` y `incoming_msg_id`. El sistema NO DEBE
incluir estos datos en `message_history`.

---

## R7 — Una única conversación AI activa por peer_number

El sistema DEBE permitir como máximo una conversación `ai_query` con
`status='active'` por `peer_number`. CUANDO existe una conversación activa y
llega un nuevo mensaje del mismo `peer_number`, el sistema DEBE reutilizar
esa conversación para el nuevo exchange.

---

## R8 — Detección de despedida por el sistema

CUANDO el sistema detecta que el mensaje del usuario expresa una despedida
(gracias, bye, eso es todo, terminamos, etc.), el sistema DEBE marcar la
conversación `sms_conversations` como `status='completed'` en lugar de
`'active'`, y DEBE responder al usuario con un mensaje de cierre cortés.

> **Nota de validación:** Corregido respecto a la versión original: la
> detección de despedida se realiza mediante coincidencia de patrones
> (`FAREWELL_PATTERNS`) en el texto del usuario, no por inferencia del LLM.
> Esto es una decisión de diseño válida (menor latencia, sin llamada extra
> al modelo). La redacción original decía "CUANDO el LLM detecta" lo cual
> era inconsistente con el diseño propuesto.

---

## R9 — Archivado de conversaciones antiguas

MIENTRAS existan conversaciones `ai_query` con `status='completed'` cuya
`last_activity` sea anterior a 90 días desde la fecha actual, el sistema
DEBE ejecutar una tarea de limpieza diaria que actualice dichas
conversaciones a `status='archived'`.

---

## R10 — Límite de exchanges configurable

El sistema DEBE leer el límite máximo de exchanges de la columna `metadata`
de `sms_conversations` bajo la clave `max_exchanges`. DONDE la clave
`max_exchanges` no está presente en `metadata`, el sistema DEBE usar el
valor por defecto de 10 exchanges.

---

## R11 — Prioridad de emergency y password reset sobre AI

CUANDO llega un SMS entrante cuyo contenido coincide con los patrones de
emergencia (`manual on`, `manual off`, `manual on ext`) o de restablecimiento
de contraseña (`reset password`), el sistema DEBE procesar el SMS con el
handler correspondiente (emergency o password_reset) aunque exista una
conversación `ai_query` activa para ese mismo `peer_number`.

---

## R12 — Status 'archived' en sms_conversations

El sistema DEBE agregar el valor `'archived'` al ENUM `status` de la tabla
`sms_conversations`, permitiendo que las conversaciones completadas sin
actividad por 90 días sean marcadas con este estado.
