# Design — rs232_resend

> Decisiones técnicas para el reenvío de datos RS232 desde el kiosko.
>
> **Nota spec-validator (2026-07-23):** Archivo original renombrado a design.old.md (ya eliminado).
> Correcciones: (1) handleConfirm ahora verifica `result.enviado_pc` antes de entrar
> en resendMode (R5 corregido), (2) documentada la carga de Hacienda/Suerte necesaria
> para `_build_frame_data()`, (3) eliminada la justificación que contradecía R5.
>
> **Nota líder (2026-07-23):** R5 original eliminado. Verificado en `src/rs232.py:68`:
> `ser.write()` sin handshaking — `enviado_pc=true` solo significa escritura UART sin
> error de SO. Por tanto, `handleConfirm()` SIEMPRE activa `resendMode = true` tras
> POST exitoso, sin evaluar `enviado_pc`. El botón siempre cambia a "Reenviar Datos".

## Archivos modificados

| Archivo | Acción | Propósito |
|---------|--------|-----------|
| `src/weighings.py` | MODIFICAR | Agregar endpoint `POST /api/weighings/{id}/resend` |
| `src/models.py` | MODIFICAR | Agregar columna `resend_count` al modelo `Weighing` |
| `frontend/src/components/KioskForm.svelte` | MODIFICAR | Lógica de botón Confirmar ↔ Reenviar Datos |
| `frontend/src/components/HistoryTable.svelte` | MODIFICAR | Agregar columna de acciones con botón 🔄 (admin-only) |
| `frontend/src/lib/constants.js` | MODIFICAR | Agregar `ENDPOINTS.WEIGHINGS_RESEND` |
| `tests/test_weighings.py` | MODIFICAR | Tests del nuevo endpoint `POST /api/weighings/{id}/resend` |

### Archivos NO modificados

- `src/rs232.py` — No se toca. `send_frame()` ya funciona correctamente.
- `src/main.py` — No se toca. El router de weighings ya está registrado.
- `frontend/src/components/WeightField.svelte` — Ya expone `onTara`/`onLeer` callbacks, no requiere cambios.
- `src/anomaly_detector.py` — No se toca. `resend` no ejecuta detección de anomalías.

## Nuevo endpoint: `POST /api/weighings/{id}/resend`

### Firma

```python
@router.post("/{weighing_id}/resend", response_model=WeighingResponse, status_code=200)
def resend_weighing(
    weighing_id: int,
    current_user: dict = Depends(check_inactivity),
    _: dict = Depends(require_any_role("admin", "operator")),
    db: Session = Depends(get_db),
) -> WeighingResponse:
```

### Comportamiento

1. Busca el registro `Weighing` por `weighing_id`. Si no existe, HTTP 404.
2. Si el usuario es `operator` y el registro no le pertenece, HTTP 404 (misma política que `get_weighing`).
3. Carga los objetos `Hacienda` y `Suerte` desde la BD usando `hacienda_id` y `suerte_id` del registro (idéntico a como lo hace `create_weighing`).
4. Construye el `frame_data` con `_build_frame_data(record, hacienda, suerte)`.
5. Llama a `_send_rs232_frame(frame_data, record)` para transmitir la trama RS232 y actualizar `enviado_pc = True`.
6. Incrementa `record.resend_count += 1`.
7. Hace `db.commit()` y `db.refresh(record)`.
8. Devuelve el registro actualizado como `WeighingResponse`.

### Diferencias con `POST /api/weighings`

| Aspecto | create_weighing | resend_weighing |
|---------|----------------|-----------------|
| Valida Hacienda/Suerte | Sí | No (ya existe) |
| Escribe todos los campos | Sí | No |
| Ejecuta detección de anomalías | Sí | **NO** |
| Actualiza `enviado_pc` | Sí (si send_frame ok) | Sí |
| Incrementa `resend_count` | No | **Sí** |
| HTTP status | 201 | 200 |

### Contrato API

**Request:**
```
POST /api/weighings/{id}/resend
Authorization: Bearer <token>
Content-Type: application/json
(sin body)
```

