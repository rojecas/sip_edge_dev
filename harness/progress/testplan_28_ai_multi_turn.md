# Plan de Pruebas Manuales — F28 `ai_multi_turn`

> **Feature:** Conversación Multiturno para Consultas AI via SMS  
> **Requisitos:** R1-R12  
> **Entorno:** EdgeBox 192.168.1.42 (SSH: `ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42`)  

---

## Prerrequisitos

Antes de empezar, verifica que todo está operativo:

```bash
# 1. Conectarte a la EdgeBox
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42

# 2. Verificar que el servicio está corriendo con F28 desplegada
sudo systemctl status sip-edge

# 3. Verificar que el módem tiene señal
mmcli -m 0 | grep "state\|signal"

# 4. Verificar migraciones aplicadas
mysql -usip_user -psip_pass sip_edge -e "SHOW COLUMNS FROM sms_conversations LIKE 'status';"
mysql -usip_user -psip_pass sip_edge -e "SHOW CREATE TABLE sms_ai_tool_log\G"
```

---

## Prueba 1 — Conversación básica multiturno (R1, R2, R4, R7)

**Objetivo:** Verificar que una conversación AI mantiene contexto entre mensajes.

### Paso 1.1 — Enviar primer mensaje AI

Desde OTRO teléfono (NO el del EdgeBox), envía un SMS al número del EdgeBox:

```
Mensaje 1: cuantos pesajes hubo hoy?
```

Espera ~30-60 segundos y verifica:

```bash
# Ver conversación creada
mysql -usip_user -psip_pass sip_edge -e "
  SELECT id, peer_number, workflow_type, status, 
         JSON_EXTRACT(metadata, '$.message_history') as history
  FROM sms_conversations 
  WHERE workflow_type='ai_query' 
  ORDER BY id DESC LIMIT 1;
"

# Ver mensajes en la conversación
mysql -usip_user -psip_pass sip_edge -e "
  SELECT id, direction, body, status, created_at 
  FROM sms_messages 
  WHERE conversation_id = <ID_DE_ARRIBA> 
  ORDER BY created_at;
"
```

**Esperado:**
- `workflow_type = 'ai_query'`, `status = 'active'`
- `message_history` contiene 1 exchange: `[{"user": "cuantos pesajes hubo hoy?", "assistant": "..."}]`
- Hay 2 mensajes: 1 received (el tuyo) + 1 sent (respuesta)

### Paso 1.2 — Enviar segundo mensaje (mismo remitente)

```
Mensaje 2: y de la hacienda La Esperanza?
```

```bash
# Verificar que se REUTILIZA la misma conversación (mismo conversation_id)
mysql -usip_user -psip_pass sip_edge -e "
  SELECT id, 
         JSON_LENGTH(JSON_EXTRACT(metadata, '$.message_history')) as num_exchanges
  FROM sms_conversations 
  WHERE workflow_type='ai_query' AND status='active'
  ORDER BY id DESC LIMIT 1;
"
```

**Esperado:**
- `num_exchanges = 2` (se agregó el segundo exchange)
- Mismo `conversation_id` que en paso 1.1
- El LLM usó el contexto de "La Esperanza" sabiendo que es una hacienda

### Paso 1.3 — Verificar que message_history NO contiene tool_calls (R2, R6)

```bash
mysql -usip_user -psip_pass sip_edge -e "
  SELECT JSON_EXTRACT(metadata, '$.message_history') 
  FROM sms_conversations 
  WHERE id = <ID>;
" | grep -i "tool_call\|tool_result"
```

**Esperado:** El grep NO encuentra "tool_call" ni "tool_result" en message_history.

---

## Prueba 2 — FIFO en límite de 10 exchanges (R3, R10)

**Objetivo:** Verificar que al superar 10 exchanges se elimina el más antiguo.

### Paso 2.1 — Enviar 11 mensajes

Envía 11 mensajes simples (pueden ser preguntas triviales como "hola", "que dia es hoy", etc.):

```
Mensajes 1 al 11: hola, ok, dime los pesajes de ayer, gracias, etc.
```

### Paso 2.2 — Verificar límite

```bash
mysql -usip_user -psip_pass sip_edge -e "
  SELECT JSON_LENGTH(JSON_EXTRACT(metadata, '$.message_history')) as num_exchanges,
         JSON_EXTRACT(metadata, '$.message_history[0].user') as oldest,
         JSON_EXTRACT(metadata, CONCAT('$.message_history[', 
           JSON_LENGTH(JSON_EXTRACT(metadata, '$.message_history'))-1, '].user')) as newest
  FROM sms_conversations 
  WHERE id = <ID>;
"
```

**Esperado:**
- `num_exchanges = 10` (nunca más de 10)
- `oldest` es el mensaje #2 (el #1 fue eliminado por FIFO)
- `newest` es el mensaje #11

---

## Prueba 3 — Detección de despedida (R8)

**Objetivo:** Verificar que palabras de despedida cierran la conversación.

### Paso 3.1 — Enviar mensaje de despedida

```
Mensaje: gracias, eso es todo
```

### Paso 3.2 — Verificar cierre

```bash
mysql -usip_user -psip_pass sip_edge -e "
  SELECT id, status, last_activity 
  FROM sms_conversations 
  WHERE id = <ID>;
"
```

**Esperado:** `status = 'completed'`

### Paso 3.3 — Intentar continuar la conversación

```
Mensaje: y cual fue el promedio?
```

```bash
mysql -usip_user -psip_pass sip_edge -e "
  SELECT id, workflow_type, status 
  FROM sms_conversations 
  WHERE peer_number = '<TU_NUMERO>' 
  ORDER BY id DESC LIMIT 2;
"
```

