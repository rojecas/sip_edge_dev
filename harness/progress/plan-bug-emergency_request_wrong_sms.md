# Plan de Bug Fix — Bug #26 (emergency_request_wrong_sms)

## Síntoma

Cuando un operador solicita modo manual desde la vista Kiosko (POST /api/emergency/request), el administrador recibe un SMS con el texto "Lo siento, el sistema de análisis no está disponible en este momento." en lugar del mensaje esperado de solicitud de emergencia.

## Causa raíz (confirmada)

**Línea 152 de `src/sms_incoming.py`:**
```python
status = _extract_sms_field(read.stdout, "status")
```

El comando `mmcli -s <ID>` expone el estado del SMS en un campo llamado **`state`**, no `status`. La salida de mmcli tiene este formato:

```
  -------------------------------
  SMS (org.freedesktop.ModemManager1.SMS)
  -------------------------------
  Properties |       state: received
             |     number: +573001234567
             |       text: Hello world
```

Como `_extract_sms_field(read.stdout, "status")` busca `"status"` pero el campo real es `"state"`, la función retorna `None`. El filtro:

```python
if status and status.lower() != "received":
```

se evalúa como `if None ...` → `False`, por lo que **nunca se activa**. Los SMS salientes (estado "sent" o "stored") no son filtrados y se procesan como si fueran SMS entrantes.

### Flujo completo del bug

1. Operador solicita modo manual → `create_request()` → `send_sms()` al admin
2. El SMS saliente queda en el módem GSM con estado "sent"
3. ~15s después, `_fetch_mmcli_sms()` hace polling y encuentra ese SMS
4. El filtro en línea 152-156 no funciona porque busca "status" en vez de "state"
5. El SMS saliente se procesa como entrante y se envía a los handlers
6. `emergency_mode.process_incoming_sms()` devuelve False (el texto no coincide con patrones de emergencia)
7. `password_reset.handle_incoming_sms()` devuelve False
8. El fallback AI handler `handle_sms_query()` intenta conectar con llama-server
9. Si llama-server no está disponible, lanza `LlamaConnectionError` y envía "Lo siento..." al admin

## Archivos implicados

| Archivo | Cambio |
|---------|--------|
| `src/sms_incoming.py:152` | Cambiar `"status"` → `"state"` en la llamada a `_extract_sms_field` |
| `tests/test_sms_incoming.py` | **Crear**: tests para `_extract_sms_field` y filtro de SMS salientes |

## Fix propuesto

Cambiar línea 152 de `sms_incoming.py`:

```python
# ANTES (BUG):
status = _extract_sms_field(read.stdout, "status")

# DESPUÉS (FIX):
status = _extract_sms_field(read.stdout, "state")
```

## Plan de verificación

1. Crear `tests/test_sms_incoming.py` con:
   - Tests unitarios para `_extract_sms_field`: verificar que extrae "state", "number", "text" correctamente de output mmcli realista; verificar que "status" retorna None
   - Test de integración mockeando `subprocess.run` para simular mmcli y verificar que SMS con state="sent" son filtrados y no llegan a handlers
   - Test de integración mockeando `subprocess.run` para verificar que SMS con state="received" pasan el filtro
2. Ejecutar los tests → deben fallar (porque el código actual usa "status")
3. Aplicar el fix en `src/sms_incoming.py`
4. Ejecutar los tests → deben pasar
5. Ejecutar `./init.ps1` → todos los bloques OK

## Notas adicionales

- El commit a06c1b9 intentó arreglar esto añadiendo el filtro en línea 152, pero usó el nombre de campo incorrecto "status" en vez de "state"
- `_extract_sms_field` está implementada correctamente; el bug está únicamente en cómo se llama
- No hay otros lugares en el código que usen `_extract_sms_field` con "status"
