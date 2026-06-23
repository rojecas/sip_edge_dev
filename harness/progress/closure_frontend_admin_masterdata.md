# Cierre — frontend_admin_masterdata

## Resumen

Feature 16 implementa el CRUD completo de datos maestros (usuarios, haciendas, suertes) en el frontend Svelte 5 del módulo administrativo (/admin/*). Corrige 6 hallazgos de auditoría (C1, C2, C3, M1, M2, M4) y agrega 121 tests unitarios en 7 nuevos archivos de test. Todos los requirements R1-R20 tienen cobertura de test verificada.

## Archivos modificados

### Archivos fuente modificados
| Archivo | Cambio |
|---------|--------|
| `frontend/src/components/AdminUsers.svelte` | Paginación (C1) + manejo HTTP 409 (C3) |
| `frontend/src/components/UserFormModal.svelte` | Mostrar username en modo edit (M4) |
| `frontend/src/components/AdminHaciendas.svelte` | Manejo HTTP 409 (M1) |
| `frontend/src/components/AdminSuertes.svelte` | Manejo HTTP 409 (M2) |

### Archivos nuevos (tests)
| Archivo | Cubre |
|---------|-------|
| `frontend/src/components/__tests__/AdminUsers.test.js` | 6 tests carga + 4 tests paginación + 4 tests crear + 4 tests editar + 3 tests desactivar |
| `frontend/src/components/__tests__/UserFormModal.test.js` | 10 tests create mode + 8 tests edit mode |
| `frontend/src/components/__tests__/AdminHaciendas.test.js` | 4 tests carga + 3 tests crear + 1 test editar + 2 tests eliminar |
| `frontend/src/components/__tests__/HaciendaFormModal.test.js` | 10 tests create + edit mode |
| `frontend/src/components/__tests__/AdminSuertes.test.js` | 5 tests dropdown y carga + 2 tests crear + 1 test editar + 1 test eliminar |
| `frontend/src/components/__tests__/SuerteFormModal.test.js` | 8 tests create + 4 tests edit mode |
| `frontend/src/components/__tests__/ConfirmModal.test.js` | Tests componente genérico de confirmación |

## Decisiones técnicas

- **Array.isArray fallback**: AdminSuertes.svelte usa `Array.isArray(result) ? result : result.items` para manejar tanto formato array plano como `{items: [...]}` del backend (corrige Bug #20).
- **HTTP 409 sin cerrar modal**: En los 3 CRUDs, el error 409 (duplicado) asigna `formError` manteniendo el modal abierto para que el usuario corrija, sin cerrarlo automáticamente.
- **$state() runes Svelte 5**: Todos los componentes usan `$state()`, `$props()`, `$effect()` y `onMount` explícito. Sin `$:` (Svelte 4 legacy).
- **Paginación consistente**: AdminUsers usa el mismo patrón de paginación que AdminHaciendas y AdminSuertes (buildQuery, CONFIG, controles Anterior/Siguiente, selector page size 10/20/50/100).

## Verificación

- [x] `npx vitest run`: **121 tests, 9 archivos, TODOS VERDES** ✅
- [x] `npm run build`: **Build exitoso** (solo warnings a11y pre-existentes) ✅
- [x] `./harness/init.ps1`: Secciones 1-5 [OK]; Sección 6 timeout (Docker no disponible en Windows) ⚠️
- [x] Trazabilidad R1-R20 ↔ tests documentada en impl_frontend_admin_masterdata.md
- [x] Skills Svelte 5 consultados y seguidos
- [x] Reviewer APPROVED (review_frontend_admin_masterdata.md)
- [x] Impacto en features existentes: ninguno (frontend-only, archivos exclusivos de esta feature)

## GitHub Issue

- Issue creado: https://github.com/rojecas/sip_edge/issues/18
- Repo: rojecas/sip_edge
- Estado: CLOSED (completed)

## Lecciones / pitfalls

- La auditoría inicial encontró 6 hallazgos que requirieron corrección antes de aprobación. El spec original no fue actualizado tras la revisión de requirements, lo que causó que algunas features (paginación en AdminUsers) se implementaran inicialmente sin ella.
- El GitHub issue para feature 16 no se creó al transicionar a `in_progress` (error procedural del leader). Se creó retroactivamente al cerrar.
- `harness/scripts/github_sync.py` falla con archivos JSON que tienen BOM (Byte Order Mark). Los archivos creados con PowerShell `Out-File` o redirección `>` en Windows pueden tener BOM `\ufeff` que no es manejado por `json.load()` sin `encoding='utf-8-sig'`. Se usó `gh` CLI directo como workaround.

## Features dependientes

- Feature 17 (frontend_analytics) — depende de 16, actualmente `in_progress`
- Feature 18 (harvest_type) — depende de 6, 8, 13 (no de 16)

No hay bloqueos ni impactos en features dependientes.
