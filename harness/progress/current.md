# Sesion "continuacion debug Bug28" — 2026-07-16

## Resumen
Sesion de cierre de F28 (ai_multi_turn): fix del bug conversation_id en dispatcher,
sanitizacion SMS, defense-in-depth, limpieza de 16 tests, release v1.4.0 y despliegue en EB1.

## Features trabajadas
| ID | Feature | Estado | Notas |
|---|---------|--------|-------|
| 28 | ai_multi_turn | **done** | Liberado en v1.4.0. Conversacion multiturno AI via SMS. |
| 29-32 | sql_tools_v2, alert_monitor, sms_scheduling_v2, sample_imaging | **pending** | Sin cambios. |

## Fixes realizados
1. **conversation_id dispatcher**: _dispatch() reutiliza conversacion activa del peer (cualquier workflow_type) en vez de crear unknown por cada SMS entrante.
2. **SMS sanitization**: _sanitize_sms_text() en sms_service.py (trunca 160, reemplaza / con -).
3. **Defense-in-depth**: null-checks en password_reset.handle_incoming_sms y emergency_mode.process_incoming_sms.
4. **16 tests arreglados**: whitelist setup + handler signatures en test_password_reset, test_emergency_mode, test_sms_persistence. 3 tests obsoletos eliminados.

## Release
- **v1.4.0** — F28 (feature) + bugs #29 #30 #31
- Commit: 577197a
- Tag: v1.4.0
- GitHub: https://github.com/rojecas/sip_edge/releases/tag/v1.4.0
- Deploy EB1: cac715d fast-forward, servicio healthy

## Verificacion
- 261 tests green (8 modulos SMS-adjacentes)
- Reviewer: APPROVED
- EB1 health: HTTP 200, logs limpios
- Pruebas manuales: OK (usuario autorizo cierre)

## Pendiente prox sesion
- F29-F32: spec-author para cada una
- EB1 untracked files (scripts/, docs/) — considerar .gitignore
- EB1 src/static/index.html modificacion local — investigar
