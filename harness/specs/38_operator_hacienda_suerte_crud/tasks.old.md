# Tasks — Feature 38: Operator Hacienda/Suerte CRUD

## Backend — Guards de rol

- [ ] T1 — Cambiar guards de rol en endpoints de haciendas (`src/haciendas.py`):
    - [ ] T1.1 — `create_new_hacienda` (POST): `require_role("admin")` → `require_any_role("admin", "operator")`. Cubre: R4.
    - [ ] T1.2 — `update_hacienda` (PUT): `require_role("admin")` → `require_any_role("admin", "operator")`. Cubre: R5.
    - [ ] T1.3 — `delete_hacienda` (DELETE): `require_role("admin")` → `require_any_role("admin", "operator")`. Cubre: R6.

- [ ] T2 — Cambiar guards de rol en endpoints de suertes (`src/haciendas.py`):
    - [ ] T2.1 — `create_new_suerte` (POST): `require_role("admin")` → `require_any_role("admin", "operator")`. Cubre: R7.
    - [ ] T2.2 — `update_suerte` (PUT): `require_role("admin")` → `require_any_role("admin", "operator")`. Cubre: R8.
    - [ ] T2.3 — `delete_suerte` (DELETE): `require_role("admin")` → `require_any_role("admin", "operator")`. Cubre: R9.

## Frontend — Navegación y routing

- [ ] T3 — Modificar `frontend/src/components/KioskLayout.svelte`:
    - [ ] T3.1 — Agregar función `goToHaciendas()`: `navigate("/kiosco/haciendas")`. Cubre: R1.
    - [ ] T3.2 — Agregar función `goToSuertes()`: `navigate("/kiosco/suertes")`. Cubre: R1.
    - [ ] T3.3 — Agregar botón "Haciendas" con class `nav-btn` y `class:active`. Cubre: R1.
    - [ ] T3.4 — Agregar botón "Suertes" con class `nav-btn` y `class:active`. Cubre: R1.

- [ ] T4 — Modificar `frontend/src/App.svelte`:
    - [ ] T4.1 — Importar `AdminHaciendas` y `AdminSuertes` (ya existen). Cubre: R1.
    - [ ] T4.2 — Agregar condición `{:else if currentRoute === "/kiosco/haciendas"}` que renderice `<AdminHaciendas />`. Cubre: R1, R2.
    - [ ] T4.3 — Agregar condición `{:else if currentRoute === "/kiosco/suertes"}` que renderice `<AdminSuertes />`. Cubre: R1, R3.
    - [ ] T4.4 — ELIMINAR imports y código sobrante de la implementación anterior: `HaciendaFormModal`, `SuerteFormModal`, `haciendasList`, `loadHaciendas`, `onMount` (si ya no se usan). Cubre: limpieza.

- [ ] T5 — Compilar frontend y copiar a `src/static/`:
    - [ ] T5.1 — `cd frontend && npm run build`. Cubre: despliegue.
    - [ ] T5.2 — `Remove-Item src/static -Recurse -Force; New-Item -ItemType Directory src/static; Copy-Item -Recurse frontend/dist/* -Destination src/static/`. Cubre: despliegue.
    - [ ] T5.3 — Verificar que `src/static/assets/` contiene los archivos JS y CSS compilados (NO aplanados en `src/static/`). Cubre: despliegue.

## Tests

- [ ] T6 — Actualizar tests en `tests/test_haciendas.py`:
    - [ ] T6.1 — `test_create_hacienda_as_operator_returns_201` (cambiar 403 → 201). Cubre: R4.
    - [ ] T6.2 — `test_update_hacienda_as_operator_returns_200` (cambiar 403 → 200). Cubre: R5.
    - [ ] T6.3 — `test_delete_hacienda_as_operator_returns_204` (cambiar 403 → 204). Cubre: R6.
    - [ ] T6.4 — `test_create_suerte_as_operator_returns_201` (cambiar 403 → 201). Cubre: R7.
    - [ ] T6.5 — `test_update_suerte_as_operator_returns_200` (cambiar 403 → 200). Cubre: R8.
    - [ ] T6.6 — `test_delete_suerte_as_operator_returns_204` (cambiar 403 → 204). Cubre: R9.
    - [ ] T6.7 — `test_create_hacienda_duplicate_codigo_returns_409`. Cubre: R12.
    - [ ] T6.8 — `test_create_suerte_duplicate_codigo_returns_409`. Cubre: R12.
    - [ ] T6.9 — Verificar tests admin existentes siguen pasando. Cubre: R4-R9.

- [ ] T7 — Tests de frontend:
    - [ ] T7.1 — `KioskLayout.test.js` verifica 4 botones con etiquetas Pesaje, Historial, Haciendas, Suertes. Cubre: R1.
    - [ ] T7.2 — Confirmar que `AdminHaciendas.test.js` y `AdminSuertes.test.js` existentes siguen pasando. Cubre: R2, R3.

## Verificación

- [ ] T8 — Ejecutar `./harness/init.ps1` y verificar que todas las secciones pasan (incluyendo tests).
