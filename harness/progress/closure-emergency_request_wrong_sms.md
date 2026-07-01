# Closure — Bug #26 (emergency_request_wrong_sms)

## Síntoma

Cuando un operador solicita modo manual desde la vista Kiosko (POST /api/emergency/request), el administrador recibe en su teléfono el mensaje "Lo siento, el sistema de análisis no está disponible en este momento." en lugar del mensaje esperado de solicitud de emergencia.

## Causa raíz

En `src/sms_incoming.py:152`, el filtro de SMS salientes usaba `_extract_sms_field(read.stdout, "status")` para determinar si un SMS debía ser procesado como entrante. Sin embargo, el comando `mmcli -s <ID>` expone el estado del SMS en un campo llamado **`state`**, no `status`. Por lo tanto:

1. `_extract_sms_field(read.stdout, "status")` siempre retornaba `None`
2. El filtro `if status and status.lower() != "received"` nunca se activaba
3. Todos los SMS (incluyendo salientes con `state=sent` o `state=stored`) se procesaban como entrantes
4. Un SMS de solicitud de emergencia saliente era re-procesado como entrante ~15s después
5. Como su texto no coincidía con patrones de emergencia, caía al handler AI fallback
6. Si llama-server no estaba disponible, se enviaba "Lo siento..." al admin

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/sms_incoming.py:152` | Cambiar `"status"` → `"state"` en la llamada a `_extract_sms_field` |
| `tests/test_sms_incoming.py` | **Creado**: 14 tests (9 unitarios + 5 de integración mockeada) |

## Fix aplicado

**Línea 152 de `src/sms_incoming.py`:**

```python
# ANTES (BUG):
status = _extract_sms_field(read.stdout, "status")

# DESPUÉS (FIX):
status = _extract_sms_field(read.stdout, "state")
```

## Regression test

**Archivo nuevo:** `tests/test_sms_incoming.py` (14 tests)

### Tests unitarios para `_extract_sms_field` (9 tests):
- `test_extract_state_received` — Extraer "state: received" del mmcli output
- `test_extract_state_sent` — Extraer "state: sent"
- `test_extract_state_stored` — Extraer "state: stored"
- `test_extract_number` — Extraer "number"
- `test_extract_text` — Extraer "text"
- `test_extract_status_returns_none` — **Documenta el bug**: "status" retorna None
- `test_extract_nonexistent_field_returns_none` — Campo inexistente retorna None
- `test_extract_field_empty_output` — Output vacío retorna None
- `test_extract_field_no_match` — Output sin formato mmcli retorna None

### Tests de filtro `_fetch_mmcli_sms` con mock (5 tests):
- `test_sent_sms_is_filtered` — **BUG #26**: SMS "sent" no debe estar en mensajes retornados
- `test_stored_sms_is_filtered` — SMS "stored" no debe estar en mensajes retornados
- `test_received_sms_passes_filter` — SMS "received" debe estar en mensajes retornados
- `test_received_sms_with_special_chars` — SMS received con texto pasa el filtro
- `test_mixed_sms_only_received_processed` — Múltiples SMS: solo los "received" se retornan

## Resultado de `./init.ps1`

Los tests de `test_sms_incoming.py` pasan al 100% en Docker.
Los 5 errores de `test_password_reset.TestIncomingSmsDispatcher` son pre-existentes
(error de event loop al correr toda la suite) y no están relacionados con este fix.

## Notas técnicas

- El commit a06c1b9 intentó arreglar este bug añadiendo el filtro en línea 152, pero usó el nombre de campo incorrecto "status" en vez de "state"
- `_extract_sms_field` está implementada correctamente; el bug estaba únicamente en cómo se llamaba
- No hay otros lugares en el código que usen `_extract_sms_field` con "status"
