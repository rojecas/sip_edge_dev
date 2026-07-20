# Design — Feature 37: notas_muestras

> Versión aprobada por humano (2026-07-20).
> Cambio vs versión spec-validator: HistoryTable — columna "Notas" reemplazada por modal de detalle al hacer click en fila.

## Resumen

Agregar un campo de texto colapsable para notas en el formulario de pesaje
(KioskForm), persistir en la BD (columna `notas` en `weighings`), mostrar en
el historial vía modal de detalle al hacer click en una fila de la tabla
(HistoryTable → WeighingDetailModal), y exponer al agente AI para consultas SMS.

---

## Archivos a crear

| Archivo | Propósito |
|---------|-----------|
| `frontend/src/components/NotesField.svelte` | Componente colapsable de notas (reutilizable) |
| `frontend/src/components/WeighingDetailModal.svelte` | Modal de detalle de pesaje — abre al hacer click en fila del historial |
| `database/migrations/2026_07_20_000001_add_notas_to_weighings.py` | Migración: columna `notas` TEXT NULL en `weighings` |

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `src/models.py` | Agregar `notas = Column(Text, nullable=True, default=None)` en clase `Weighing` |
| `src/weighings.py` | Agregar `notas: str \| None = None` en `WeighingCreate` y `WeighingResponse`; pasar `notas` en `create_weighing`; incluir en `_build_frame_data`; **IMPORTANTE: agregar `notas=w.notas` en construcción manual de `WeighingResponse` dentro de `list_weighings`** (líneas 263-280) |
| `src/rs232.py` | **Condicional — requiere coordinación F11.** Agregar `notas` al final de la línea CSV en `send_frame()` si se decide expandir de 15 a 16 campos. Ver sección "Impacto en APIs existentes" para detalles. |
| `src/sql_tools.py` | Agregar tool `get_weighing_notes` + entrada en `TOOL_DEFINITIONS`; registrar en `execute_tool` |
| `frontend/src/components/KioskForm.svelte` | Importar `NotesField`, agregar estado `notas`, incluir en formulario, enviar en POST body, limpiar en `resetForm` |
| `frontend/src/components/HistoryTable.svelte` | Importar `WeighingDetailModal`; agregar estado `selectedWeighing` + `showDetail`; hacer filas clickeables con `onclick`; renderizar `<WeighingDetailModal>` condicionalmente |
| `frontend/src/lib/constants.js` | Sin cambios — el body se envía dinámicamente desde KioskForm |
| `tests/test_weighings.py` | Tests para R1, R5, R11, R12, R13 |
| `tests/test_sql_tools.py` | Tests para R9 (get_weighing_notes) |
| `frontend/src/components/__tests__/KioskForm.test.js` | Test para R2, R3, R4, R6 |
| `frontend/src/components/__tests__/HistoryTable.test.js` | Test para R7, R8 (modal abre con click, muestra notas/"Sin observaciones") |

---

## Firmas nuevas

### Backend — Models (`src/models.py`)

```python
# En clase Weighing (agregar después de tipo_cosecha):
notas = Column(Text, nullable=True, default=None)
```

### Backend — Schemas (`src/weighings.py`)

```python
# En WeighingCreate:
notas: Optional[str] = Field(default=None, max_length=65535)

# En WeighingResponse:
notas: Optional[str] = None
```

### Backend — Endpoint list_weighings (cambio manual obligatorio)

> **ATENCIÓN:** `list_weighings()` construye `WeighingResponse` manualmente
> (líneas 263-280), NO usa `from_attributes`. Es necesario agregar
> `notas=w.notas` en cada ítem construido. El endpoint `get_weighing`
> (single-item) y `create_weighing` (retorno directo de `record`) usan
> `from_attributes` automáticamente y no requieren cambios manuales adicionales.

```python
# En list_weighings(), dentro del bucle for w in records:
items.append(WeighingResponse(
    id=w.id,
    fecha=w.fecha,
    ...
    tipo_cosecha=w.tipo_cosecha,
    notas=w.notas,  # <-- AGREGAR ESTA LÍNEA
))
```

