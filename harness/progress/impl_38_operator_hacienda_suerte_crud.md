# Implementación — Feature 38: operator_hacienda_suerte_crud

## Fecha
2026-07-18

## Cambios realizados

| Archivo | Cambio |
|---------|--------|
| `src/haciendas.py` | `create_new_hacienda`: `require_role("admin")` → `require_any_role("admin", "operator")` (R6) |
| `src/haciendas.py` | `create_new_suerte`: `require_role("admin")` → `require_any_role("admin", "operator")` (R7) |
| `frontend/src/components/KioskLayout.svelte` | Funciones `goToHaciendas()` y `goToSuertes()` + 2 botones nav "Haciendas" y "Suertes" con estilo `.nav-btn` (R1) |
| `frontend/src/App.svelte` | Imports: `onMount`, `buildQuery`, `ApiError`, `navigate`, `ENDPOINTS`, `CONFIG`, `HaciendaFormModal`, `SuerteFormModal` (R1-R5) |
| `frontend/src/App.svelte` | Estado `haciendasList` + `onMount` carga paginada completa (R3, R10) |
| `frontend/src/App.svelte` | Ruta `/kiosco/haciendas` → `<HaciendaFormModal show={true} mode="create">` (R1, R2) |
| `frontend/src/App.svelte` | Ruta `/kiosco/suertes` → `<SuerteFormModal show={true} mode="create" haciendas={haciendasList}>` (R1, R3) |
| `frontend/src/App.svelte` | Estilo `.loading-text` (R3) |
| `tests/test_haciendas.py` | `test_create_hacienda_as_operator_returns_201` — 201 en vez de 403 (R6) |
| `tests/test_haciendas.py` | `test_create_suerte_as_operator_returns_201` — 201 en vez de 403 (R7) |
| `tests/test_haciendas.py` | `test_new_hacienda_available_after_creation` — disponibilidad post-creación (R10) |
| `frontend/src/components/__tests__/KioskLayout.test.js` | Test nuevo — verifica 4 botones `.nav-btn` con etiquetas Pesaje, Historial, Haciendas, Suertes (R1) |

## Trazabilidad

| Requirement | Test |
|-------------|------|
| R1 — Pestañas de navegación | `KioskLayout.test.js` — verifica existencia de 4 botones `.nav-btn` con etiquetas correctas |
| R2 — Formulario Haciendas | T4.7 (HaciendaFormModal renderizado en /kiosco/haciendas) |
| R3 — Formulario Suertes | T4.8 (SuerteFormModal renderizado en /kiosco/suertes) |
| R4 — Envío POST /api/haciendas | T4.7 (onSave llama api.post HACIENDAS) |
| R5 — Envío POST /api/suertes | T4.8 (onSave llama api.post SUERTES) |
| R6 — POST /api/haciendas permite operator | `test_create_hacienda_as_operator_returns_201` |
| R7 — POST /api/suertes permite operator | `test_create_suerte_as_operator_returns_201` |
| R8 — Error código hacienda duplicado | `test_create_hacienda_duplicate_codigo` (existente, sigue pasando) |
| R9 — Error código suerte duplicado | `test_create_suerte_duplicate_codigo` (existente, sigue pasando) |
| R10 — Disponibilidad inmediata | `test_new_hacienda_available_after_creation` |
| R11 — Validación cliente Haciendas | `HaciendaFormModal.test.js` (existente, sigue pasando) |
| R12 — Validación cliente Suertes | `SuerteFormModal.test.js` (existente, sigue pasando) |

## Impacto en features existentes

Ningún impacto negativo:
- **F4 (farm_lot_crud):** Admin sigue teniendo acceso completo. Los guards de PUT/DELETE no se modificaron.
- **F13 (frontend_login_kiosk):** KioskLayout y App.svelte modificados con adiciones compatibles; rutas existentes sin cambios.
- **F16 (frontend_admin_masterdata):** Modales HaciendaFormModal y SuerteFormModal reutilizados sin modificaciones; siguen funcionando en admin.

## Skills consultados

- **svelte5** — Cargado desde `.opencode/skills/svelte5/SKILL.md`. Aplicado para:
  `$state` (currentRoute en KioskLayout, haciendasList, showError en App.svelte),
  `$effect` (hashchange listener en KioskLayout),
  `$props()` (KioskLayout children), imports explícitos (onMount en App.svelte).
  Checklist verificado: `main.js` usa `mount(App, {target})` (no `new App()`),
  ningún `.js` usa runes (solo `.svelte`), `onMount` con import explícito,
  stores usan `writable`/`derived` de `svelte/store`.

## Verificación

- Backend: 57/57 tests pasan en `tests/test_haciendas.py`
- Frontend: KioskLayout.test.js, HaciendaFormModal.test.js y SuerteFormModal.test.js pasan
