# Tasks — Paginación en endpoints y tablas de Usuarios y Backups

> Cada task referencia los R&lt;n&gt; que cubre. El implementer marca `[x]` al completar.
> Orden de ejecución recomendado: backend → tests backend → frontend → tests frontend.

---

## Fase 1 — Modelo compartido

- [x] T1 — Crear `src/schemas.py` con el modelo `PaginatedResponse[T]` (Generic[T], BaseModel).
      Cubre: R9.

- [x] T2 — En `src/haciendas.py`: eliminar la definición local de `PaginatedResponse` y agregar
      `from src.schemas import PaginatedResponse`. Verificar que `get_haciendas()` sigue funcionando.
      Cubre: R9.

- [x] T3 — En `src/weighings.py`: eliminar la definición local de `PaginatedResponse` y agregar
      `from src.schemas import PaginatedResponse`. Verificar que `list_weighings()` sigue funcionando.
      Cubre: R9.

## Fase 2 — Backend: GET /api/users paginado

- [x] T4 — En `src/users.py`: agregar `from src.schemas import PaginatedResponse`. Agregar imports
      necesarios (`math`, `Query` de FastAPI). Cubre: R9.

- [x] T5 — Modificar la función `get_users()` (endpoint GET /api/users):
      - Agregar parámetros query `page: int = Query(1, ge=1)` y `page_size: int = Query(20, ge=1, le=100)`.
      - Cambiar `response_model` de `List[UserResponse]` a `PaginatedResponse[UserResponse]`.
      - Agregar lógica: `total = query.count()`, `total_pages = max(1, math.ceil(total / page_size))`,
        `offset = (page - 1) * page_size`, `records = query.offset(offset).limit(page_size).all()`.
      - Retornar `PaginatedResponse(items=..., total=..., page=..., page_size=..., total_pages=...)`.
      Cubre: R1, R2, R3, R4.

## Fase 3 — Backend: GET /api/backup/status paginado

- [x] T6 — En `src/main.py`: agregar `import math`. Agregar `from src.schemas import PaginatedResponse`.
      Definir `BackupLogResponse` como Pydantic BaseModel con `from_attributes = True` usando los
      campos de `BackupLog` (id, filename, file_size, local_checksum, usb_copied, usb_checksum,
      error_message, created_at). Crear helper `_backup_log_to_response(log) -> BackupLogResponse`.
      Cubre: R5.

- [x] T7 — Modificar `get_backup_status()`:
      - Agregar parámetros query `page: int = Query(1, ge=1)` y `page_size: int = Query(10, ge=1, le=100)`.
      - Cambiar respuesta a `PaginatedResponse[BackupLogResponse]`.
      - Reemplazar `.limit(10)` fijo con lógica de paginación: count, total_pages, offset, limit.
      - Retornar `PaginatedResponse(items=..., total=..., page=..., page_size=..., total_pages=...)`.
      Cubre: R5, R6, R7, R8.

## Fase 4 — Tests backend

- [x] T8 — En `tests/test_users.py`: agregar clase `TestUserPagination` o métodos en `TestUserManagement`
      que verifiquen:
      - `test_list_users_default_pagination`: GET /api/users sin parámetros → status 200, response
        tiene keys items/total/page/page_size/total_pages, page=1, page_size=20.
      - `test_list_users_with_custom_pagination`: GET /api/users?page=1&page_size=5 → page_size=5.
      - `test_list_users_page_beyond_total`: GET /api/users?page=999 → items vacío, page=999,
        total_pages calculado correctamente.
      Cubre: R15.

- [x] T9 — En `tests/test_backup.py`: agregar tests de paginación en `TestBackupEndpoints` que
      verifiquen:
      - `test_get_status_default_pagination`: GET /api/backup/status → response paginado, page=1,
        page_size=10.
      - `test_get_status_with_custom_pagination`: GET /api/backup/status?page=1&page_size=5 →
        page_size=5.
      - `test_get_status_page_beyond_total`: GET /api/backup/status?page=999 → items vacío.
      Cubre: R16.

## Fase 5 — Frontend: AdminUsers.svelte con paginación

- [x] T10 — En `AdminUsers.svelte`:
      - Agregar import: `import { api, ApiError, buildQuery } from "../lib/api.js";`
        (buildQuery ya existe en api.js).
      - Agregar variables de estado: `currentPage = $state(1)`, `totalPages = $state(1)`,
        `totalItems = $state(0)`, `pageSize = $state(20)`.
      Cubre: R10.

- [x] T11 — Modificar `loadUsers()` en `AdminUsers.svelte` para:
      - Construir query string con `buildQuery({ page: currentPage, page_size: pageSize })`.
      - Leer `result.items`, `result.total_pages`, `result.total` del response paginado.
      Cubre: R10.

- [x] T12 — Agregar funciones de paginación en `AdminUsers.svelte`:
      - `goToPage(page)`: actualiza currentPage y llama loadUsers().
      - `changePageSize(e)`: parsea pageSize de event target, resetea currentPage=1, llama loadUsers().
      Cubre: R12.

- [x] T13 — Agregar HTML de controles de paginación en `AdminUsers.svelte` dentro del table-wrapper,
      debajo de la tabla, condicional a `totalPages > 1`:
      - Botón "Anterior" deshabilitado si `currentPage <= 1`.
      - Select de page size con opciones 10, 20, 50, 100.
      - Texto "Página {currentPage} de {totalPages} ({totalItems} registros)".
      - Botón "Siguiente" deshabilitado si `currentPage >= totalPages`.
      Cubre: R10, R12, R13, R14.

## Fase 6 — Frontend: AdminBackup.svelte con paginación

- [x] T14 — En `AdminBackup.svelte`:
      - Agregar import: `import { api, ApiError, buildQuery } from "../lib/api.js";`.
      - Agregar variables: `currentPage = $state(1)`, `totalPages = $state(1)`,
        `totalItems = $state(0)`, `pageSize = $state(10)`.
      Cubre: R11.

- [x] T15 — Modificar `loadBackups()` en `AdminBackup.svelte` para usar buildQuery con parámetros
      de paginación y leer `result.items`, `result.total_pages`, `result.total`.
      Cubre: R11.

- [x] T16 — Agregar funciones `goToPage(page)` y `changePageSize(e)` en `AdminBackup.svelte`.
      Cubre: R12.

- [x] T17 — Agregar HTML de controles de paginación en `AdminBackup.svelte` (mismo patrón que
      AdminUsers, condicional a totalPages > 1).
      Cubre: R11, R12, R13, R14.

## Fase 7 — Tests frontend

- [x] T18 — En `AdminUsers.test.js`: agregar tests que verifiquen:
      - Los controles de paginación se renderizan cuando hay múltiples páginas.
      - Al cambiar page size, se resetea a page=1 y se recargan datos.
      Cubre: R17.

- [x] T19 — En `AdminBackup.test.js`: agregar tests que verifiquen:
      - Los controles de paginación se renderizan correctamente.
      - La navegación Anterior/Siguiente modifica currentPage y recarga datos.
      Cubre: R18.
