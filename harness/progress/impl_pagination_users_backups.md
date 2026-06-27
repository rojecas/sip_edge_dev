# Implementation Progress — Feature 21: pagination_users_backups

## Resumen

Feature 21 implementada: Paginación en GET /api/users y GET /api/backup/status (backend) y controles de paginación en AdminUsers.svelte y AdminBackup.svelte (frontend). Modelo PaginatedResponse extraído a `src/schemas.py` para eliminar duplicación.

## Trazabilidad R<n> → Tests

| Requirement | Test | Archivo |
|-------------|------|---------|
| R1 | `test_list_users_as_admin` | `tests/test_users.py` |
| R2 | `test_list_users_default_pagination` | `tests/test_users.py` |
| R3 | FastAPI validation `ge=1, le=100` (auto-tested) | Pydantic/FastAPI |
| R4 | `test_list_users_page_beyond_total` | `tests/test_users.py` |
| R5 | `test_get_status_with_admin_returns_200` | `tests/test_backup.py` |
| R6 | `test_get_status_default_pagination` | `tests/test_backup.py` |
| R7 | FastAPI validation `ge=1, le=100` (auto-tested) | Pydantic/FastAPI |
| R8 | `test_get_status_page_beyond_total` | `tests/test_backup.py` |
| R9 | All haciendas/weighings tests passing | `tests/test_haciendas.py`, `tests/test_weighings.py` |
| R10 | Paginación UI tests existentes en `AdminUsers.test.js` | `frontend/src/components/__tests__/AdminUsers.test.js` |
| R11 | `test_get_status_default_pagination`, paginación UI tests en `AdminBackup.test.js` | `tests/test_backup.py`, `frontend/src/components/__tests__/AdminBackup.test.js` |
| R12 | `changePageSize` resetea page=1 en `AdminUsers.test.js` y `AdminBackup.test.js` | Tests frontend |
| R13 | "oculta controles cuando hay una sola pagina" en `AdminBackup.test.js` | `frontend/src/components/__tests__/AdminBackup.test.js` |
| R14 | "Anterior deshabilitado en primera pagina", "Siguiente deshabilitado en ultima" en `AdminBackup.test.js` | `frontend/src/components/__tests__/AdminBackup.test.js` |
| R15 | 3 tests de paginación en `TestUserManagement` | `tests/test_users.py` |
| R16 | 3 tests de paginación en `TestBackupEndpoints` | `tests/test_backup.py` |
| R17 | Paginación UI tests existentes en `AdminUsers.test.js` | `frontend/src/components/__tests__/AdminUsers.test.js` |
| R18 | Nuevos tests de paginación en `AdminBackup.test.js` | `frontend/src/components/__tests__/AdminBackup.test.js` |
| R3 (users) | `test_list_users_with_custom_pagination` | `tests/test_users.py` |
| R7 (backup) | `test_get_status_with_custom_pagination` | `tests/test_backup.py` |

## Archivos modificados

### Creados
| Archivo | Descripción |
|---------|-------------|
| `src/schemas.py` | Modelo genérico `PaginatedResponse[T]` compartido |

### Modificados (backend)
| Archivo | Cambio |
|---------|--------|
| `src/haciendas.py` | Eliminada definición local de PaginatedResponse, importa desde `src.schemas` |
| `src/weighings.py` | Eliminada definición local de PaginatedResponse, importa desde `src.schemas` |
| `src/users.py` | Endpoint GET /api/users paginado: parámetros `page`/`page_size`, response_model `PaginatedResponse[UserResponse]`, lógica count/offset/limit |
| `src/main.py` | Agregado `import math`, `BackupLogResponse` Pydantic model, helper `_backup_log_to_response()`, endpoint GET /api/backup/status paginado |
| `tests/test_users.py` | Actualizado `test_list_users_as_admin` para respuesta paginada; agregados 3 tests de paginación |
| `tests/test_backup.py` | Actualizado `test_get_status_with_admin_returns_200` para respuesta paginada; agregados 3 tests de paginación |
| `tests/test_password_reset.py` | Actualizados `test_user_list_hides_reset_pin` y `test_user_response_includes_force_password_change` para acceder a `data["items"]` |

### Modificados (frontend)
| Archivo | Cambio |
|---------|--------|
| `frontend/src/components/AdminUsers.svelte` | Import `buildQuery`, variables `currentPage`/`totalPages`/`totalItems`/`pageSize` ($state), `loadUsers()` paginado, funciones `goToPage()`/`changePageSize()`, HTML controles paginación + CSS |
| `frontend/src/components/AdminBackup.svelte` | Import `buildQuery`, variables `currentPage`/`totalPages`/`totalItems`/`pageSize` ($state), `loadBackups()` paginado, funciones `goToPage()`/`changePageSize()`, HTML controles paginación + CSS |
| `frontend/src/components/__tests__/AdminBackup.test.js` | Agregado `buildQuery` al mock, agregado `fireEvent` import, actualizados todos los `api.get` mocks con `total`/`total_pages`, agregados 6 tests de paginación |

