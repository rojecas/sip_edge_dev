# Closure Report - Feature 28: ai_multi_turn

**Fecha:** 2026-07-16
**Release:** v1.4.0
**Status:** DONE

## Resumen

Extension del sistema de consultas AI via SMS para soportar conversaciones multiturno sobre la infraestructura de sms_conversations/sms_messages (Feature 27). Mantiene historial de hasta 10 exchanges (FIFO, texto plano sin tool_calls), tabla sms_ai_tool_log para auditoria, deteccion de despedidas, y archival a 90 dias.

## Componentes entregados

| Componente | Archivo | Estado |
|------------|---------|--------|
| AI multi-turn handler | src/ai_multi_turn.py | DONE |
| Dispatcher conversation_id fix | src/sms_dispatcher_v2.py | DONE |
| get_active_conversation_by_peer_any_type | src/sms_persistence.py | DONE |
| SMS sanitization | src/sms_service.py | DONE |
| Defense-in-depth password_reset | src/password_reset.py | DONE |
| Defense-in-depth emergency_mode | src/emergency_mode.py | DONE |
| Tabla sms_ai_tool_log | database/migrations/ | DONE |
| Spec SDD | harness/specs/28_ai_multi_turn/ | DONE |

## Tests
- 261 tests green across 8 SMS-adjacent modules
- Regression test: test_dispatch_reuses_active_conversation_for_same_peer
- 10 new sanitization tests in test_sms_service.py
- 16 pre-existing failing tests fixed (whitelist setup + handler signatures)

## Verificacion en EdgeBox (EB1)
- Deploy: cac715d fast-forward, servicio active
- Health check: HTTP 200 {"status":"healthy"}
- Logs arranque: limpio, DispatcherV2 polling iniciado, modem auto-detectado
- Pruebas manuales multiturno: OK (usuario autorizo cierre)

## Testing-phase fixes
1. **conversation_id bug**: _dispatch() creaba conversacion unknown por cada SMS entrante. Fix: reutiliza conversacion activa del peer (cualquier workflow_type).
2. **SMS sanitization**: _sanitize_sms_text() trunca a 160 chars y reemplaza / con - (mitiga filtro SMSC de Tigo).
3. **Defense-in-depth**: null-checks en password_reset.handle_incoming_sms y emergency_mode.process_incoming_sms.

## Issues conocidos
- SMSC Tigo filtra la palabra "Mina" en ambas direcciones. Mitigado via sanitization y cambio de nombre del operador. No es bug del app.
