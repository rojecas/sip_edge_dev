# Tasks — Gestión de Haciendas y Suertes

> Marcar `[x]` al completar. Cada task referencia al menos un `R<n>`.

---

- [x] T1 — Añadir modelos ORM `Hacienda` y `Suerte` en `src/models.py`.
      Cubre: R1, R10.

- [x] T2 — Añadir migraciones en `database/migrations/` para crear tablas
      `haciendas` y `suertes`. Cubre: Persistencia.

- [x] T3 — Crear `src/haciendas.py` con esquemas Pydantic:
      `HaciendaCreate`, `HaciendaUpdate`, `HaciendaResponse`,
      `SuerteCreate`, `SuerteUpdate`, `SuerteResponse`.
      Cubre: R23, R24.

- [x] T4 — Implementar funciones CRUD de haciendas en `src/haciendas.py`:
      `list_haciendas`, `get_hacienda`, `create_hacienda`,
      `update_hacienda`, `soft_delete_hacienda`.
      Cubre: R1, R2, R3, R4, R5, R6, R7, R8, R9, R23.

- [x] T5 — Implementar funciones CRUD de suertes en `src/haciendas.py`:
      `list_suertes`, `get_suerte`, `create_suerte`, `update_suerte`,
      `soft_delete_suerte`.
      Cubre: R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R20, R24.

- [x] T6 — Registrar `router` con prefijo `/api/haciendas` y endpoints
      GET, POST, GET/{id}, PUT/{id}, DELETE/{id}. Todos con
      `Depends(check_inactivity)` + `Depends(require_role("admin"))`.
      Cubre: R21, R22.

- [x] T7 — Registrar `router` con prefijo `/api/suertes` y endpoints
      GET, POST, GET/{id}, PUT/{id}, DELETE/{id}. El GET lista filtra
      por `?hacienda_id=X` opcional. Todos con protección admin.
      Cubre: R11, R21, R22.

- [x] T8 — Registrar `haciendas_router` en `src/main.py` con
      `app.include_router(haciendas_router)`.
      Cubre: R1, R10.

- [x] T9 — Crear `tests/test_haciendas.py` con `TestHaciendas` clase.
      Tests de auth: `test_list_haciendas_without_token` (R21),
      `test_list_suertes_as_operator` (R22).
      Cubre: R21, R22.

- [x] T10 — Tests de CRUD haciendas: `test_list_haciendas` (R1),
      `test_create_hacienda` (R2), `test_get_hacienda` (R3),
      `test_get_hacienda_not_found` (R4), `test_update_hacienda` (R5),
      `test_update_hacienda_not_found` (R6), `test_soft_delete_hacienda` (R7),
      `test_soft_delete_hacienda_not_found` (R8),
      `test_create_hacienda_duplicate_codigo` (R9),
      `test_list_haciendas_excludes_deleted` (R7, R1).
      Cubre: R1–R9.

- [x] T11 — Tests de CRUD suertes: `test_list_suertes` (R10),
      `test_list_suertes_filter_by_hacienda` (R11),
      `test_create_suerte` (R12), `test_create_suerte_invalid_hacienda` (R13),
      `test_get_suerte` (R14), `test_get_suerte_not_found` (R15),
      `test_update_suerte` (R16), `test_update_suerte_not_found` (R17),
      `test_soft_delete_suerte` (R18), `test_soft_delete_suerte_not_found` (R19),
      `test_create_suerte_duplicate_codigo` (R20).
      Cubre: R10–R20.

- [x] T12 — Verificar trazabilidad en `progress/impl_farm_lot_crud.md`.
      Cubre: todos los R.

- [x] T13 — Ejecutar `python -m unittest discover -s tests -v` — todo verde.
      Cubre: verificación Nivel 1.

- [x] T14 — Ejecutar `./init.ps1` — todos los bloques `[OK]`.
      Cubre: verificación Nivel 3.
