# Implementación: rejected workflow_type para SMS de operadores

## Contexto

Feature 28 (ai_multi_turn) en fase testing. El dispatcher de SMS ignora silenciosamente los mensajes de operadores (role=operator) completando la conversación sin cambiar el workflow_type. Para trazabilidad y seguridad, se marca explícitamente con `workflow_type='rejected'` en `sms_conversations`.

## Cambios realizados

### 1. `src/models.py` (línea 276)
Agregado `'rejected'` al ENUM `workflow_type` en `SmsConversation`:
```python
Enum("emergency", "password_reset", "ai_query", "unknown", "rejected")
```

### 2. `src/sms_persistence.py` (línea 45)
Agregado `'rejected'` a la validación de `workflow_type` en `create_conversation`:
```python
if workflow_type not in ("emergency", "password_reset", "ai_query", "unknown", "rejected"):
```

### 3. `src/sms_persistence.py` — Nuevo método `update_conversation_workflow_type`
Agregado después de `update_conversation_status`. Sigue el mismo patrón: valida el valor, busca la conversación por ID, actualiza el campo y el timestamp `last_activity`.

### 4. `src/sms_dispatcher_v2.py` (línea ~292)
En el bloque de whitelist que rechaza SMS de roles no autorizados, se agregó:
```python
self._persistence.update_conversation_workflow_type(conv.id, "rejected")
```
antes del `update_conversation_status(conv.id, "completed")` existente.

### 5. Migración de BD
`database/migrations/2026_07_16_000001_add_rejected_to_sms_conversations_workflow_type.sql`:
```sql
ALTER TABLE sms_conversations 
MODIFY COLUMN workflow_type ENUM('emergency','password_reset','ai_query','unknown','rejected') NOT NULL;
```

### 6. Tests
Dos tests agregados en `tests/test_sms_dispatcher_v2.py` (clase `TestSmsDispatcherV2`):

- `test_operator_sms_marked_as_rejected`: SMS de número sin usuario registrado → `workflow_type='rejected'`, `status='completed'`
- `test_operator_user_sms_marked_as_rejected`: SMS de usuario con `role='operator'` → `workflow_type='rejected'`, `status='completed'`

## Trazabilidad

| Criterio | Test |
|----------|------|
| SMS de operador → workflow_type='rejected' | `test_operator_sms_marked_as_rejected` |
| SMS de usuario operator → workflow_type='rejected' | `test_operator_user_sms_marked_as_rejected` |

## Impacto en features existentes

- **Ninguno.** El cambio es backward-compatible:
  - Conversaciones existentes con `workflow_type='unknown'` no se modifican.
  - El nuevo valor `'rejected'` solo se asigna en nuevas conversaciones de operadores.
  - La whitelist y el flujo de rechazo ya existían; solo se agregó la asignación explícita del tipo.

## Tests preexistentes que fallan (NO relacionados con este cambio)

7 tests en `test_sms_dispatcher_v2.py` fallan debido a la whitelist (`role is None or role not in ("admin", "corresponsal")`) que bloquea SMS de números sin usuario admin/corresponsal registrado. Estos tests usan números sin usuarios en la BD de test. **Estas fallas son preexistentes y no fueron causadas por este cambio** — la whitelist ya existía antes.

Tests afectados (todos en `TestSmsDispatcherV2`):
- `test_conversation_created_on_first_message`
- `test_handler_order_matters`
- `test_no_catchall_ai_handler`
- `test_no_catchall_handler_bug26_regression`
- `test_persist_before_dispatch`
- `test_unknown_sms_help_response`
- `test_sms_with_existing_modem_id_is_skipped` (en `TestSmsDispatcherV2Fix3`)

## Verificación

1. `docker compose exec backend python -m unittest tests.test_sms_dispatcher_v2.TestSmsDispatcherV2.test_operator_sms_marked_as_rejected tests.test_sms_dispatcher_v2.TestSmsDispatcherV2.test_operator_user_sms_marked_as_rejected -v` → **OK** (2 tests)
2. `docker compose exec backend python -m unittest tests.test_sms_dispatcher_v2 -v` → 11/18 OK (7 fallas preexistentes)
3. `.\harness\init.ps1` → Pasos 1-5 OK, timeout en paso 6 (test suite completo muy grande)
