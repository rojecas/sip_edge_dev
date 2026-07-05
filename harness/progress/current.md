# Sesion actual

- **Inicio:** 2026-07-03
- **Fin:** 2026-07-05
- **Agente:** leader (deepseek-v4-pro)
- **Features:** F27 (sms_persistence), Bug 26, F12 (password_reset_sms)
- **SIMs quemadas:** 2 (vieja + nueva) por spam sin rate limiter

## Lo que FUNCIONA

| Componente | Archivo | Estado |
|---|---|---|
| DRY_RUN (0 SMS reales) | sms_service.py + .env | ACTIVO |
| Filtro autorizacion admin/corresponsal | sms_dispatcher_v2.py | OK |
| Rate limiter 60s | sms_send_queue.py | OK |
| DeepSeek backend primario | llm_client.py (DualBackendClient) | OK |
| Circuit breaker | llm_client.py | OK |
| Dispatch en thread (anti-watchdog) | sms_dispatcher_v2.py | OK |
| Role context para corresponsal | agent_orchestrator.py | OK |
| _has_data gate eliminado | agent_orchestrator.py | OK |
| tool_choice=required | llm_client.py | OK |
| Migracion tipo_cosecha en EdgeBox | weighings | OK |
| Schemas local/remoto identicos | - | OK |

## Lo que NO funciona

| Problema | Causa probable |
|---|---|
| DeepSeek no usa tools SQL | tool_choice=required aplicado pero LLM sigue respondiendo sin consultar BD. Dice "2024" cuando datos son 2026. |
| SIM bloqueada (QMI error 54) | 2da SIM quemada por loop de mensajes sin rate limiter |
| Pruebas F12 no realizadas | Sin SIM funcional |

## Archivos modificados en la sesion

src/llm_client.py, src/agent_orchestrator.py, src/main.py, src/sms_service.py, src/sms_dispatcher_v2.py, src/sms_send_queue.py, src/emergency_mode.py, tests/test_sms_dispatcher_v2.py, .env (EdgeBox), database/migrations/2026_06_25_*tipo_cosecha*