**Esperado:** Se crea una NUEVA conversación `ai_query` con `status='active'`. La anterior sigue `completed`.

---

## Prueba 4 — Auditoría de tool_calls (R5, R6)

**Objetivo:** Verificar que las herramientas SQL invocadas quedan registradas en `sms_ai_tool_log`.

### Paso 4.1 — Hacer una consulta que requiera tool

```
Mensaje: dime los pesajes de ayer
```

### Paso 4.2 — Verificar tool_log

```bash
mysql -usip_user -psip_pass sip_edge -e "
  SELECT tl.id, tl.tool_name, 
         JSON_EXTRACT(tl.tool_args, '$.fecha_inicio') as fecha_ini,
         tl.duration_ms, tl.created_at
  FROM sms_ai_tool_log tl
  JOIN sms_messages m ON tl.incoming_msg_id = m.id
  WHERE m.conversation_id = <ID>
  ORDER BY tl.created_at;
"
```

**Esperado:**
- Aparece al menos 1 registro con `tool_name = 'get_daily_summary'` o similar
- `tool_args` contiene la fecha de ayer
- `duration_ms > 0`

### Paso 4.3 — Verificar que tool_calls NO están en message_history (R6)

```bash
mysql -usip_user -psip_pass sip_edge -e "
  SELECT JSON_EXTRACT(metadata, '$.message_history') 
  FROM sms_conversations WHERE id = <ID>;
" | grep -c "tool_call"
```

**Esperado:** `0` coincidencias.

---

## Prueba 5 — Prioridad de emergency sobre AI (R11)

**Objetivo:** Verificar que "manual on" se procesa como emergencia aunque haya conversación AI activa.

### Paso 5.1 — Iniciar conversación AI

```
Mensaje: hola
```

Verifica que la conversación AI está activa.

### Paso 5.2 — Enviar comando de emergencia (DESDE TELÉFONO DE ADMIN)

```
Mensaje: manual on
```

### Paso 5.3 — Verificar que NO se creó conversación ai_query

```bash
mysql -usip_user -psip_pass sip_edge -e "
  SELECT id, workflow_type, status, peer_number
  FROM sms_conversations 
  WHERE peer_number = '<NUMERO_ADMIN>'
  ORDER BY id DESC LIMIT 3;
"
```

**Esperado:**
- El mensaje "manual on" generó una conversación con `workflow_type = 'emergency'`
- La conversación AI del mismo número NO se vio afectada (sigue `active`)

---

## Prueba 6 — Una conversación AI activa por peer_number (R7)

**Objetivo:** Verificar que no se crean múltiples conversaciones activas.

### Paso 6.1 — Enviar mensajes desde el mismo número

```
Mensaje 1: cuantos pesajes hoy?   (crea conversación)
Mensaje 2: y de ayer?             (reutiliza)
Mensaje 3: gracias                (cierra)
Mensaje 4: hola de nuevo          (crea nueva)
```

```bash
mysql -usip_user -psip_pass sip_edge -e "
  SELECT id, status, created_at 
  FROM sms_conversations 
  WHERE peer_number = '<TU_NUMERO>' AND workflow_type='ai_query'
  ORDER BY created_at;
"
```

**Esperado:**
- Conversación #1: `status = 'completed'` (cerrada por "gracias")
- Conversación #2: `status = 'active'` (nueva, para "hola de nuevo")
- NO hay 2 conversaciones `active` simultáneas para el mismo número

---

## Prueba 7 — Logs de ejecución

**Objetivo:** Verificar que el flujo completo se registra en los logs.

```bash
sudo journalctl -u sip-edge --no-pager -n 100 | grep -i "ai_multi_turn\|AiMultiTurn\|farewell\|archived"
```

**Esperado:**
- Líneas de log con prefijos como `[AiMultiTurn]` o `ai_multi_turn`
- Mensajes de farewell detection cuando se detecta despedida
- Mensajes de archivado diario (si aplica)

---

## Prueba 8 — Manejo de conversación pre-creada por dispatcher (R1 + design §14)

**Objetivo:** Verificar que el handler AI reutiliza la conversación `unknown` del dispatcher.

```bash
# Después de enviar un SMS de consulta AI, verificar:
mysql -usip_user -psip_pass sip_edge -e "
  SELECT id, workflow_type, status
  FROM sms_conversations 
  WHERE peer_number = '<TU_NUMERO>'
  ORDER BY created_at DESC LIMIT 1;
"
```

**Esperado:**
- `workflow_type = 'ai_query'` (NUNCA `'unknown'` después de procesar)
- No hay 2 conversaciones para el mismo SMS (una `unknown` + una `ai_query`)

---

## Resumen de verificación

| Prueba | R cubierto | Criterio de éxito |
|--------|-----------|---------------------|
| P1.1 | R1, R7 | Conversación ai_query creada con message_history |
| P1.2 | R2, R4 | Contexto se mantiene entre mensajes |
| P1.3 | R2, R6 | message_history sin tool_calls |
| P2 | R3, R10 | FIFO limita a 10 exchanges |
| P3 | R8 | "gracias" cierra conversación a completed |
| P4 | R5, R6 | sms_ai_tool_log registra tool_calls |
| P5 | R11 | "manual on" se procesa como emergencia, no AI |
| P6 | R7 | Máximo 1 conversación active por número |
| P7 | — | Logs confirman ejecución |
| P8 | R1+§14 | Dispatcher conversation reutilizada, no duplicada |