### Backend — SQL Tools (`src/sql_tools.py`)

```python
# Nueva entrada en TOOL_DEFINITIONS:
{
    "type": "function",
    "function": {
        "name": "get_weighing_notes",
        "description": "Obtiene las notas registradas en pesajes, filtrado opcionalmente por vagon y/o rango de fechas.",
        "parameters": {
            "type": "object",
            "properties": {
                "vagon": {"type": "string", "description": "Filtro opcional por identificador de vagon"},
                "fecha_inicio": {"type": "string", "description": "Fecha inicio formato YYYY-MM-DD"},
                "fecha_fin": {"type": "string", "description": "Fecha fin formato YYYY-MM-DD"},
                "limit": {"type": "integer", "description": "Maximo de registros a retornar (default 20)"},
            },
        },
    },
},

# Nuevo método en SqlTools:
def get_weighing_notes(
    self,
    vagon: str | None = None,
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Retorna notas de pesajes filtrados por vagon y/o rango de fechas."""
    ...
```

### Frontend — Componente `NotesField.svelte`

```svelte
<script>
  let { bind:notas, label = "Notas" } = $props();
  let expanded = $state(false);
</script>
```

Propiedades:
- `bind:notas` — texto de las notas (two-way binding)
- `label` — texto del label (default "Notas")

### Frontend — Componente `WeighingDetailModal.svelte`

```svelte
<script>
  let { weighing, onclose } = $props();
</script>
```

Props:
- `weighing` — objeto completo del pesaje (todos los campos de `WeighingResponse`)
- `onclose` — callback para cerrar el modal

Comportamiento:
- Overlay semitransparente que cubre toda la pantalla
- Panel centrado con layout de dos columnas (etiqueta: valor) + sección de notas al pie
- Cierre con botón X, tecla Escape (`onkeydown` en `svelte:window`), y click fuera del panel (click en overlay)
- Sección de notas muestra texto completo si existe, o "Sin observaciones" si es NULL/vacío
- Filas de la tabla en HistoryTable se vuelven clickeables (`cursor: pointer`, `onclick` que setea `selectedWeighing` y `showDetail = true`)

---

## Decisiones técnicas

1. **Columna TEXT nullable vs VARCHAR.** Se usa `TEXT` (no `VARCHAR`) porque las
   notas del operador pueden ser extensas (varias líneas) y no hay un límite
   superior estricto. `TEXT` soporta hasta 65.535 bytes en MySQL/MariaDB.

2. **Componente colapsable Svelte 5.** Se crea `NotesField.svelte` como
   componente independiente (no inline en KioskForm) para reutilización futura.
   Usa `$state()` para el toggle expandir/colapsar y transiciones CSS simples
   (sin animaciones complejas que dependan de librerías externas).

3. **Sin dependencias externas.** El componente colapsable usa CSS puro +
   Svelte 5 `$state`. No se agregan librerías de UI.

4. **Tool SQL separada, no modificación de tools existentes.** Se crea una
   herramienta específica `get_weighing_notes` en lugar de modificar
   `get_daily_summary` o `get_shift_summary`, porque la consulta de notas es
   un caso de uso distinto (texto, no métricas numéricas) y mezclarlo rompería
   el principio de responsabilidad única.

5. **Empty string → NULL en backend.** El frontend envía `notas: notas || null`
   (empty string se convierte en null antes de llegar al backend). Para robustez
   ante llamadas API directas, se recomienda agregar un `field_validator` en
   `WeighingCreate.notas` que normalice cadena vacía a `None`:
   ```python
   @field_validator("notas", mode="before")
   @classmethod
   def normalize_notas(cls, v):
       if v is not None and isinstance(v, str) and v.strip() == "":
           return None
       return v
   ```
   Esto cubre el caso de R11 para los tres escenarios (None, "", omitido).

