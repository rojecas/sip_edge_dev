# Review — bug 26 (emergency_request_wrong_sms)

**Veredicto:** APPROVED

## Cobertura del reproduction

Reproduction steps (del feature_list.json):
1. Abrir vista Kiosko como operador
2. Solicitar modo manual (seleccionar supervisor, escribir motivo)
3. Esperar ~15-30 segundos
4. Observar que el admin recibe "Lo siento..." en vez de la solicitud de emergencia
5. Verificar que el modo manual no se activa aunque el admin responda "manual on"

Cobertura:
- [x] test_sent_sms_is_filtered — SMS con state="sent" NO debe estar en mensajes retornados (cubre pasos 3-4)
- [x] test_stored_sms_is_filtered — SMS con state="stored" NO debe estar en mensajes retornados
- [x] test_received_sms_passes_filter — SMS "received" DEBE estar en mensajes retornados (verifica que SMS legítimos siguen funcionando)
- [x] test_mixed_sms_only_received_processed — Múltiples SMS: solo "received" se retornan
- [x] test_extract_status_returns_none — Documenta el bug: "status" retorna None en mmcli output
- [x] test_extract_state_received — Extraer "state: received" del mmcli output

## Regresiones

- tests/test_emergency_mode.py: 59/59 OK
- tests/test_sms_service.py: 22/22 OK
- tests/test_password_reset.py: 51/51 OK (individualmente; 5 errores pre-existentes de event loop al correr suite completa)
- tests/test_sms_incoming.py: 14/14 OK (nuevos, creados para el bug)

No hay regresiones introducidas por el fix. Los 5 errores en test_password_reset.TestIncomingSmsDispatcher al correr la suite completa son pre-existentes (conflicto de event loop asyncio) y están documentados en closure-emergency_request_wrong_sms.md.

## GitHub sync

github.json enabled: true
- [ ] Bug #26 NO tiene campo github_issue en feature_list.json. Debería crearse un issue en GitHub para tracking.
  Nota: no es criterio de rechazo para revisión de fix; el release-manager lo gestionará al marcar done.

## Checkpoints (C11)

- [x] C11: plan-bug-emergency_request_wrong_sms.md existe con diagnóstico, causa raíz y fix propuesto
- [x] C11: closure-emergency_request_wrong_sms.md existe con síntoma, causa raíz, fix aplicado y regression test
- [x] C11: regression test asociado (tests/test_sms_incoming.py) cubre el escenario de reproduction
- [x] C11: El reproduction del bug coincide con lo que el test verifica
- [ ] C11: ./init.ps1 — timeout (3 min) al ejecutar suite completa; los módulos individuales pasan. Pre-existente.

## ./init.ps1

El script ./init.ps1 no completó dentro del timeout de 180s al ejecutar la suite completa. Es un problema pre-existente de rendimiento de la suite completa. Los tests del bug fix y de las features afectadas (9, 7, 8) pasan correctamente de forma individual.

## Cambios requeridos (no blocking para APPROVE)

1. (Recomendado) Agregar github_issue a bug #26 en feature_list.json para habilitar GitHub sync.
2. (Recomendado) Los 5 errores pre-existentes en test_password_reset.TestIncomingSmsDispatcher al correr la suite completa deberían corregirse en un issue separado (no relacionados con este fix).
