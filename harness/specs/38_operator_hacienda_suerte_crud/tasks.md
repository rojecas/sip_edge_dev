# Tasks — Feature 38: Operator Hacienda/Suerte CRUD

## Backend — Guards de rol

- [x] T1 — Cambiar guard de `PUT /api/haciendas/{id}` en `src/haciendas.py`:
    - `require_role("admin")` → `require_any_role("admin", "operator")`. Cubre: R5.
    - POST y DELETE sin cambios (POST ya usa require_any_role, DELETE se mantiene solo admin).

- [x] T2 — Cambiar guard de `PUT /api/suertes/{id}` en `src/haciendas.py`:
    - `require_role("admin")` → `require_any_role("admin", "operator")`. Cubre: R7.
    - POST y DELETE sin cambios.

## Frontend — Prop allowDelete

- [x] T3 — Modificar `AdminHaciendas.svelte`:
    - [x] T3.1 — Agregar prop `let { allowDelete = true } = $props();`. Cubre: R2.
    - [x] T3.2 — Envolver botón de eliminar con `{#if allowDelete}...{/if}`. Cubre: R2.

- [x] T4 — Modificar `AdminSuertes.svelte`:
    - [x] T4.1 — Agregar prop `let { allowDelete = true } = $props();`. Cubre: R3.
    - [x] T4.2 — Envolver botón de eliminar con `{#if allowDelete}...{/if}`. Cubre: R3.

## Frontend — App.svelte

- [x] T5 — Modificar `frontend/src/App.svelte`:
    - [x] T5.1 — Reemplazar `<HaciendaFormModal ... />` por `<AdminHaciendas allowDelete={false} />` en ruta `/kiosco/haciendas`. Cubre: R1, R2.
    - [x] T5.2 — Reemplazar `<SuerteFormModal ... />` por `<AdminSuertes allowDelete={false} />` en ruta `/kiosco/suertes`. Cubre: R1, R3.
    - [x] T5.3 — Eliminar imports/código sobrante: `HaciendaFormModal`, `SuerteFormModal`, `haciendasList`, `loadHaciendas`, `loadRemainingHaciendas`, `onMount` (si ya no se usan), `buildQuery` (si ya no se usa). Cubre: limpieza.
    - Nota: `KioskLayout` ya tiene 4 botones de la iteración anterior. No se requieren cambios.

## Compilación frontend

- [x] T6 — Compilar y desplegar:
    - [x] T6.1 — `cd frontend && npm run build`. Cubre: despliegue.
    - [x] T6.2 — `Remove-Item src/static -Recurse -Force; Copy-Item -Recurse frontend/dist -Destination src/static`. Cubre: despliegue.
    - [x] T6.3 — Verificar `src/static/assets/index-*.js` y `index-*.css` existen dentro de `assets/`. Cubre: despliegue.

## Tests

- [x] T7 — Actualizar `tests/test_haciendas.py`:
    - [x] T7.1 — `test_update_hacienda_as_operator_returns_200` (ahora crea hacienda primero, actualiza como operator, espera 200). Cubre: R5.
    - [x] T7.2 — `test_update_suerte_as_operator_returns_200` (ahora crea hacienda y suerte primero, actualiza como operator, espera 200). Cubre: R7.
    - [x] T7.3 — `test_delete_hacienda_as_operator_returns_403` (verificado que SIGUE devolviendo 403). Cubre: R8.
    - [x] T7.4 — `test_delete_suerte_as_operator_returns_403` (verificado que SIGUE devolviendo 403). Cubre: R8.
    - [x] T7.5 — `test_create_hacienda_as_operator_returns_201` (ya existía, verificado que pasa). Cubre: R4.
    - [x] T7.6 — `test_create_suerte_as_operator_returns_201` (ya existía, verificado que pasa). Cubre: R6.
    - [x] T7.7 — Tests de admin existentes siguen pasando (57/57 OK). Cubre: regresión.
    - [x] T7.8 — Verificado que `test_new_hacienda_available_after_creation` sigue pasando. Cubre: R9.
    - [x] T7.9 — Verificado que tests de duplicado existentes siguen pasando. Cubre: R10.

- [x] T8 — Tests de frontend:
    - [x] T8.1 — `KioskLayout.test.js` verifica 4 botones (ya existía). Cubre: R1.
    - [x] T8.2 — `AdminHaciendas.test.js` verifica que botón eliminar se oculta con `allowDelete={false}`. Cubre: R2.
    - [x] T8.3 — `AdminSuertes.test.js` verifica que botón eliminar se oculta con `allowDelete={false}`. Cubre: R3.

## Verificación

- [x] T9 — Ejecutar `./harness/init.ps1` y verificar que todas las secciones pasan.

## Trazabilidad R → T → Test

| R | Descripción | Tasks | Test |
|---|------------|-------|------|
| R1 | 4 pestañas | T5 | T8.1 |
| R2 | Haciendas: listar, crear, editar (sin eliminar) | T3, T5.1 | T8.2 |
| R3 | Suertes: listar, crear, editar (sin eliminar) | T4, T5.2 | T8.3 |
| R4 | POST haciendas operator | — (ya hecho) | T7.5 |
| R5 | PUT haciendas operator | T1 | T7.1 |
| R6 | POST suertes operator | — (ya hecho) | T7.6 |
| R7 | PUT suertes operator | T2 | T7.2 |
| R8 | DELETE solo admin | — (sin cambios) | T7.3, T7.4 |
| R9 | Disponibilidad inmediata F36 | T7.8 | test_new_hacienda_available_after_creation |
| R10 | Errores duplicado 409 | T7.9 | test_create_hacienda_duplicate_codigo, test_create_suerte_duplicate_codigo |
