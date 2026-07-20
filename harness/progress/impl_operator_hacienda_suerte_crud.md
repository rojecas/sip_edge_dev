# Implementación — Feature 38: Operator Hacienda/Suerte CRUD

## Fecha: 2026-07-19

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/haciendas.py` | L305: `require_role("admin")` → `require_any_role("admin", "operator")` en `update_existing_hacienda`. L356: mismo cambio en `update_existing_suerte`. DELETE sin cambios. POST ya usaba `require_any_role`. |
| `frontend/src/components/AdminHaciendas.svelte` | Agregado `let { allowDelete = true } = $props();` y envuelto botón eliminar con `{#if allowDelete}` |
| `frontend/src/components/AdminSuertes.svelte` | Agregado `let { allowDelete = true } = $props();` y envuelto botón eliminar con `{#if allowDelete}` |
| `frontend/src/App.svelte` | Reemplazados modales `HaciendaFormModal`/`SuerteFormModal` por `AdminHaciendas allowDelete={false}` / `AdminSuertes allowDelete={false}`. Limpiados imports sobrantes: `onMount`, `HaciendaFormModal`, `SuerteFormModal`, `buildQuery`, `api`, `ApiError`, `isRoute`, `navigate`, `ENDPOINTS`, `CONFIG`, y código asociado (`haciendasList`, `loadHaciendas`, `loadRemainingHaciendas`). |
| `tests/test_haciendas.py` | Renombrado `test_update_hacienda_as_operator` → `test_update_hacienda_as_operator_returns_200`: ahora crea hacienda, actualiza como operator, espera 200. Renombrado `test_update_suerte_as_operator` → `test_update_suerte_as_operator_returns_200`: ahora crea hacienda+suerte, actualiza como operator, espera 200. |
| `frontend/src/components/__tests__/AdminHaciendas.test.js` | Agregados 2 tests: `oculta boton eliminar cuando allowDelete=false` y `muestra boton eliminar por defecto (allowDelete=true)` |
| `frontend/src/components/__tests__/AdminSuertes.test.js` | Agregados 2 tests: `oculta boton eliminar cuando allowDelete=false` y `muestra boton eliminar por defecto (allowDelete=true)` |
| `src/static/` | Bundle frontend recompilado (`npm run build` + copy) |

## Impacto en features existentes

- **F4 (farm_lot_crud):** PUT endpoints de haciendas/suertes ahora aceptan operator. Admin mantiene acceso. DELETE sin cambios (solo admin).
- **F13 (frontend_login_kiosk):** App.svelte modificado — eliminados modales en kiosko, reemplazados por AdminHaciendas/AdminSuertes con `allowDelete={false}`.
- **F16 (frontend_admin_masterdata):** AdminHaciendas/AdminSuertes ahora aceptan prop `allowDelete` (default `true`). Sin romper admin — cuando no se pasa la prop, el comportamiento es idéntico al anterior.

## Trazabilidad

| R | Descripción | Test |
|---|------------|------|
| R1 | 4 pestañas en navegación kiosko | `KioskLayout.test.js` — 4 botones (ya existía) |
| R2 | Haciendas: listar, crear, editar (sin eliminar) | `AdminHaciendas.test.js` — allowDelete oculta botón eliminar |
| R3 | Suertes: listar, crear, editar (sin eliminar) | `AdminSuertes.test.js` — allowDelete oculta botón eliminar |
| R4 | POST haciendas operator → 201 | `test_create_hacienda_as_operator_returns_201` (ya existía) |
| R5 | PUT haciendas operator → 200 | `test_update_hacienda_as_operator_returns_200` |
| R6 | POST suertes operator → 201 | `test_create_suerte_as_operator_returns_201` (ya existía) |
| R7 | PUT suertes operator → 200 | `test_update_suerte_as_operator_returns_200` |
| R8 | DELETE solo admin (403 para operator) | `test_delete_hacienda_as_operator` (sigue 403), `test_delete_suerte_as_operator` (sigue 403) |
| R9 | Disponibilidad inmediata F36 | `test_new_hacienda_available_after_creation` (ya existía) |
| R10 | Errores duplicado 409 | `test_create_hacienda_duplicate_codigo`, `test_create_suerte_duplicate_codigo` (ya existían) |

## Resultados

- **Backend tests:** 57/57 OK (tests.test_haciendas)
- **Frontend tests (nuevos):** 4/4 OK (allowDelete en AdminHaciendas + AdminSuertes)
- **Frontend tests (pre-existentes):** 7 fallos pre-existentes no relacionados (componentes sin columna "ID", selectores `.btn-edit`/`.btn-delete` inexistentes)
- **Build frontend:** OK
- **Despliegue a src/static:** Verificado (assets/index-*.js dentro de assets/)

## Skills consultados
- **svelte5** — Cargado desde `.opencode/skills/svelte5/SKILL.md`. Aplicado para:
  `$props()` (prop `allowDelete` en AdminHaciendas y AdminSuertes), `$state` (estado local de componentes), `{#if}` (renderizado condicional del botón eliminar).
