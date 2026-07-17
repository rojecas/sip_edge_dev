# Implementación — Fixes de Testing para Feature 28 (ai_multi_turn)

> Fecha: 2026-07-16
> Feature: 28 — ai_multi_turn (en estado `testing`)
> Sesión: Corrección de 3 issues encontrados durante pruebas manuales en EdgeBox

---

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/sms_persistence.py` | Añadido `get_active_conversation_by_peer_any_type()` (nuevo método) |
| `src/sms_dispatcher_v2.py` | Modificado `_dispatch()`: reutiliza conversación activa existente en vez de crear nueva `unknown` |
| `tests/test_sms_dispatcher_v2.py` | Añadido `test_dispatch_reuses_active_conversation_for_same_peer`, mock de `get_user_role_by_phone` en `setUp`, corregidos handlers de 2-arg a 4-arg, actualizado `test_sms_with_existing_modem_id_is_skipped` |
| `tests/test_sms_service.py` | Añadidas clases `TestSmsSanitization` (8 tests) y `TestSendSmsSanitizesBeforePersistence` (2 tests) |

---

## Tarea 1 — Fix conversation_id bug en _dispatch()

### Problema
`_dispatch()` en `sms_dispatcher_v2.py` llamaba a `get_or_create_active_conversation(peer_number=sender_phone, workflow_type="unknown")`. Este método en `sms_persistence.py:74` filtra por `workflow_type == "unknown" AND status == "active"`. En el 2do+ mensaje entrante del mismo peer, la conversación ya fue actualizada de `unknown` a `ai_query` por el handler AI → no hay `unknown` activa → se crea una NUEVA conversación `unknown` cada vez. Resultado: mensajes entrantes y salientes aterrizan en conversaciones diferentes → `message_history` se rompe → contexto multiturno perdido.

### Solución elegida
**Nuevo método `get_active_conversation_by_peer_any_type(peer_number)` en `SmsPersistenceService`** que busca CUALQUIER conversación activa (`status == "active"`, sin filtrar por `workflow_type`). En `_dispatch()`, primero se busca si existe una conversación activa para ese peer. Si existe, se reutiliza (bump de `last_activity`). Si no, se crea una nueva `unknown`.

### Alternativa rechazada
Sobrecargar `get_or_create_active_conversation` o modificar su semántica. Rechazado porque:
- El método existente tiene una semántica clara: "dame o crea una de tipo X". Cambiarlo a "dame o crea de cualquier tipo" confundiría a otros callers.
- Un nuevo método con nombre explícito (`get_active_conversation_by_peer_any_type`) documenta la intención.

### Defensa en profundidad
El handler AI en `ai_multi_turn.py:90-100` mantiene su lógica de dedup (si `conversation_id` es provisto y es `unknown`, busca `ai_query` activa existente y completa la `unknown`). Con el fix del dispatcher, esta lógica se vuelve no-op en el caso normal (la conversación ya es `ai_query` y activa → línea 109 la reutiliza). No se elimina: sirve como defensa para casos edge (ej: dos SMS casi simultáneos que ambos crean `unknown`).

### Código nuevo en `sms_persistence.py`
```python
def get_active_conversation_by_peer_any_type(
    self, peer_number: str,
) -> SmsConversation | None:
    """Busca CUALQUIER conversacion activa para un peer_number,
    sin filtrar por workflow_type."""
    db: Session = self._db_session_factory()
    try:
        return (
            db.query(SmsConversation)
            .filter(
                SmsConversation.peer_number == peer_number,
                SmsConversation.status == "active",
            )
            .order_by(SmsConversation.last_activity.desc())
            .first()
        )
    finally:
        db.close()