**Response (200):**
```json
{
  "id": 42,
  "fecha": "2026-07-23",
  "hora": "10:30:00",
  "tractomula": "ABC-123",
  "vagon": "V5",
  "numero_guia": "G-789",
  "hacienda_id": 1,
  "suerte_id": 1,
  "peso_muestra": 1.500,
  "peso_mineral": 0.800,
  "peso_vegetal_extrano": 0.200,
  "usuario_id": 2,
  "created_at": "2026-07-23T10:30:00",
  "enviado_pc": true,
  "manual_entry": false,
  "tipo_cosecha": "Mecanico - Verde",
  "notas": null,
  "resend_count": 1
}
```

**Errors:**
| Status | Detail | Condición |
|--------|--------|-----------|
| 404 | "Weighing not found" | ID inexistente o pertenece a otro operator |
| 401 | — | Token inválido o expirado |
| 422 | — | `weighing_id` no es entero válido |

### Excepciones reutilizadas

- `Rs232Error` (de `src/rs232.py`) — capturada por `_send_rs232_frame()` y logueada. El endpoint retorna 200 aunque el envío RS232 falle, porque el registro ya existe (solo falló la transmisión). El campo `enviado_pc` queda `False` si falla.

## Persistencia

### Tabla modificada: `weighings`

Nueva columna:

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `resend_count` | `INTEGER` | NO | `0` | Contador de reintentos de envío RS232 |

### Migración

Archivo nuevo: `database/migrations/2026_07_23_000001_add_resend_count_to_weighings.py`
(formato `.py` con `upgrade()`/`downgrade()`, mismo patrón que F37 y F39)

```python
from sqlalchemy.engine import Connection
from sqlalchemy.sql import text

def upgrade(connection: Connection) -> None:
    connection.execute(text("""
        ALTER TABLE weighings
        ADD COLUMN resend_count INTEGER NOT NULL DEFAULT 0
        AFTER enviado_pc
    """))

def downgrade(connection: Connection) -> None:
    connection.execute(text("""
        ALTER TABLE weighings
        DROP COLUMN resend_count
    """))
```

Ejecución: el implementer corre `upgrade()` en su entorno de desarrollo (Docker).
La automatización de migraciones será feature F45 (`migration_tracker`).

### Modelo (`src/models.py`)

Agregar en la clase `Weighing`:

```python
resend_count = Column(Integer, nullable=False, default=0, server_default="0")
```

### Schema (`src/weighings.py`)

Agregar en `WeighingResponse`:

```python
resend_count: int = Field(default=0)
```

## Frontend — KioskForm.svelte

### Nuevo estado reactivo

```javascript
let lastWeighingId = $state(null);
let resendMode = $state(false);
```

### Flujo handleConfirm() modificado

```javascript
async function handleConfirm() {
  // ... validación y POST existente ...
  const result = await api.post(ENDPOINTS.WEIGHINGS, body);
  lastWeighingId = result.id;
  // R1: Siempre activar modo reenvío — enviado_pc no es confiable
  // (el write al UART puede tener éxito aunque el PC no reciba).
  resendMode = true;
  successMessage = "Pesaje registrado exitosamente";
  // NO hacer resetForm() ni setTimeout — si resendMode=true, el botón cambia a Reenviar Datos
}
```

### Nueva función handleResend()

```javascript
async function handleResend() {
  if (!lastWeighingId || isSubmitting) return;
  isSubmitting = true;
  errorMessage = "";
  try {
    const result = await api.post(
      `${ENDPOINTS.WEIGHINGS_RESEND}/${lastWeighingId}`
    );
    if (result.enviado_pc) {
      successMessage = "Datos reenviados exitosamente al PC";
    }
  } catch (err) {
    errorMessage = err instanceof ApiError
      ? err.message
      : "Error al reenviar datos";
  } finally {
    isSubmitting = false;
  }
}
```

### Botón condicional