6. **list_weighings construcción manual (crítico).** A diferencia de
   `create_weighing` y `get_weighing` que retornan el objeto ORM directamente
   (mapeo automático vía `from_attributes=True`), `list_weighings` construye
   instancias de `WeighingResponse` manualmente campo por campo. Si `notas`
   no se agrega explícitamente en esa construcción manual, la respuesta de
   `GET /api/weighings` no incluirá el campo `notas`, rompiendo R7 y R12.
   El implementer DEBE verificar que `notas=w.notas` está presente en la
   construcción de cada ítem (ver sección "Firmas nuevas" arriba).

7. **RS232 frame: cambio en dos pasos.** `_build_frame_data()` agrega `notas`
   al dict, pero `src/rs232.py:send_frame()` construye la línea CSV usando
   claves explícitas (`frame_data['id']`, `frame_data['vagon']`, etc.).
   Agregar `notas` solo a `_build_frame_data` NO incluye el campo en la trama
   RS232 enviada. Para que `notas` aparezca en el CSV se requiere modificar
   también `rs232.py`, agregando `frame_data.get('notas', '')` al final de la
   línea CSV. Esta modificación requiere coordinación con el equipo del PC
   externo (cambio de 15 a 16 campos). El diseño actual incluye `notas` en
   el dict (`_build_frame_data`) como paso preparatorio; la activación real
   en la trama RS232 queda pendiente de coordinación con F11.

8. **Modal de detalle vs columna en tabla.** Descartada la opción de agregar una
   columna "Notas" en HistoryTable por dos razones: (a) la tabla ya tiene 11
   columnas y es ilegible en pantalla de kiosko si se agrega una más, y (b) las
   notas son `TEXT` libre (párrafos enteros) que no caben en una celda. El modal
   resuelve ambos problemas y además muestra todos los campos con etiquetas
   legibles, no solo las notas.

---

## Alternativa descartada

**Almacenar notas en tabla separada `weighing_notes` con FK a `weighings`.**
Descartado porque:
- Es una relación 1:1 (un pesaje tiene exactamente cero o un conjunto de notas).
- Una tabla separada requeriría JOIN en cada consulta de historial,
  agregando complejidad innecesaria.
- El modelo actual ya tiene columnas opcionales directas en `weighings`
  (`manual_entry`, `enviado_pc`) que siguen el mismo patrón.
- La migración es más simple y el rendimiento de lectura mejora al evitar JOINs.

---

## Persistencia

### Tabla modificada: `weighings`

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| notas | TEXT | YES | NULL | Nueva columna |

No se modifican índices existentes ni se agregan nuevos (las consultas de notas
se filtran por `vagon` — ya indexado implícitamente por ser VARCHAR — y
`fecha` — columna existente sin índice explícito, aceptable para el volumen
esperado de datos).

### Migraciones

1. `database/migrations/2026_07_20_000001_add_notas_to_weighings.py`

```python
def upgrade(connection):
    connection.execute(text("""
        ALTER TABLE weighings
        ADD COLUMN notas TEXT NULL DEFAULT NULL
        AFTER tipo_cosecha
    """))

def downgrade(connection):
    connection.execute(text("""
        ALTER TABLE weighings
        DROP COLUMN notas
    """))
```

### Datos semilla
Sin cambios. No se requieren datos iniciales para esta columna.

---

## Contrato API

### POST /api/weighings

**Body** (WeighingCreate modificado):
```json
{
  "tractomula": "ABC123",
  "vagon": "VAG-001",
  "numero_guia": "G-001",
  "hacienda_id": 1,
  "suerte_id": 1,
  "peso_muestra": 1.250,
  "peso_mineral": 0.800,
  "peso_vegetal_extrano": 0.050,
  "manual_entry": false,
  "tipo_cosecha": "Mecanico - Verde",
  "notas": "Problemas con core sampler, muestra muy humeda"
}
```