```

### Código modificado en `sms_dispatcher_v2.py` (`_dispatch()`, líneas 262-278)
Reemplaza la llamada a `get_or_create_active_conversation(workflow_type="unknown")` por:
1. `get_active_conversation_by_peer_any_type(sender_phone)` → si existe, `update_conversation_last_activity`
2. Si no existe, `create_conversation(workflow_type="unknown")`

---

## Tarea 2 — Fix 7 failing tests en test_sms_dispatcher_v2.py

### Causa raíz de los fallos
Dos problemas independientes:
1. **Whitelist:** `_dispatch()` línea 286 llama a `get_user_role_by_phone()`. Los tests no registraban `User` en la DB de prueba → `role=None` → SMS rechazado antes de llegar a handlers.
2. **Signatura de handlers:** Varios tests usaban handlers con 2 argumentos (`lambda p, t: ...`) pero el dispatcher v2 llama con 4 argumentos (`handler(sender_phone, trimmed_text, msg.id, conv.id)`) → `TypeError` tragado por `except Exception` → `handled=False`.

### Solución
**Mock global de `get_user_role_by_phone` en `setUp`** que retorna `"admin"` para todos los números. Esto evita:
- Registrar usuarios en DB (que causaba falsos positivos por normalización de teléfonos: `"3001234567"` normaliza a `["3001234567", "573001234567"]` y matcheaba usuarios de otros tests).
- Complejidad de registrar usuarios individualmente en cada test.

En `tearDown` se restaura el método original. Los tests que necesitan el comportamiento real de whitelist (`test_operator_sms_marked_as_rejected`, `test_operator_user_sms_marked_as_rejected`) restauran el método original explícitamente.

**Corrección de handlers 2-arg → 4-arg:**
- `test_persist_before_dispatch`: `my_handler(sender_phone, text)` → `my_handler(sender_phone, text, message_id=None, conversation_id=None)`
- `test_handler_order_matters`: `handler_a(p, t)` → `handler_a(p, t, *args)`
- `test_no_catchall_handler_bug26_regression`: `emergency_handler(sender_phone, text)` → `emergency_handler(sender_phone, text, *args)`
- `test_no_catchall_ai_handler`: `lambda p, t: False` → `lambda p, t, *args: False`
- `test_conversation_created_on_first_message`: `lambda p, t: True` → `lambda p, t, *args: True`
- `test_incoming_sms_stores_modem_sms_id`: `lambda p, t: True` → `lambda p, t, *args: True`
- `test_persist_before_dispatch_message_exists`: `lambda p, t: ...` → `lambda p, t, *args: ...`

**`test_sms_with_existing_modem_id_is_skipped`:** El código de producción eliminó el filtro por `modem_sms_id` en `_fetch_mmcli_sms()` (el comentario en línea 204 explica que el filtro por `status != "received"` es suficiente). La aserción del test esperaba 0 mensajes; se actualizó a esperar 1 mensaje (el SMS con `state=received` se retorna normalmente). Nombre y docstring actualizados para reflejar el nuevo comportamiento.

---

## Tarea 3 — Tests de sanitización SMS

Añadidos 10 tests en `tests/test_sms_service.py`:

### `TestSmsSanitization` (8 tests unitarios de `_sanitize_sms_text`)
| Test | Cobertura |
|------|-----------|
| `test_sanitize_replaces_slash_with_dash` | `/` → `-` |
| `test_sanitize_replaces_multiple_slashes` | Múltiples `/` → `-` |
| `test_sanitize_truncates_long_text` | >160 chars → 157 + `"..."` |
| `test_sanitize_exactly_160_chars_unchanged` | 160 chars exactos sin cambio |
| `test_sanitize_short_text_unchanged` | Texto corto sin slash intacto |
| `test_sanitize_short_text_with_slash_replaced` | Texto corto con slash: solo slash reemplazado |
| `test_sanitize_empty_string` | String vacío → vacío |
| `test_sanitize_159_chars_with_slash_becomes_160_with_dash` | Edge: 159 chars con slash → 159 chars con dash |

### `TestSendSmsSanitizesBeforePersistence` (2 tests de integración)
| Test | Cobertura |
|------|-----------|
| `test_send_sms_persists_sanitized_body` | `send_sms` persiste versión sanitizada (sin `/`) |
| `test_send_sms_persists_truncated_body` | Texto >160 chars se persiste truncado a 160 |

---

## Trazabilidad

| Tarea | Test(s) que la cubren |
|-------|----------------------|
| T1 (conversation_id bug) | `test_dispatch_reuses_active_conversation_for_same_peer` |
| T2 (7 failing tests) | Los 7 tests ahora pasan: `test_conversation_created_on_first_message`, `test_handler_order_matters`, `test_no_catchall_ai_handler`, `test_no_catchall_handler_bug26_regression`, `test_persist_before_dispatch`, `test_unknown_sms_help_response`, `test_sms_with_existing_modem_id_is_skipped` |
| T3 (SMS sanitization) | 8 tests en `TestSmsSanitization` + 2 tests en `TestSendSmsSanitizesBeforePersistence` |

---

## Verificación

### 1. `tests.test_sms_dispatcher_v2` — 19 tests, ALL GREEN
```
Ran 19 tests in 0.458s — OK
```

### 2. `tests.test_sms_service` + `tests.test_agent_orchestrator` + `tests.test_ai_multi_turn` + `tests.test_ai_multi_turn_integration` — 94 tests, ALL GREEN
```
Ran 94 tests in 1.395s — OK
```

### 3. Sanity check — el nuevo test de regresión falla si se revierte el fix
- El test `test_dispatch_reuses_active_conversation_for_same_peer` verifica que 2 SMS del mismo peer terminan en la misma conversación (`len(convs) == 1`, mismo `conversation_id`).
- Si se revierte el fix (usando `get_or_create_active_conversation(workflow_type="unknown")`), el test falla porque se crean 2 conversaciones `unknown` separadas.

### 4. Regresiones — todas corregidas en segunda ronda (ver abajo)

---

## Segunda ronda — Limpieza de tests restantes

> Fecha: 2026-07-16 (misma sesión). Los fixes de la primera ronda dejaron 16 fallos en 3 módulos de tests con las mismas causas raíz: whitelist del dispatcher v2, handlers con signatura 2-arg, y tests obsoletos.

### Bucket A — Tests obsoletos `message_exists_by_modem_id` (test_sms_persistence.py, 3 ERRORs → 0)

- **Tests eliminados**: `test_message_exists_by_modem_id_returns_true_when_exists`, `test_message_exists_by_modem_id_returns_false_when_not_exists`, `test_message_exists_by_modem_id_ignores_other_ids`
- **Razón**: El método `message_exists_by_modem_id` fue intencionalmente removido de `SmsPersistenceService` en commit `c125895`. El dedup por modem_id fue reemplazado por filtrado basado en status (`status != "received"` en `_fetch_mmcli_sms()`).
- **Acción**: Eliminados los 3 tests. Se dejó un comentario explicativo en el archivo.

### Bucket B — Whitelist + 2-arg handlers

#### test_password_reset.py — `TestIncomingSmsDispatcherV2` (6 FAILs → 0)

- **Mock de `get_user_role_by_phone`**: Añadido mock en `setUp` → `"admin"`, restaurado en `tearDown`. Esta clase prueba comportamiento de dispatch (cadena, cola, excepciones), NO el whitelist.
- **Handlers corregidos**: `handler(phone, text)` → `handler(phone, text, *args)` en todos los handlers de la clase: `test_register_and_dispatch`, `test_handler_returns_true_stops_chain`, `test_handler_returns_false_continues_chain`, `test_dev_mode_queue`, `test_handler_exception_does_not_crash_dispatcher`, `test_unhandled_sms_gets_help_response`, `test_v2_persists_conversation`.

#### test_password_reset.py — `TestPasswordResetPersistence` (2 FAILs → 0)

- **`test_non_admin_rejected`** (FAIL): `handle_incoming_sms` no chequeaba el rol del remitente. La función asumía que el dispatcher ya filtra no-admins, pero al ser llamada directamente desde el test, procedía a `generate_and_send_pin` para cualquier remitente encontrado en DB.
- **`test_unknown_phone_rejected`** (ERROR): `AttributeError` en `sender_user.username` cuando `sender_user is None` (teléfono no registrado).
- **Bug genuino en producción**: `password_reset.py:handle_incoming_sms` no validaba que `sender_user` existe ni que su rol sea `"admin"`. **Fix en producción**: añadido null-check (`if sender_user is None → reject`) y role-check (`if sender_user.role != "admin" → reject`). Esto es defensa en profundidad: la función ahora es segura incluso si se llama sin pasar por el dispatcher.

#### test_emergency_mode.py — `TestFullPipelineV2` (3 FAILs → 0)

- **Mock de `get_user_role_by_phone`**: Añadido en `setUp` → `"admin"`. Estos tests verifican el pipeline de activación de emergencia, no el whitelist del dispatcher.
- **`test_pipeline_v2_unauthorized`**: Restaura el método original (`self._original_get_role`) para que el whitelist real rechace el número no registrado. Este test SÍ prueba el whitelist.

#### test_emergency_mode.py — `TestSmsPolling.test_incoming_sms_unknown_sender` (1 ERROR → 0)

- **Bug genuino en producción**: `emergency_mode.py:process_incoming_sms` hacía `user.id` sin verificar que `user is not None`. **Fix en producción**: añadido null-check que retorna `False` silenciosamente para remitentes no registrados.

### Bucket C — `test_get_user_role_by_phone_returns_role` (test_sms_persistence.py, 1 FAIL → 0)

- **Problema**: La función `get_user_role_by_phone` normaliza el teléfono (stripping `+`, probando variantes con/sin código de país). El test registraba usuarios con `phone="+573001234567"` (con `+`), pero `get_user_role_by_phone("+573001234567")` busca `"573001234567"` (sin `+`).
- **Fix**: Se registraron los usuarios con formato normalizado (`phone="573001234567"` y `"573007654321"` sin `+`). Sin cambios en producción.

### Archivos de producción modificados (segunda ronda)

| Archivo | Cambio |
|---------|--------|
| `src/password_reset.py` | `handle_incoming_sms`: añadido null-check para `sender_user` + role-check (`!= "admin"`). Defense-in-depth para llamadas directas sin dispatcher. |
| `src/emergency_mode.py` | `process_incoming_sms`: añadido null-check antes de `user.id`. Retorna `False` para remitentes no registrados. |

### Verificación final

```bash
docker compose exec -T backend python -m unittest \
  tests.test_sms_persistence \
  tests.test_sms_dispatcher_v2 \
  tests.test_sms_service \
  tests.test_password_reset \
  tests.test_emergency_mode \
  tests.test_agent_orchestrator \
  tests.test_ai_multi_turn \
  tests.test_ai_multi_turn_integration -v
