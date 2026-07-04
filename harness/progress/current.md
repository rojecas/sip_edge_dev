# Sesion actual

> Este archivo se vacia al cerrar cada sesion y se mueve a history.md.

- **Inicio:** 2026-07-03 22:30 UTC
- **Fin:** 2026-07-03 (pendiente cierre)
- **Agente:** leader (deepseek-v4-pro)
- **Features trabajadas:** F27 (sms_persistence), Bug 26 (emergency_request_wrong_sms), F12 (password_reset_sms)
- **Estado:** SIM TIGO bloqueada por spam — pruebas manuales SMS pendientes de SIM funcional

---

## Indice de features

| ID | Nombre | Status |
|----|--------|--------|
| 27 | sms_persistence | testing |
| 26 | emergency_request_wrong_sms | triaged |
| 12 | password_reset_sms | done (pendiente verificacion hardware) |
| 25 | virtual_scale | testing |
| 28 | ai_multi_turn | pending |

---

## Resumen de la sesion

### Fase 1 — Despliegue Feature 27 (sms_persistence)
- git push + pull en EdgeBox OK
- Migraciones SQL ejecutadas: sms_conversations, sms_messages creadas
- Servicio sip-edge reiniciado, health check OK
- Dispatcher v2 activo procesando SMS entrantes

### Fase 2 — Bug 26: handler AI catch-all
- Diagnostico: _build_ai_sms_handler() siempre retorna True
- Fix parcial: elimino handler AI del dispatcher (rompia consultas AI)
- Correccion final: handler AI re-registrado con retorno bool (False si LLM falla)
- Regression test agregado

### Fase 3 — Backend AI Dual + Circuit Breaker
- DeepSeek API como backend primario (remote, mas rapido)
- llama.cpp local como secundario (fallback)
- Circuit breaker con exponential backoff (30s -> 300s max)
- SYSTEM_PROMPT actualizado con lista de comandos reconocidos
- Configuracion en .env: DEEPSEEK_API_KEY, AI_PRIMARY_BACKEND=remote

### Fase 4 — Fixes criticos de envio SMS
- SMSC +573003690025 agregado a _send_via_mmcli_sync() (sin SMSC no llegan)
- Dispatch en asyncio.to_thread() (evita bloqueo de event loop + watchdog timeout)
- Rate limiter: minimo 60s entre envios al mismo numero (previene bloqueo TIGO)
- Timestamp de rate limit se actualiza ANTES de intentar envio (previene rafagas en reintentos)

### Fase 5 — Problema: SIM TIGO bloqueada
- ~40 SMS salientes en ~2 min saturaron a TIGO
- QMI error 54 (WmsCauseCode): operador rechaza SMS salientes
- SIM sigue bloqueada al cierre de sesion
- Pruebas manuales F12 y F27 pendientes de SIM funcional

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| src/llm_client.py | api_key param en LlamaClient, nueva clase DualBackendClient |
| src/agent_orchestrator.py | SYSTEM_PROMPT con comandos, handle_sms_query retorna bool |
| src/main.py | Dual backend init, AI handler re-registrado, min_send_interval=60 |
| src/sms_service.py | SMSC +573003690025 en _send_via_mmcli_sync |
| src/sms_dispatcher_v2.py | _dispatch en asyncio.to_thread (anti-watchdog) |
| src/sms_send_queue.py | Rate limiter: _wait_rate_limit + min_send_interval |
| tests/test_sms_dispatcher_v2.py | test_no_catchall_handler_bug26_regression |
| .env (EdgeBox) | DEEPSEEK_API_KEY, AI_PRIMARY_BACKEND, DEEPSEEK_MODEL |
| database/migrations/ | 2026_07_02_*_sms_conversations.sql, *_sms_messages.sql |

## Pendientes para proxima sesion

1. **SIM nueva o SIM desbloqueada** — prerequisito para cualquier prueba SMS
2. Probar F27 end-to-end: enviar "hola" -> verificar respuesta DeepSeek en telefono
3. Probar F12: "reset password <usuario>" -> verificar PIN recibido
4. Probar emergencia: "manual on" desde admin -> verificar activacion
5. Si todo OK -> release-manager para F27 y Bug 26
6. Sincronizar cambios locales con EdgeBox (git pull)
