# Design — Feature 36: Entrada de Código de Hacienda en Kiosko y AdminSuertes

> Decisiones técnicas tomadas antes de implementar.
> Apoyado en `docs/architecture.md`, `docs/conventions.md`.

---

## Archivos a crear

| Archivo | Propósito |
|---------|-----------|
| `frontend/src/components/HaciendaCodeInput.svelte` | Componente Svelte compartido que encapsula la entrada de código, búsqueda vía API, display confirmado, modal de error y botón limpiar. |

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `src/haciendas.py` | Agregar parámetro `search: Optional[str]` al endpoint `GET /api/haciendas`. Filtro case-insensitive sobre `codigo`. |
| `frontend/src/components/KioskForm.svelte` | Reemplazar el `<select>` de hacienda (líneas 314–333) por `<HaciendaCodeInput>`. Eliminar `haciendas`, `loadHaciendas()`, `loadRemainingHaciendas()`. El componente emite el `id` de la hacienda seleccionada. |
| `frontend/src/components/AdminSuertes.svelte` | Reemplazar el `<select>` de hacienda (líneas 227–236) por `<HaciendaCodeInput>`. Eliminar `haciendas`, `loadHaciendas()`, `loadRemainingHaciendas()`. El componente emite el `id` de la hacienda seleccionada. |
| `tests/test_haciendas.py` | Agregar tests para el nuevo parámetro `search` en `GET /api/haciendas`. |

## Firmas nuevas

### Backend — `src/haciendas.py`

```python
# Nuevo parámetro en get_haciendas():
search: Optional[str] = Query(None, description="Case-insensitive exact match on codigo"),

# Modificación interna (líneas 258+):
if search:
    query = query.filter(func.lower(Hacienda.codigo) == search.lower())
```

### Frontend — `HaciendaCodeInput.svelte`

```svelte
<!-- Props -->
<script>
  let { onSelect, placeholder = "Ingrese código de hacienda" } = $props();
  // onSelect: callback cuando se confirma una hacienda: function(hacienda: HaciendaResponse | null)

  // Internal state
  let inputValue = $state("");
  let selectedHacienda = $state(null);   // HaciendaResponse when confirmed
  let showErrorModal = $state(false);
  let searchCode = $state("");           // code that failed to resolve
  let loading = $state(false);
</script>
```

### Formato de display

Un único formato `CODIGO - NOMBRE` para todas las vistas (ej. `131 - Hacienda San José`).
No se requiere prop `format` — el componente usa este formato fijo.

### HaciendaCodeInput API (emit signals)

| Señal | Tipo | Cuándo |
|-------|------|--------|
| `onSelect(hacienda)` | `HaciendaResponse` | Código resuelto exitosamente |
| `onSelect(null)` | `null` | Código limpiado (botón x) |

## Excepciones

No se crean nuevas excepciones. Se reutilizan:
- `ApiError` (frontend) para errores de red.
- `HTTPException` 422 (backend) si `search` tiene longitud 0 (manejado por Pydantic/FastAPI).

## Contrato API

### GET /api/haciendas — Nuevo parámetro `search`

**Request:**
```
GET /api/haciendas?search=131&page_size=1
GET /api/haciendas?search=a16&page_size=1   (matchea "A16", case-insensitive)
```

**Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "codigo": "131",
      "nombre": "Hacienda San José",
      "created_at": "2026-01-15T10:00:00",
      "updated_at": "2026-06-01T08:30:00",
      "created_by": 1,
      "created_by_username": "admin"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 1,
  "total_pages": 1
}
```

**Response cuando no hay match:**
```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 1,
  "total_pages": 0
}
```

## Persistencia

No aplica. Esta feature no toca la base de datos — solo modifica la capa de consulta (query filter) y la UI.

## Alternativa descartada

### Alternativa A: Resolución cliente-side contra todas las haciendas cargadas

Se descartó porque el frontend carga haciendas con paginación (default 100 por página). Una hacienda con 500+ registros requeriría 5+ llamadas para poblar el array completo. Además, en la práctica las páginas de fondo pueden fallar silenciosamente (ver `loadRemainingHaciendas` con `catch` vacío), dejando el catálogo incompleto. La resolución vía API es más confiable, simple y consistente con la paginación existente.

### Alternativa B: Endpoint dedicado `GET /api/haciendas/lookup?codigo=X`

Se descartó en favor de agregar un parámetro `search` al endpoint existente. Razon: el endpoint actual ya retorna `PaginatedResponse[HaciendaResponse]`, y con `page_size=1` se obtiene exactamente el comportamiento deseado. Un endpoint separado sería duplicación innecesaria que viola el principio de capas claras.

### Alternativa C: Búsqueda case-sensitive

Se descartó porque agrega fricción innecesaria al usuario. En campo, los operadores no diferencian entre mayúsculas y minúsculas al teclear códigos (ej. `a16` vs `A16`). La búsqueda case-insensitive mediante `func.lower()` en ambos lados de la comparación elimina este problema sin impacto de rendimiento significativo.

## Impacto en APIs existentes

### Feature 4 — farm_lot_crud (GET /api/haciendas)

| Item | Cambio | Retrocompatible |
|------|--------|----------------|
| Parámetro `search` en `GET /api/haciendas` | Nuevo parámetro opcional | Sí — el default es `None`, los llamantes existentes no se ven afectados |
| Filtro SQL `func.lower(Hacienda.codigo) == search.lower()` | Solo se aplica si `search` no es `None` | Sí — la query sin search es idéntica a la actual |

### Feature 13 — frontend_login_kiosk (KioskForm)
| Item | Cambio | Retrocompatible |
|------|--------|----------------|
| KioskForm.svelte | El `<select>` se reemplaza por `<HaciendaCodeInput>` | No — el markup cambia. Las props y el comportamiento de salida (`selectedHaciendaId`) se conservan. |
| `selectedHaciendaId` | Sigue siendo el state que usa el formulario | Sí — el componente emite el `id` de la misma forma. |

### Feature 16 — frontend_admin_masterdata (AdminSuertes)
| Item | Cambio | Retrocompatible |
|------|--------|----------------|
| AdminSuertes.svelte | El `<select>` se reemplaza por `<HaciendaCodeInput>` | No — el markup cambia. La reactividad a `selectedHaciendaId` para cargar suertes se conserva. |

### Feature 38 — operator_hacienda_suerte_crud
| Item | Cambio | Retrocompatible |
|------|--------|----------------|
| AdminSuertes (reusado en kiosko) | Mismo cambio que Feature 16 | Misma compatibilidad. |
| Ruta `/kiosco/haciendas` | El botón [Crear nueva hacienda] del modal navega aquí | Sí — la ruta ya existe y está implementada. |

### Feature 39 — hacienda_suerte_created_by
No hay impacto directo. Los schemas `HaciendaResponse` no se modifican.

## Análisis de impacto en features existentes

### Métodos modificados en `src/`

**`GET /api/haciendas` (función `get_haciendas` en `src/haciendas.py`)**

Consumidores (todos vía HTTP, no hay llamantes directos en Python):
| Consumidor | Archivo | Uso |
|------------|---------|-----|
| Feature 4 — farm_lot_crud | `tests/test_haciendas.py` | Tests CRUD |
| Feature 13 — KioskForm | `frontend/src/components/KioskForm.svelte:107` | `api.get(ENDPOINTS.HACIENDAS...)` |
| Feature 16 — AdminSuertes | `frontend/src/components/AdminSuertes.svelte:65` | `api.get(ENDPOINTS.HACIENDAS...)` |
| Feature 38 — AdminHaciendas | `frontend/src/components/AdminHaciendas.svelte` | `api.get(ENDPOINTS.HACIENDAS...)` |
| Feature 39 — created_by | `tests/test_haciendas.py` | Tests de created_by |

Ningún consumidor se rompe porque el nuevo parámetro es opcional.

**`KioskForm.svelte` (componente completo)**

Consumidores:
| Consumidor | Archivo | Uso |
|------------|---------|-----|
| Feature 13 — App.svelte root | `frontend/src/App.svelte:62` | `<KioskForm />` |

El cambio es interno al componente (reemplazar `<select>` por `<HaciendaCodeInput>`). La interfaz hacia `App.svelte` (sin props, sin eventos) no cambia.

**`AdminSuertes.svelte` (componente completo)**

Consumidores:
| Consumidor | Archivo | Uso |
|------------|---------|-----|
| Feature 16 — App.svelte (admin) | `frontend/src/App.svelte:76` | `<AdminSuertes />` |
| Feature 38 — App.svelte (kiosko) | `frontend/src/App.svelte:59` | `<AdminSuertes allowDelete={false} />` |

La prop `allowDelete` se conserva. El cambio es interno (reemplazar `<select>` por `<HaciendaCodeInput>`).