```

**Resultado: Ran 261 tests in 75.815s — OK (0 failures, 0 errors)**

---

## Impacto en features existentes

| Feature | Archivo | Impacto | Mitigación |
|---------|---------|---------|------------|
| F27 (sms_persistence) | `src/sms_persistence.py` | Nuevo método `get_active_conversation_by_peer_any_type` | Aditivo, no rompe callers existentes |
| F27 (sms_persistence) | `src/sms_dispatcher_v2.py` | Cambio en lógica de `_dispatch()` | Comportamiento más correcto: reutiliza conversaciones en vez de duplicar |
| F28 (ai_multi_turn) | `src/ai_multi_turn.py` | Dedup logic (líneas 90-100) se vuelve no-op en caso normal | Conservado como defensa en profundidad |
| F8 (ai_agent) | `src/agent_orchestrator.py` | Sin cambios | Sin impacto |
| F9 (emergency_mode) | `src/emergency_mode.py` | Null-check en `process_incoming_sms` | Defense-in-depth; sin cambio de comportamiento en producción (el dispatcher ya filtra) |
| F12 (password_reset) | `src/password_reset.py` | Null-check + role-check en `handle_incoming_sms` | Defense-in-depth; sin cambio de comportamiento en producción (el dispatcher ya filtra) |
