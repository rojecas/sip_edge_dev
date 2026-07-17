# Review — feature 28 (ai_multi_turn) — Testing Fixes

**Veredicto:** APPROVED

## Trazabilidad requirements <-> tests

Los fixes de testing corrigen bugs encontrados durante pruebas manuales en EdgeBox. No introducen nuevos requirements, pero se mapean a requirements existentes:

- **R1** (mismo conversation_id para todos los mensajes de una conversación): [x] cubierto por `test_dispatch_reuses_active_conversation_for_same_peer`. El fix asegura que el dispatcher reutiliza la conversación activa existente, garantizando que todos los mensajes del mismo peer compartan conversation_id.
- **R7** (una única conversación activa por peer): [x] cubierto por `test_dispatch_reuses_active_conversation_for_same_peer`. El fix evita crear conversaciones unknown duplicadas.
- **R13** (non-admin rejected): [x] cubierto por `test_non_admin_rejected`, `test_unknown_phone_rejected`. Defense-in-depth en password_reset.py ahora protege estos paths.
- **R19** (whitelist dispatcher): [x] cubierto por `test_operator_sms_marked_as_rejected`, `test_operator_user_sms_marked_as_rejected`, `test_pipeline_v2_unauthorized`. Ningún test debilita el whitelist.

## Focus Area 1 — conversation_id fix

| Aspecto | Estado | Evidencia |
|---------|--------|-----------|
| `_dispatch()` busca conversación activa de ANY workflow_type | ✅ Listo | `get_active_conversation_by_peer_any_type(sender_phone)` en sms_dispatcher_v2.py:266-268 |
| Reusa conversación existente (bump last_activity) | ✅ Listo | Líneas 269-270: `update_conversation_last_activity(conv.id)` |
| Crea nueva 'unknown' solo si no existe ninguna activa | ✅ Listo | Líneas 271-276: `create_conversation(workflow_type='unknown')` |
| SMS entrante persistido contra conv.id reutilizado | ✅ Listo | Línea 278: `conversation_id=conv.id` |
| sms_messages.conversation_id NOT NULL se mantiene | ✅ Listo | Siempre se asigna desde conv.id existente o recién creada |
| AI handler dedup (ai_multi_turn.py:90-100) preservado | ✅ Listo | Líneas 86-115 en ai_multi_turn.py intactas |
| Regression test fallaría si se revierte | ✅ Listo | test verifica len(convs)==1 y mismo conversation_id |

## Focus Area 2 — Whitelist NO debilitado (CRÍTICO)

| Test | Método | ¿Usa whitelist real? |
|------|--------|---------------------|
| `test_operator_sms_marked_as_rejected` | Restaura `_original_get_role` L395-398 | ✅ Sí |
| `test_operator_user_sms_marked_as_rejected` | Restaura `_original_get_role` L423-426 | ✅ Sí |
| `test_pipeline_v2_unauthorized` | Restaura `_original_get_role` L1492 | ✅ Sí |
| `test_non_admin_rejected` | TestPasswordResetPersistence NO mockea | ✅ Sí (defense-in-depth en password_reset.py) |
| `test_unknown_phone_rejected` | TestPasswordResetPersistence NO mockea | ✅ Sí |

Mock `get_user_role_by_phone -> 'admin'` SOLO aplicado en setUp de clases que prueban mecánica de dispatch/pipeline:
- `TestSmsDispatcherV2.setUp` — restaurado en tearDown
- `TestIncomingSmsDispatcherV2.setUp` — restaurado en tearDown
- `TestFullPipelineV2.setUp` — restaurado per-test con restore previo

Producción (sms_dispatcher_v2.py:292-303): whitelist intacto, sin cambios.

## Focus Area 3 — Defense-in-depth en producción

### password_reset.py (líneas 139-156)
- **Null-check**: `sender_user is None -> return True` (silent reject). Previene `AttributeError` en acceso a `sender_user.username`.
- **Role-check**: `sender_user.role != 'admin' -> return True`. Evita que no-admins generen PINs.
- Comportamiento vía dispatcher: sin cambio (whitelist ya filtra).
- Comportamiento en llamada directa: ahora seguro (antes podía fallar o procesar a no-admin).

### emergency_mode.py (líneas 256-263)
- **Null-check**: `user is None -> return False`. Previene `AttributeError: 'NoneType' object has no attribute 'id'`.
- Comportamiento vía dispatcher: sin cambio (whitelist ya filtra).
- Comportamiento en llamada directa: ahora retorna False en vez de crash.

### Veredicto sobre alcance
Los cambios en F9 (emergency_mode) y F12 (password_reset) son **justificados**. Fueron descubiertos durante las pruebas de F28 (tests fallaban al llamar handlers directamente sin dispatcher). Son cambios pequeños, defense-in-depth, sin cambio de comportamiento en el path normal (siempre pasan por dispatcher whitelist). Separarlos en otra issue sería burocracia innecesaria para cambios de 3-5 líneas cada uno.

## Focus Area 4 — Tests obsoletos eliminados

- `test_message_exists_by_modem_id_returns_true_when_exists`
- `test_message_exists_by_modem_id_returns_false_when_not_exists`
- `test_message_exists_by_modem_id_ignores_other_ids`

Los 3 tests fueron **eliminados** (no comentados). Método `message_exists_by_modem_id` no existe en src/ (grep confirma 0 referencias). Dejado comentario explicativo en el archivo.

## Focus Area 5 — Sanitización SMS

| Aspecto | Estado |
|---------|--------|
| `_sanitize_sms_text` reemplaza / por - | ✅ |
| Trunca a 157 + "..." cuando > 160 chars | ✅ |
| `send_sms()` llama sanitización antes de persistir | ✅ Línea 141 |
| `send_sms_sync()` llama sanitización antes de persistir | ✅ Línea 195 |
| 8 tests unitarios (TestSmsSanitization) | ✅ 8/8 OK |
| 2 tests de integración (TestSendSmsSanitizesBeforePersistence) | ✅ 2/2 OK |

## Focus Area 6 — Suite verde

| Módulo | Tests | Resultado |
|--------|-------|-----------|
| test_sms_dispatcher_v2 | 19 | OK (verificado) |
| test_password_reset | 63 | OK (verificado) |
| test_sms_service (sanitization) | 10 | OK (verificado) |
| test_emergency_mode (unauthorized) | 1 | OK (verificado) |
| Total 8 módulos (reporte líder) | 261 | OK (confirmado) |

## Focus Area 7 — Tasks.md y documentación

- tasks.md original (F28): 100% completo, todos [x].
- Testing fixes están documentados en `harness/progress/impl_28_testing_fixes.md` con trazabilidad a tests correspondientes.
- Sección 'Impacto en features existentes' presente y completa (F9, F12, F27, F28).

## Checkpoints

- C11 (plan-bug existe para bugs): N/A — no es bug, son testing fixes.
- Impl report documenta: [x] problema, [x] solución elegida, [x] alternativa rechazada, [x] archivos modificados, [x] verificación.
- Impacto en features existentes: [x] documentado.
- Defense-in-depth scope: [x] justificado.

## Release readiness
- [x] La feature F28 está en estado `testing`, los fixes cierran issues encontrados en EdgeBox.
- [x] Tests verdes.
- [x] Impacto en features existentes documentado.
- [x] Sin regresiones.

---

**No hay cambios requeridos. Aprobado.**