**Response** (201, WeighingResponse modificado):
```json
{
  "id": 42,
  "fecha": "2026-07-20",
  "hora": "14:30:00",
  "tractomula": "ABC123",
  "vagon": "VAG-001",
  "numero_guia": "G-001",
  "hacienda_id": 1,
  "suerte_id": 1,
  "peso_muestra": 1.250,
  "peso_mineral": 0.800,
  "peso_vegetal_extrano": 0.050,
  "usuario_id": 2,
  "created_at": "2026-07-20T14:30:00",
  "enviado_pc": true,
  "manual_entry": false,
  "tipo_cosecha": "Mecanico - Verde",
  "notas": "Problemas con core sampler, muestra muy humeda"
}
```

### GET /api/weighings y GET /api/weighings/{id}

Mismos campos que el response de POST. El campo `notas` se incluye en cada
ítem del array `items`.

**Atención lista paginada:** `GET /api/weighings` construye `WeighingResponse`
manualmente; el implementer DEBE agregar `notas=w.notas` en esa construcción.

### Herramienta SQL: get_weighing_notes (para el agente AI)

Input: `{ vagon?: str, fecha_inicio?: str (YYYY-MM-DD), fecha_fin?: str (YYYY-MM-DD), limit?: int }`

Output:
```json
[
  {
    "id": 42,
    "fecha": "2026-07-20",
    "vagon": "VAG-001",
    "tractomula": "ABC123",
    "notas": "Problemas con core sampler, muestra muy humeda"
  },
  ...
]
```

Mínimo uno de `vagon` o `fecha_inicio` DEBE ser proporcionado (validación
en la tool).

---

## Impacto en APIs existentes

La columna `notas` se agrega a `weighings` y se expone en todos los endpoints
que retornan `WeighingResponse`. Esto afecta:

### POST /api/weighings (Feature 6, 18)
- Schema `WeighingCreate`: nuevo campo opcional `notas: str | None = None`.
- Schema `WeighingResponse`: nuevo campo `notas: str | None`.
- Constructor de `Weighing` en `create_weighing()`: pasar `notas=body.notas`.
- Recomendado: agregar `field_validator` en `WeighingCreate.notas` para
  normalizar cadena vacía a `None` (cubre R11 para llamadas API directas).

### GET /api/weighings (Feature 6)
- Schema `WeighingResponse` incluye `notas`.
- **CRÍTICO:** `list_weighings()` construye `WeighingResponse` manualmente.
  Se requiere agregar `notas=w.notas` explícitamente en cada ítem construido
  (líneas 263-280 de `src/weighings.py`). Sin este cambio, el modal de detalle
  no mostrará notas aunque existan en la BD.

### GET /api/weighings/{id} (Feature 6)
- Schema `WeighingResponse` incluye `notas`.
- Usa `from_attributes=True` — no requiere cambios manuales adicionales.

### POST /api/weighings/reset (Feature 24)
- Sin cambios. El reset es del lado del cliente (frontend). El endpoint
  backend no gestiona notas.

### RS232 frame (Feature 11 — rs232_transmission)
- `_build_frame_data()` en `weighings.py` debe incluir `"notas": record.notas`
  en el dict retornado (paso preparatorio).
- **Paso 2 (requiere coordinación F11):** `src/rs232.py:send_frame()` construye
  la línea CSV con claves explícitas. Para que `notas` aparezca en la trama
  RS232, se debe agregar `frame_data.get('notas', '')` al final de `csv_line`.
  Esto expande el CSV de 15 a 16 campos y requiere coordinación con el equipo
  del PC externo.
- **Decisión actual:** agregar `notas` al dict de `_build_frame_data` para
  que esté disponible cuando rs232.py se actualice. La activación real en la
  trama RS232 se difiere hasta que el equipo del PC externo confirme soporte
  para el campo 16.

### Frontend: HistoryTable (Feature 13)
- **Las filas de la tabla se vuelven clickeables** (cursor pointer, `onclick`).
- Al hacer click en una fila, se abre `WeighingDetailModal` con el detalle
  completo del pesaje, incluyendo notas.
- El modal se cierra con X, Escape, o click fuera.
- **No se agrega columna "Notas" a la tabla.** Se reutilizan las 11 columnas
  existentes sin cambios.