```svelte
<button
  type="button"
  class="btn-confirm"
  onclick={resendMode ? handleResend : handleConfirm}
  disabled={resendMode ? false : (!isFormValid() || isSubmitting)}
>
  {#if resendMode}
    Reenviar Datos
  {:else if isSubmitting}
    Registrando...
  {:else}
    Confirmar Medidas
  {/if}
</button>
```

### Detección de Tara/Leer para salir de resendMode

Se bindean los callbacks `onTara` y `onLeer` de los 3 `WeightField`:

```svelte
<WeightField fieldName="Peso Muestra" bind:value={pesoMuestra}
  onTara={exitResendMode} onLeer={exitResendMode} ... />
<WeightField fieldName="Peso Vegetal" bind:value={pesoVegetal}
  onTara={exitResendMode} onLeer={exitResendMode} ... />
<WeightField fieldName="Peso Mineral" bind:value={pesoMineral}
  onTara={exitResendMode} onLeer={exitResendMode} ... />
```

```javascript
function exitResendMode() {
  resendMode = false;
  lastWeighingId = null;
}
```

También se resetea `resendMode` en `resetForm()` y `confirmReset()`.

### Persistencia del estado de reenvío

El estado `resendMode` es volátil del frontend. Si el operador cierra sesión y vuelve,
`resendMode` se pierde (decisión de diseño: intencional, el pendiente de envío se cierra
al terminar la sesión). No se requiere consultar `GET /api/weighings/{id}` al cargar
porque el estado no persiste.

## Frontend — HistoryTable.svelte

### Nueva columna de acciones

Agregar columna `<th>Acción</th>` en el `<thead>`.

En el `<tbody>`, antes del cierre de `</tr>`, agregar:

```svelte
<td>
  {#if $authStore.isAdmin && !w.enviado_pc}
    <button class="btn-action" onclick={(e) => { e.stopPropagation(); handleResend(w.id); }}
      title="Reenviar datos al PC">&#x1F504;</button>
  {/if}
</td>
```

### Nueva función handleResend

```javascript
async function handleResend(weighingId) {
  try {
    await api.post(`${ENDPOINTS.WEIGHINGS_RESEND}/${weighingId}`);
    // Recargar la tabla para reflejar el cambio en enviado_pc
    await loadData();
  } catch (err) {
    // Manejar error (toast o mensaje)
  }
}
```

## CONSTANTES

Agregar en `frontend/src/lib/constants.js`:

```javascript
WEIGHINGS_RESEND: "/api/weighings",
```

Nota: se reutiliza `/api/weighings` como base y se añade `/${id}/resend` en el
código del componente, porque la constante almacena la ruta base.

## Alternativa descartada

### Reutilizar `POST /api/weighings` para reenvío

Se consideró agregar un flag `?resend=true` o un campo `resend_of_id` en el body
del endpoint `POST /api/weighings` para indicar que es un reenvío.

**Justificación del descarte:** (coincide con `design_decision` en feature_list.json)

1. **Responsabilidad única:** `POST /api/weighings` crea pesajes. El reenvío es
   una operación distinta (no crea, solo retransmite).
2. **Semántica clara:** `POST /api/weighings/{id}/resend` expresa exactamente
   qué hace: reenviar el registro `{id}`.
3. **No acoplamiento:** Si en el futuro se modifica `POST /api/weighings` (ej.
   nueva validación, nuevo campo obligatorio), el reenvío no se vería afectado.
4. **No re-ejecución de anomalías:** El endpoint de creación ejecuta detección
   de anomalías post-pesaje (F8). El reenvío no debe re-ejecutarla. Separar los
   endpoints evita tener que agregar condiciones para saltar lógica.

### Persistir estado `resendMode` en backend

Se consideró guardar una bandera `pendiente_reenvio` en la tabla `weighings`
o en una tabla separada.

**Justificación del descarte:** El humano decidió que el pendiente de envío
es estado volátil del frontend. Si el operador cierra sesión, el pendiente
se pierde intencionalmente (no hay garantía de que el PC esté disponible
cuando el operador retome el turno). Esto simplifica la implementación y
evita tener que limpiar estados huérfanos.

