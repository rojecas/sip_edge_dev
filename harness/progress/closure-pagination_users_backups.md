# Cierre — pagination_users_backups

## Resumen

Se implementó soporte de paginación en los endpoints GET /api/users y GET /api/backup/status, y se agregaron controles de paginación (Anterior/Siguiente, selector de page size) en los componentes AdminUsers.svelte y AdminBackup.svelte. Se extrajo el modelo genérico `PaginatedResponse[T]` a `src/schemas.py`, refactorizando `haciendas.py` y `weighings.py` para usarlo. Se actualizaron 22 tests (backend + frontend) y se verificó que tests de features dependientes (haciendas, weighings, password_reset) continúan pasando.

## Archivos modificados

### Creados
| Archivo | Descripción |
|---------|-------------|
| `src/schemas.py` | Modelo genérico `PaginatedResponse[T]` compartido entre features |

### Modificados (backend)
| Archivo | Cambio |
|---------|--------|
| `src/haciendas.py` | Eliminada definición local de PaginatedResponse, importa desde `src.schemas` |
| `src/weighings.py` | Eliminada definición local de PaginatedResponse, importa desde `src.schemas` |
| `src/users.py` | Endpoint GET /api/users paginado con parámetros `page`/`page_size`, response_model `PaginatedResponse[UserResponse]` |
| `src/main.py` | Endpoint GET /api/backup/status paginado con `PaginatedResponse[BackupLogResponse]` |
| `tests/test_users.py` | Actualizado + 3 tests de paginación nuevos |
| `tests/test_backup.py` | Actualizado + 3 tests de paginación nuevos |
| `tests/test_password_reset.py` | Actualizados 2 tests para respuesta paginada |

### Modificados (frontend)
| Archivo | Cambio |
|---------|--------|
| `frontend/src/components/AdminUsers.svelte` | Import `buildQuery`, variables de estado de paginación ($state), funciones `goToPage()`/`changePageSize()`, controles HTML de paginación |
| `frontend/src/components/AdminBackup.svelte` | Import `buildQuery`, variables de estado de paginación ($state), funciones `goToPage()`/`changePageSize()`, controles HTML de paginación |
| `frontend/src/components/__tests__/AdminBackup.test.js` | 6 tests de paginación nuevos |

## Decisiones técnicas

- Se creó `src/schemas.py` con `PaginatedResponse[T]` genérico usando `Generic` de typing, en lugar de mantener definiciones duplicadas en cada módulo. Esta refactorización no cambia el contrato de los endpoints existentes (haciendas, weighings).
- Se usó `response_model=PaginatedResponse[UserResponse]` en FastAPI, que serializa correctamente el genérico con `model_serializer`.
- Los parámetros de paginación usan `Query(ge=1)` para page (default 1) y `Query(ge=1, le=100)` para page_size (default 20 en users, 10 en backups), validados por FastAPI/Pydantic.
- En frontend: se usó `$state` de Svelte 5 (runes) para `currentPage`, `totalPages`, `totalItems`, `pageSize`. Se importó `buildQuery` de `src/lib/utils.js` y `onMount` de `svelte`.
- Alternativa descartada: mantener PaginatedResponse duplicado en cada módulo. Se optó por extraerlo a `src/schemas.py` para evitar duplicación y facilitar mantenimiento futuro.

## Verificación

- [x] `./init.ps1` verde (secciones 1-5)
- [x] Backend: 461 tests passed (5 errores pre-existentes de asyncio event loop en dispatcher, no relacionados)
- [x] Frontend: AdminUsers.test.js (21/21), AdminBackup.test.js (17/17)
- [x] Trazabilidad R1-R18 → tests verificada en impl_pagination_users_backups.md
- [x] Review: APPROVED por reviewer (4 issues, 3 resueltos, 1 delegado a release-manager)
- [x] GitHub issue #19 creado y cerrado
- [x] Registrado en releases/tracker.json como pending

## Lecciones / pitfalls

- El BOM UTF-8 en `feature_list.json` (escrito por PS 5.1) causa `JSONDecodeError` en `github_sync.py`. Se corrigió el BOM del archivo directamente.
- La feature no tenía `github_issue` previo; el release-manager debió crearlo como parte del registro (no asignado al implementer).
- Los tests de AdminBackup.test.js requerían actualizar mocks con campos `total`/`total_pages` para soportar respuesta paginada.