---

## Análisis de impacto en features existentes

### Feature 6 — weighing_capture
| Ítem | Archivo | Cambio requerido | Breaking? |
|------|---------|-----------------|-----------|
| Schema WeighingCreate | `src/weighings.py` | Agregar `notas: Optional[str] = None` + field_validator empty-string | No (campo opcional, default None) |
| Schema WeighingResponse | `src/weighings.py` | Agregar `notas: Optional[str] = None` | No (nuevo campo en response) |
| Constructor Weighing | `src/weighings.py` | Agregar `notas=body.notas` en create_weighing() | No |
| list_weighings manual build | `src/weighings.py` | Agregar `notas=w.notas` en WeighingResponse(...) dentro del bucle for | No (nuevo campo) |
| _build_frame_data | `src/weighings.py` | Agregar `"notas": record.notas` al dict | No (aditivo al dict) |
| Tests | `tests/test_weighings.py` | Agregar tests de persistencia, lectura, y texto largo | — |

### Feature 8 — ai_agent (via sql_tools)
| Ítem | Archivo | Cambio requerido | Breaking? |
|------|---------|-----------------|-----------|
| TOOL_DEFINITIONS | `src/sql_tools.py` | Agregar entrada `get_weighing_notes` | No (nueva herramienta) |
| SqlTools | `src/sql_tools.py` | Agregar método `get_weighing_notes()` + registro en `tool_map` de `execute_tool` | No |
| Tests | `tests/test_sql_tools.py` | Agregar tests de la nueva tool | — |

### Feature 11 — rs232_transmission
| Ítem | Archivo | Cambio requerido | Breaking? |
|------|---------|-----------------|-----------|
| Frame data dict | `src/weighings.py` | `_build_frame_data()` agrega `"notas"` al dict retornado | No (aditivo) |
| CSV output | `src/rs232.py` | `send_frame()` debe agregar `frame_data.get('notas', '')` al CSV (paso 2, requiere coordinación) | SI — requiere coordinación con equipo de PC externo |
| Formato CSV | `src/rs232.py` | De 15 a 16 campos si se activa paso 2 | SI — coordinación F11 |

### Feature 13 — frontend_login_kiosk
| Ítem | Archivo | Cambio requerido | Breaking? |
|------|---------|-----------------|-----------|
| Componente NotesField (nuevo) | `frontend/src/components/NotesField.svelte` | Crear componente colapsable | N/A |
| Componente WeighingDetailModal (nuevo) | `frontend/src/components/WeighingDetailModal.svelte` | Crear modal de detalle de pesaje | N/A |
| KioskForm | `frontend/src/components/KioskForm.svelte` | Importar NotesField, agregar estado notas, enviar en POST, limpiar en reset | No |
| HistoryTable | `frontend/src/components/HistoryTable.svelte` | Importar WeighingDetailModal; agregar estado `selectedWeighing` + `showDetail`; hacer filas clickeables (`onclick`); renderizar `<WeighingDetailModal>` condicional | No |
| Tests KioskForm | `frontend/src/components/__tests__/KioskForm.test.js` | Agregar tests de visibilidad y reset | — |
| Tests HistoryTable | `frontend/src/components/__tests__/HistoryTable.test.js` | Agregar tests de modal (abre con click, muestra notas, muestra "Sin observaciones") | — |

### Feature 18 — harvest_type
No requiere cambios directos. El patrón de agregar columna a `weighings` es
el mismo que usó esta feature y sirve como precedente.

### Feature 24 — reset_individual_pesos
No requiere cambios directos. El reset de notas es parte del reset general
del formulario.

### Feature 27 — sms_persistence
No requiere cambios directos. La tool `get_weighing_notes` usará la sesión
de BD estándar.

### Feature 28 — ai_multi_turn
No requiere cambios directos. El flujo multiturno manejará consultas de notas
como cualquier otra consulta AI.

---

## github_labels

`feature`, `database`, `frontend`, `ai-agent`, `sms`