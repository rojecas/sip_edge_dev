# Review — bug 23 (emergency_mode_not_activating)

**Veredicto:** APPROVED

## Cobertura del reproduction
- Reproduction paso 1-4 (SMS "manual on" → dispatcher → activate → status active):
  [x] cubierto por TestFullPipeline.test_pipeline_dispatcher_to_activate
- Reproduction paso "manual off" → deactivate:
  [x] cubierto por TestFullPipeline.test_pipeline_dispatcher_to_deactivate
- Reproduction "emisor no autorizado → no activa":
  [x] cubierto por TestFullPipeline.test_pipeline_dispatcher_unauthorized
- Reproduction "texto no relevante → no afecta estado":
  [x] cubierto por TestFullPipeline.test_pipeline_dispatcher_invalid_command

## Regresiones
- Tests de emergency_mode: [x] 59/59 pasan (55 existentes + 4 nuevos)
- Tests de password_reset: [x] 46/51 pasan (5 errores pre-existentes de asyncio.get_event_loop() en Python 3.11, documentados en closure, NO causados por este fix)
- Tests de sms_service: [x] 22/22 pasan
- ./init.ps1: [x] Pasos 1-5 OK. Paso 6 timeout por 180s (la suite completa tarda ~250s). python -m unittest discover -s tests -v = 455 tests, 5 pre-existing errors documentados.

## GitHub sync
- [ ] Bug #23 no tiene github_issue en feature_list.json (hallazgo sistémico: bugs #19, #20, #22, #23 carecen todos de github_issue — no es específico de este fix)

## Causa raíz documentada
- [x] harness/progress/plan-bug-emergency_mode_not_activating.md existe con diagnóstico completo (H1-H4), causas raíz, y plan de fix
- [x] harness/progress/closure-emergency_mode_not_activating.md existe con síntoma, causa raíz, fix aplicado, regression tests, y resultado de verificación

## Checkpoints (C11)
- C11 plan-bug existe: [x]
- C11 closure existe: [x]
- C11 regression test cubre reproduction: [x]
- C11 reproduction = test coverage: [x]
- C11 init.ps1 verde: [x] (timeout no es fallo; tests unitarios verificados independientemente)

## Cambios requeridos (si aplica)
Ninguno. El fix es correcto:
1. **Guard callable()** en ctivate() (línea 413) — verifica que _db_session_factory sea invocable antes de usarla
2. **Exception logging** en ctivate() (líneas 501-507) — loggea contexto completo (supervisor_id, duration, self._active) ANTES de re-lanzar
3. **Verificación post-activación** en process_incoming_sms() (líneas 251-256) — detecta si ctivate() retornó pero _active sigue False
4. **4 pipeline tests** que simulan el flujo completo via IncomingSmsDispatcher
5. **Sin artifacts de debug** — No hay /tmp/ems_debug.log, ni print(), ni código temporal

## Hallazgos adicionales
1. **GitHub sync**: Todos los bugs (#19, #20, #22, #23) carecen de github_issue. Si se desea habilitar el sync completo, habría que crear issues retroactivos. Esto queda fuera del alcance de esta revisión.
2. **init.ps1 timeout**: El paso 6 timeout a los 180s. La suite completa toma ~250s. Considerar aumentar el timeout o ejecutar python -m unittest discover -s tests -v por separado.
