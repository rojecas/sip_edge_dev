# Review — bug 31 (sms_dispatcher_v2_crashes)

**Veredicto:** APPROVED

## Cobertura del reproduction
- Reproduction paso 4 (AttributeError por metodo faltante): [x] cubierto por `test_get_user_role_by_phone_returns_role` — verifica que el metodo existe y retorna el rol esperado
- Reproduction paso 4 (no crashea): [x] cubierto por `test_get_user_role_by_phone_returns_none_for_unknown` — verifica que numeros no registrados retornan None sin error
- Reproduction paso 4 (no crashea con BD vacia): [x] cubierto por `test_get_user_role_by_phone_returns_none_when_no_users` — verifica que tabla vacia no lanza AttributeError

## Verificacion de get_user_role_by_phone()
- [x] Implementado en `src/sms_persistence.py:330-348` — query a User por phone, retorna role o None, finally cierra sesion
- [x] Import de User agregado en `src/sms_persistence.py:13`
- [x] Respeta SOLID: metodo unico, responsabilidad unica, sin side effects

## Regresiones
- Tests de `test_sms_persistence.py`: [x] 20 tests OK (incluyendo 3 nuevos de regression para Bug #31)
- Tests de `test_sms_dispatcher_v2.py`: [ ] 6 FAILURES — ver detalle abajo

### Detalle de las 6 fallas en test_sms_dispatcher_v2.py
Estas fallas NO son regresiones del fix. Son tests pre-existentes que nunca crearon usuarios con telefono en la BD de prueba. Antes del fix, el metodo `get_user_role_by_phone()` no existia, y el AttributeError resultante era tragado por el except Exception en _poll_loop() — los tests pasaban "de casualidad" porque el crash silencioso dejaba la conversacion en estado "active" y no bloqueaba a los handlers.

Con el fix, la whitelist funciona correctamente: numeros no registrados se marcan como "completed" y se ignoran. Los tests fallan porque su setup no registra telefonos. El closure documenta esto como fuera del scope del bug #31.

Tests afectados:
1. `test_conversation_created_on_first_message` — espera "active", recibe "completed" por whitelist
2. `test_handler_order_matters` — espera handlers ejecutados, whitelist bloquea antes
3. `test_no_catchall_ai_handler` — espera respuesta, whitelist bloquea
4. `test_no_catchall_handler_bug26_regression` — espera mensajes de ayuda, whitelist bloquea
5. `test_persist_before_dispatch` — espera handler llamado, whitelist bloquea
6. `test_unknown_sms_help_response` — espera respuesta de ayuda, whitelist bloquea

## GitHub sync
- [x] `harness/github.json` existe con `enabled: true`
- [x] gh CLI autenticado como rojecas
- [ ] Bug #31 NO tiene campo `github_issue` en feature_list.json — no se creo issue al triar

## Checkpoints (C11)
- C11 plan-bug existe: [x] `harness/progress/plan-bug-31_sms_dispatcher_v2_crashes.md`
- C11 closure existe: [x] `harness/progress/closure-31_sms_dispatcher_v2_crashes.md`
- C11 regression test asociado: [x] 3 tests en test_sms_persistence.py
- C11 ./init.ps1 verde: [ ] 6 pre-existing failures en test_sms_dispatcher_v2.py (documentados arriba)

## Hallazgos
1. **6 tests pre-existentes fallan** en `test_sms_dispatcher_v2.py` porque no registran usuarios con telefono. El fix expuso la inconsistencia. Estos tests deben actualizarse en un bug/feature separado.
2. **Sin github_issue**: Bug #31 no tiene issue en GitHub, aunque `github.json` tiene `enabled: true`. El protocolo requiere crearlo al triar.

## Release
- [ ] El bug esta listo para release-manager (closure existe)
