# Requirements — Paginación en endpoints y tablas de Usuarios y Backups

> Feature 21: Agregar paginación a GET /api/users y GET /api/backup/status,
> y sus correspondientes tablas frontend AdminUsers.svelte y AdminBackup.svelte.
> Patrón de paginación existente en GET /api/haciendas (src/haciendas.py).
>
> Notación: EARS estricto (Ubicuo / Evento / Estado / Opcional / No deseado).

---

## R1
CUANDO un usuario admin autenticado invoca GET /api/users?page=1&page_size=20,
el sistema DEBE devolver un objeto JSON con la estructura:
`{items: List[UserResponse], total: int, page: int, page_size: int, total_pages: int}`.
Cubre: AC1.

## R2
CUANDO se invoca GET /api/users sin los parámetros query `page` y `page_size`,
el sistema DEBE usar page=1 y page_size=20 como valores por defecto.
Cubre: AC2.

## R3
SI GET /api/users recibe page < 1, page_size < 1 o page_size > 100
ENTONCES el sistema DEBE devolver HTTP 422 (Unprocessable Entity).

## R4
CUANDO GET /api/users recibe page > total_pages, el sistema DEBE devolver
items vacío con total, page, page_size y total_pages calculados correctamente.

## R5
CUANDO un usuario admin autenticado invoca GET /api/backup/status?page=1&page_size=10,
el sistema DEBE devolver un objeto JSON paginado con la estructura:
`{items: List[BackupLogResponse], total: int, page: int, page_size: int, total_pages: int}`.
Cubre: AC4.

## R6
CUANDO se invoca GET /api/backup/status sin los parámetros query `page` y `page_size`,
el sistema DEBE usar page=1 y page_size=10 como valores por defecto.

## R7
SI GET /api/backup/status recibe page < 1, page_size < 1 o page_size > 100
ENTONCES el sistema DEBE devolver HTTP 422 (Unprocessable Entity).

## R8
CUANDO GET /api/backup/status recibe page > total_pages, el sistema DEBE devolver
items vacío con total, page, page_size y total_pages calculados correctamente.

## R9
El modelo genérico PaginatedResponse[T] (items: list[T], total: int, page: int,
page_size: int, total_pages: int) DEBE extraerse a un módulo compartido
`src/schemas.py` y ser importado por `src/haciendas.py`, `src/weighings.py`,
`src/users.py` y `src/main.py`, eliminando las definiciones duplicadas
existentes en `src/haciendas.py` y `src/weighings.py`.

## R10
AdminUsers.svelte DEBE mostrar controles de paginación funcionales que incluyan:
botón "Anterior", botón "Siguiente", un selector de page size con opciones
10, 20, 50, 100, y el texto informativo "Página X de Y (Z registros)".
Cubre: AC3.

## R11
AdminBackup.svelte DEBE mostrar controles de paginación funcionales que incluyan:
botón "Anterior", botón "Siguiente", un selector de page size con opciones
10, 20, 50, 100, y el texto informativo "Página X de Y (Z registros)".
Cubre: AC5.

## R12
CUANDO el usuario cambia el valor del selector page size en AdminUsers.svelte
o AdminBackup.svelte, el sistema DEBE reiniciar a page=1, actualizar el page_size
y recargar los datos del endpoint paginado correspondiente.

## R13
MIENTRAS totalPages <= 1, los controles de paginación DEBEN ocultarse
en AdminUsers.svelte y AdminBackup.svelte.

## R14
CUANDO currentPage === 1, el botón "Anterior" DEBE estar deshabilitado.
CUANDO currentPage >= totalPages, el botón "Siguiente" DEBE estar deshabilitado.

## R15
test_users.py DEBE incluir al menos 3 tests de paginación que verifiquen:
(a) paginación con valores por defecto retorna el formato correcto,
(b) paginación con page y page_size explícitos funciona,
(c) page > total_pages retorna items vacío.
Cubre: AC6.

## R16
test_backup.py DEBE incluir al menos 3 tests de paginación que verifiquen:
(a) paginación con valores por defecto retorna el formato correcto,
(b) paginación con page y page_size explícitos funciona,
(c) page > total_pages retorna items vacío.
Cubre: AC6.

## R17
AdminUsers.test.js DEBE verificar que los controles de paginación se renderizan
y que el cambio de page size dispara recarga con reset a page=1.
Cubre: AC7.

## R18
AdminBackup.test.js DEBE verificar que los controles de paginación se renderizan
y que la navegación entre páginas (Anterior/Siguiente) modifica currentPage
correctamente.
Cubre: AC7.
