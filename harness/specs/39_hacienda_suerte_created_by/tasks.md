# Tasks — Feature 39: Trazabilidad: Registro de usuario creador en Haciendas y Suertes

## Backend

- [x] T1 — Crear migración `2026_07_19_000001_add_created_by_to_haciendas.py`:
      ALTER TABLE `haciendas` ADD `created_by` BIGINT UNSIGNED NULL,
      ADD FK `fk_haciendas_created_by` → `users(id)` ON DELETE SET NULL.
      Cubre: R1.

- [x] T2 — Crear migración `2026_07_19_000002_add_created_by_to_suertes.py`:
      ALTER TABLE `suertes` ADD `created_by` BIGINT UNSIGNED NULL,
      ADD FK `fk_suertes_created_by` → `users(id)` ON DELETE SET NULL.
      Cubre: R2.

- [x] T3 — Modelo `Hacienda` en `src/models.py`: agregar columna `created_by`
      (BigInteger, FK → `users.id`, nullable) y relación `creator =
      relationship("User", foreign_keys=[created_by])`.
      Cubre: R1, R5, R9.

- [x] T4 — Modelo `Suerte` en `src/models.py`: agregar columna `created_by`
      (BigInteger, FK → `users.id`, nullable) y relación `creator =
      relationship("User", foreign_keys=[created_by])`.
      Cubre: R2, R6, R9.

- [x] T5 — Schema `HaciendaResponse` en `src/haciendas.py`: agregar campos
      `created_by: Optional[int] = None` y
      `created_by_username: Optional[str] = None`.
      Cubre: R5.

- [x] T6 — Schema `SuerteResponse` en `src/haciendas.py`: agregar campos
      `created_by: Optional[int] = None` y
      `created_by_username: Optional[str] = None`.
      Cubre: R6.

- [x] T7 — Función `_hacienda_to_response` en `src/haciendas.py`: incluir
      `created_by=h.created_by` y
      `created_by_username=h.creator.username if h.creator else None`.
      Cubre: R5, R9.

- [x] T8 — Función `_suerte_to_response` en `src/haciendas.py`: incluir
      `created_by=s.created_by` y
      `created_by_username=s.creator.username if s.creator else None`.
      Cubre: R6, R9.

- [x] T9 — Función `create_hacienda` en `src/haciendas.py`: agregar parámetro
      `user_id: int` y asignar `created_by=user_id` al crear `Hacienda(...)`.
      Cubre: R3.

- [x] T10 — Función `create_suerte` en `src/haciendas.py`: agregar parámetro
      `user_id: int` y asignar `created_by=user_id` al crear `Suerte(...)`.
      Cubre: R4.

- [x] T11 — Router `create_new_hacienda` en `src/haciendas.py`: modificar
      dependencia para capturar `current_user: dict = Depends(check_inactivity)`
      y pasar `current_user["user_id"]` a `create_hacienda(db, body, user_id)`.
      Cubre: R3.

- [x] T12 — Router `create_new_suerte` en `src/haciendas.py`: modificar
      dependencia para capturar `current_user: dict = Depends(check_inactivity)`
      y pasar `current_user["user_id"]` a `create_suerte(db, body, user_id)`.
      Cubre: R4.

## Frontend

- [x] T13 — Componente `AdminHaciendas.svelte`: agregar columna "Creado por"
      en `<thead>` y mostrar `h.created_by_username || "—"` en `<tbody>`.
      Cubre: R7.

- [x] T14 — Componente `AdminSuertes.svelte`: agregar columna "Creado por"
      en `<thead>` y mostrar `s.created_by_username || "—"` en `<tbody>`.
      Cubre: R8.

## Tests

- [x] T15 — Test `test_create_hacienda_sets_created_by`: crear hacienda como
      admin, verificar que response incluye `created_by` (int) y
      `created_by_username` (str). Cubre: R3, R5.

- [x] T16 — Test `test_create_suerte_sets_created_by`: crear hacienda y suerte
      como admin, verificar que response incluye `created_by` y
      `created_by_username`. Cubre: R4, R6.

- [x] T17 — Test `test_list_haciendas_includes_created_by`: crear varias
      haciendas, verificar `created_by` y `created_by_username` en GET list.
      Cubre: R5.

- [x] T18 — Test `test_list_suertes_includes_created_by`: crear suertes,
      verificar `created_by` y `created_by_username` en GET list.
      Cubre: R6.

- [x] T19 — Test `test_existing_records_have_null_created_by`: verificar que
      registros existentes (sin created_by en BD) exponen null.
      Cubre: R9.

- [x] T20 — Test `test_create_hacienda_without_token_still_returns_401`:
      verificar que POST sin token sigue dando 401 antes de tocar created_by.
      Cubre: R10.
