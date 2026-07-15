# Sesion \"Nuevas features\" — 2026-07-14/15

## Resumen
Sesion larga multi-objetivo: analisis de solicitud del cliente, creacion de ERS V1.4,
implementacion y correccion de F28 (ai_multi_turn) con pruebas en EdgeBox, y correccion
de multiples bugs en el pipeline de SMS encontrados durante las pruebas.

## Features trabajadas
| ID | Feature | Estado | Notas |
|---|---------|--------|-------|
| 28 | ai_multi_turn | **testing** | Implementada + validada. Conversacion multiturno AI via SMS con FIFO, tool_log, archivado. 3 bugs corregidos en pruebas. |
| 29-32 | sql_tools_v2, alert_monitor, sms_scheduling_v2, sample_imaging | **pending** | Registradas en feature_list.json + ERS_V1_4_Adendas.md |

## Bugs encontrados y corregidos
1. SMS duplicado por ENUM: F27 omitio 'sending' en sms_messages.status. Fix: agregado al ENUM.
2. SMS duplicado por race queue: SendQueue no marcaba 'sending' antes de enviar. Fix: queue ahora marca sending.
3. Conversaciones AI duplicadas: get_or_create_ai_conversation creaba nueva por cada SMS. Fix: reutiliza ai_query existente.
4. SMS entrantes descartados: deteccion de auto-generados por modem_id era falsa positivo. Fix: eliminada (status != received basta).
5. sudo mmcli pedia password: /etc/sudoers.d/sip-edge no existia. Fix: creado con NOPASSWD.
6. Ambiguedad fechas en multiturno: LLM suponia fechas sin preguntar. Fix: pre-procesamiento inyecta nota de clarificacion.

## Fixes entorno EdgeBox
- Keyring deshabilitado (gnome-keyring autostarts movidos a .disabled)
- Chromium kiosk autostart en /etc/xdg/autostart/kiosk.desktop
- Keypad decimal fijado (kpdl:dot via localectl + autostart)
- sudo NOPASSWD para mmcli documentado en Informe 02

## Documentos generados
- docs/ERS_V1.4_Adendas.md (39 RF + 2 NFR)
- docs/analisis_solicitud_reportes_sms.md
- harness/specs/28_ai_multi_turn/ (spec validado)
- harness/progress/testplan_28_ai_multi_turn.md

## Harness corregido
- AGENTS.md: Caso A ahora incluye spec-validator, Casos B/C trigger cambiado a spec-reviewed
- CHECKPOINTS.md: C7 incluye spec-reviewed y testing

## Pendiente prox sesion
- F28: terminar pruebas manuales → autorizar cierre → release-manager → done
- F29-F35: spec-author para cada una
- Revisar race condition send_sms vs SmsSendQueue (discutir solucion final)

## Estado final
- EdgeBox: /health 200, sudo mmcli OK, SMS funcional
- F28: testing (esperando pruebas manuales)
- F29-F35: pending