## Impacto en APIs existentes

### Feature 6 — weighing_capture

| Ítem | Archivo | Cambio requerido |
|------|---------|-----------------|
| Schema WeighingResponse | src/weighings.py | Agregar campo `resend_count: int = 0` |
| GET /api/weighings/{id} | src/weighings.py | Incluir `resend_count` en la respuesta (automático por `from_attributes = True`) |

Justificación: la columna `resend_count` se agrega al modelo y al schema de
respuesta para que el frontend (o cualquier cliente) pueda conocer cuántos
reintentos se han hecho. No se requiere modificar el endpoint de creación.

NO hay impacto en:
- `POST /api/weighings` (no toca `resend_count`)
- `GET /api/weighings` (la lista incluye automáticamente el nuevo campo vía ORM)
- `POST /api/weighings/reset` (solo resetea estado temporal del formulario)

### Feature 11 — rs232_transmission

No hay impacto. `send_frame()` y `_send_rs232_frame()` se reutilizan tal cual,
sin modificaciones. El flujo de reenvío llama al mismo `_send_rs232_frame()`
que usa `create_weighing()`.

### Feature 13 — frontend_login_kiosk

No hay impacto directo. El componente `KioskForm.svelte` se modifica, pero
ninguna dependencia externa cambia su comportamiento.

## Análisis de impacto en features existentes

### Método `_send_rs232_frame()` en `src/weighings.py`

**Consumidores actuales:**
1. `create_weighing()` en `src/weighings.py` — se llama tras crear un pesaje.

**Consumidor nuevo:**
1. `resend_weighing()` (nuevo endpoint) — llamará al mismo `_send_rs232_frame()`.

**Compatibilidad hacia atrás:** Total. No se modifica la firma ni el
comportamiento de `_send_rs232_frame()`.

### Columna `enviado_pc` en modelo `Weighing`

**Consumidores actuales:**
1. `_send_rs232_frame()` en `src/weighings.py` — escribe `True` tras éxito.
2. `GET /api/weighings/{id}` — retorna el campo.
3. `GET /api/weighings` — retorna el campo en la lista.
4. `HistoryTable.svelte` — no muestra el campo actualmente, pero el nuevo botón 🔄 lo usará (nuevo consumo).
5. `WeighingDetailModal.svelte` — no muestra el campo actualmente.

**Compatibilidad hacia atrás:** Total. `enviado_pc` ya existe. El nuevo endpoint
lo escribe igual que `_send_rs232_frame()`.

### Dependencias transitivas

No hay dependencias transitivas más allá de F6 y F11 declaradas en
`depends_on`. Los únicos módulos que tocan `Weighing` son `weighings.py` y
`models.py` en el backend, y `KioskForm.svelte` / `HistoryTable.svelte` en
el frontend.

## Tests

### Archivo: `tests/test_weighings.py`

Nuevos tests a agregar:

| Test | Cubre R |
|------|---------|
| `test_resend_endpoint_returns_200` | R2, R5 |
| `test_resend_endpoint_increments_resend_count` | R7 |
| `test_resend_endpoint_404_if_not_found` | R5 |
| `test_resend_endpoint_404_if_operator_other_user` | R5 |
| `test_resend_endpoint_does_not_run_anomaly_detection` | R2 |
| `test_resend_endpoint_updates_enviado_pc` | R2, R5 |
| `test_resend_multiple_times_allowed` | R3 |
| `test_resend_count_defaults_to_zero_on_create` | R6 |

### Tests de frontend

| Test | Cubre R |
|------|---------|
| `test_confirm_button_changes_to_resend_after_post` | R1 |
| `test_resend_button_triggers_api_call` | R2 |
| `test_resend_mode_exits_on_tara_or_leer` | R4 |
| `test_admin_history_resend_button_visible` | R8 |
| `test_operator_history_resend_button_not_visible` | R9, R8 |

## github_labels

No se requieren etiquetas adicionales.