## Impacto en features existentes

### Feature 3 — user_management
- **Archivo modificado:** `src/users.py` — endpoint GET /api/users cambió de retornar `List[UserResponse]` a `PaginatedResponse[UserResponse]`
- **Tests re-ejecutados:** `tests/test_users.py` (31 tests: OK), `tests/test_password_reset.py` TestUserResponseHidesResetFields (3 tests: OK)
- **Consumidores frontend:** `AdminUsers.svelte` ya fue actualizado en esta feature

### Feature 4 — farm_lot_crud
- **Archivo modificado:** `src/haciendas.py` — solo eliminó definición local de `PaginatedResponse`, importa desde `src/schemas.py` (clase idéntica)
- **Tests re-ejecutados:** `tests/test_haciendas.py` (all passed)

### Feature 6 — weighing_capture
- **Archivo modificado:** `src/weighings.py` — solo eliminó definición local de `PaginatedResponse`, importa desde `src/schemas.py` (clase idéntica)
- **Tests re-ejecutados:** `tests/test_weighings.py` (32 tests: OK)

### Feature 10 — backup_system
- **Archivo modificado:** `src/main.py` — endpoint GET /api/backup/status cambió de retornar lista plana a `PaginatedResponse[BackupLogResponse]`
- **Tests re-ejecutados:** `tests/test_backup.py` (34 tests: OK)
- **Consumidores frontend:** `AdminBackup.svelte` ya fue actualizado en esta feature

### Feature 12 — password_reset_sms
- **Archivo modificado:** `tests/test_password_reset.py` — actualizados 2 tests que iteraban sobre respuesta como lista
- **Tests re-ejecutados:** TestUserResponseHidesResetFields (3 tests: OK)

### Feature 16 — frontend_admin_masterdata
- **Archivo modificado:** `AdminUsers.svelte` — agregada paginación
- **Tests:** `AdminUsers.test.js` (tests ya esperaban respuesta paginada)

## Skills consultados
- `svelte5` — Reglas de Svelte 5 (runas $state, $derived, $effect): cumplidas. Verificado que `.svelte` usa `$state` correctamente, `onMount` tiene su import explícito, no se usa `new App()` y stores no aplican en estos componentes.

## Verificación

- Backend tests: 461 passed (5 errores pre-existentes de asyncio event loop en dispatcher tests, no relacionados)
- init.ps1 secciones 1-5: OK

## Correcciones post-review

Se corrigieron 4 hallazgos del reviewer (sesión 2026-06-12):

### Issue 1 — [BUG crítico] currentPage no se actualiza desde result.page

**Archivos modificados:**
- `frontend/src/components/AdminUsers.svelte` — Agregado `currentPage = result.page || 1;` en `loadUsers()` (línea después de `users = result.items || []`).
- `frontend/src/components/AdminBackup.svelte` — Agregado `currentPage = result.page || 1;` en `loadBackups()` (línea después de `backups = result.items || []`).

**Estado:** ✅ Corregido.

### Issue 2 — [Cobertura R17] Falta test de page size reset en AdminUsers.test.js

**Archivos modificados:**
- `frontend/src/components/__tests__/AdminUsers.test.js` — Agregado test `"cambiar page size resetea a page=1 (R17)"` en el bloque `describe("AdminUsers — paginacion (C1, R1)")`. El test verifica que al cambiar el page size a 50 se llama a `api.get` con `page_size=50` y `page=1`.

**Estado:** ✅ Corregido.

### Issue 3 — [Protocolo] Documentar skills consultados

**Archivos modificados:**
- `harness/progress/impl_pagination_users_backups.md` — Agregada sección `## Skills consultados` con referencia a `svelte5` y verificación de cumplimiento de reglas.

**Estado:** ✅ Corregido.

### Issue 4 — [GitHub] Agregar github_issue

**Verificación:** Se consultó `gh issue list --repo rojecas/sip_edge` y no existe un issue abierto para la feature 21 (`pagination_users_backups`).

**Acción:** No se crea issue (corresponde al release-manager). No se modifica `feature_list.json` porque no hay URL que agregar. Queda pendiente de creación por el release-manager.

**Estado:** ⚠️ Pendiente — el release-manager debe crear el issue de GitHub para esta feature.
