# Sesion actual - 2026-07-05

- **Inicio:** 2026-07-05
- **Agente:** leader (deepseek-v4-pro) + bug-fixer (deepseek-reasoner)
- **Enfoque:** Debugging flujo SMS+LLM - DeepSeek no llamaba tools SQL
- **SIM:** Bloqueada (QMI error 54). SMS_DRY_RUN=true.

## Bugs resueltos en esta sesion

### Bug A — tool_choice=required en segunda vuelta (CRITICO)
**Sintoma:** DeepSeek respondia "Sin respuesta." en consultas SMS.
**Causa raiz:** 	ool_choice=required se aplicaba tambien en la segunda vuelta
(parafraseo), forzando a DeepSeek a llamar tools otra vez en vez de generar texto.
**Fix:** chat_completion() acepta 	ool_choice param. Segunda vuelta usa 	ools=None.
system prompt incluye "ano actual es 2026" para evitar alucinacion de fechas.
**Commit:** 257aeab

### Bug B1 — SMS huerfanos en modem al fallar envio
**Sintoma:** Loop infinito: SMS de respuesta fallido quedaba en modem, dispatcher
lo detectaba como entrante, lo procesaba de nuevo.
**Causa raiz:** _send_via_mmcli_sync() creaba objeto SMS en modem via --messaging-create-sms,
pero si --send fallaba, el objeto quedaba huerfano.
**Fix:** _delete_orphan_sms() en los 3 paths de fallo (returncode, timeout, OSError).
**Commit:** 79be573

### Bug B2 — Dispatcher no filtraba estado unknown
**Sintoma:** SMS huerfanos en estado "unknown" (sin campo state en mmcli) pasaban
el filtro del dispatcher y se trataban como entrantes.
**Causa raiz:** Condicion if status and status.lower() != "received" - si status=None,
None es falsy y no entraba al filtro.
**Fix:** if not status or status.lower() != "received" - None tambien se filtra.
**Commit:** 79be573

### Bug B3 — SMS_DRY_RUN no protegia send queue
**Sintoma:** A pesar de SMS_DRY_RUN=true, los mensajes se persistian como "pending"
y el send queue los recogia e intentaba enviar via mmcli.
**Causa raiz:** send queue llama a _send_via_mmcli_sync() directamente, bypassando
send_sms() donde estaba el guardia DRY_RUN.
**Fix:** DRY_RUN agregado en _send_with_retry() del send queue. send_sms() y
send_sms_sync() tambien protegidos.
**Commit:** 431e56c

### modem_sms_id (correccion de diseño F27)
**Sintoma:** Columna modem_sms_id existia en schema pero nunca se poblaba (ni para
entrantes ni salientes). Era un bug de implementacion de F27.
**Fix:** _send_via_mmcli_sync() guarda modem_sms_id tras envio exitoso.
create_message() acepta modem_sms_id. _fetch_mmcli_sms() propaga sms_id al dispatch.
Dispatcher usa message_exists_by_modem_id() para saltar auto-generados.
**Commit:** 431e56c, db337a0

## Hallazgos de la prueba con LLM local (Qwen 1.5B)

### Configuracion actual EdgeBox
| Componente | Puerto | Estado |
|-----------|--------|--------|
| sip-edge | 8000 | Activo |
| llama-server (Qwen 1.5B) | 8080 | Activo (taskset -c 0-2, -t 3) |
| phpMyAdmin | 8081 | Activo |
| AI_PRIMARY_BACKEND | - | local |
| llm_timeout | - | 240s (4 min) |

### Rendimiento observado (llama-server logs)

| Metrica | Primera vuelta (con tools) | Segunda vuelta (sin tools) |
|---------|---------------------------|---------------------------|
| Prompt processing | 141 tokens, 36.66s (3.85 t/s) | 56 tokens, 10.62s (5.27 t/s) |
| Generacion | 104 tokens, 1.37 t/s | 16 tokens, 3.08 t/s |
| Contexto total | ~2315 tokens (2174 en tool definitions) | ~400 tokens (cacheado) |
| Tiempo total | ~110s (casi cancelado por timeout 120s) | 35s completado OK |

### Cuello de botella identificado
Las 12 tool definitions SQL ocupan ~2174 tokens del prompt. Para el LLM local
(1.5B en Cortex-A72 sin DOTPROD), procesar eso toma ~36s solo en prompt evaluation.
Una optimizacion futura (F28) seria seleccionar dinamicamente solo las tools
relevantes segun la consulta, reduciendo el prompt a ~400 tokens y la respuesta
a segundos.

## Pendientes para proxima sesion

| Item | Status | Nota |
|------|--------|------|
| Bug 26 (emergency_request_wrong_sms) | triaged | Bug-fixer pendiente |
| F27 (sms_persistence) | testing | Espera pruebas manuales + autorizacion para done |
| F28 (ai_multi_turn) | pending | Incluira optimizacion tools + sms_ai_tool_log |
| SIM nueva | - | No insertar hasta que DRY_RUN confirme todo el flujo |
| Restaurar AI_PRIMARY_BACKEND=remote | - | Cuando se quiera DeepSeek como primario otra vez |
