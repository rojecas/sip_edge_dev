# Design — Reset Individual de Pesos en Kiosko de Pesaje

> Feature 24 — reset_individual_pesos
> Dependencias: feature 6 (weighing_capture), feature 13 (frontend_login_kiosk)

---

## Resumen del cambio

Reemplazar el botón único de Reset general del formulario por tres botones
de reset individual, uno por cada campo de peso. Cada botón limpia solo su
campo correspondiente, permitiendo al operador corregir una lectura sin perder
las otras dos. El reset general se mantiene como acción secundaria.

---

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `src/weighings.py` | Añadir schema `ResetFieldRequest`; modificar endpoint `POST /api/weighings/reset` para aceptar `step` opcional |
| `frontend/src/components/WeightField.svelte` | Añadir prop `onReset` y botón "Reset" junto a Tara/Leer |
| `frontend/src/components/KioskForm.svelte` | Añadir 3 manejadores de reset individual; relegar reset general a acción secundaria; eliminar modal de confirmación para resets individuales |
| `tests/test_weighings.py` | Añadir tests para step válido, step inválido, step ausente, y autenticación |
| `frontend/src/components/__tests__/WeightField.test.js` o nuevo | Añadir test para botón Reset en WeightField |

---

## API: POST /api/weighings/reset (modificado)

### Request (nuevo cuerpo opcional)

```json
{
  "step": "peso_muestra"
}
```

Campos:
- `step` (string, opcional): Nombre del campo de peso a reiniciar.
  Valores válidos: `"peso_muestra"`, `"peso_mineral"`, `"peso_vegetal_extrano"`.
  Si se omite, se comporta como reset completo (compatibilidad hacia atrás).

### Response (sin cambios en el esquema)

```json
{
  "mensaje": "Campo peso_muestra reiniciado"
}
```

Códigos HTTP:
- `200` — Reset exitoso (individual o completo)
- `400` — `step` inválido (`{"detail": "step inválido. Valores aceptados: peso_muestra, peso_mineral, peso_vegetal_extrano"}`)
- `401` — No autenticado

### Dependencias de seguridad (sin cambios)

- `check_inactivity` — verifica sesión activa
- `require_any_role("admin", "operator")` — solo admin y operador

---

## Firmas nuevas / modificadas

### Backend: `src/weighings.py`

```python
class ResetFieldRequest(BaseModel):
    step: Optional[str] = None
```

Modificar función existente:

```python
@router.post("/reset", response_model=ResetResponse)
def reset_weighing_form(
    body: Optional[ResetFieldRequest] = None,
    current_user: dict = Depends(check_inactivity),
    _: dict = Depends(require_any_role("admin", "operator")),
):
    if body and body.step:
        # Validar step
        valid_steps = ["peso_muestra", "peso_mineral", "peso_vegetal_extrano"]
        if body.step not in valid_steps:
            raise HTTPException(
                status_code=400,
                detail=f"step inválido. Valores aceptados: {', '.join(valid_steps)}"
            )
        return ResetResponse(mensaje=f"Campo {body.step} reiniciado")
    # Sin step: reset completo (comportamiento actual)
    return ResetResponse()
```

### Frontend: `frontend/src/components/WeightField.svelte`

Nueva prop:

```javascript
let {
    fieldName = "",
    value = 0,
    disabled = true,
    onTara = () => {},
    onLeer = () => {},
    onReset = null,  // NUEVA: callback individual para reset
} = $props();
```

Nuevo botón en el template (dentro de `.field-row`):

```html
<button
    type="button"
    class="btn-reset-peso"
    onclick={onReset}
    title="Resetear este peso"
>Reset</button>
```

### Frontend: `frontend/src/components/KioskForm.svelte`

Nuevas funciones:

```javascript
async function handleResetPesoMuestra() {
    await api.post(ENDPOINTS.WEIGHINGS_RESET, { step: "peso_muestra" });
    pesoMuestra = 0;
}
async function handleResetPesoMineral() {
    await api.post(ENDPOINTS.WEIGHINGS_RESET, { step: "peso_mineral" });
    pesoMineral = 0;
}
async function handleResetPesoVegetal() {
    await api.post(ENDPOINTS.WEIGHINGS_RESET, { step: "peso_vegetal_extrano" });
    pesoVegetal = 0;
}
```

Modificar slots de `WeightField` para pasar `onReset`:

```svelte
<WeightField fieldName="Peso Muestra" bind:value={pesoMuestra}
    disabled={!isEmergencyMode} onReset={handleResetPesoMuestra} />
```

---

## Excepciones

No se añaden nuevas excepciones. El endpoint existente usa `HTTPException` de
FastAPI para errores, y se reutiliza para el caso de `step` inválido.

---

## Persistencia

No hay cambios en la base de datos. La feature no modifica ni crea tablas.
El endpoint `/api/weighings/reset` no persiste ningún estado (el formulario
es solo frontend state). No se requieren migraciones.

---

## Impacto en APIs existentes

No hay impacto. El endpoint `POST /api/weighings/reset` mantiene compatibilidad
hacia atrás: cuando se llama sin `step`, se comporta exactamente como antes.
Ningún otro endpoint ni schema se modifica.

---

## Alternativa descartada

**Endpoint independiente por campo** (`POST /api/weighings/reset/peso_muestra`,
`POST /api/weighings/reset/peso_mineral`, `POST /api/weighings/reset/peso_vegetal_extrano`):
Se descartó porque multiplica los endpoints sin beneficio real. Modificar el
endpoint existente con un campo `step` opcional mantiene la superficie de API
mínima y preserva compatibilidad hacia atrás.

**Reset individual sin llamada al backend**: Se descartó porque el endpoint
actual sirve como verificación de autenticación y registro de auditoría.
Eliminarlo para resets individuales rompería la consistencia y podría permitir
resets no autorizados si el frontend se manipula.
