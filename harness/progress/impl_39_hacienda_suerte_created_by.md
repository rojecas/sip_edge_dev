# Implementación — Feature 39: hacienda_suerte_created_by

## Resumen

Implementación completada de la feature de trazabilidad que registra el usuario
creador en las tablas `haciendas` y `suertes`.

## Archivos modificados/creados

| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `database/migrations/2026_07_19_000001_add_created_by_to_haciendas.py` | Nuevo | Migración: ALTER TABLE haciendas ADD created_by FK |
| `database/migrations/2026_07_19_000002_add_created_by_to_suertes.py` | Nuevo | Migración: ALTER TABLE suertes ADD created_by FK |
| `src/models.py` | Modificado | Agregado `created_by` + relación `creator` en Hacienda y Suerte |
| `src/haciendas.py` | Modificado | Schemas + `_to_response` + `create_*` + routers |
| `frontend/src/components/AdminHaciendas.svelte` | Modificado | Columna "Creado por" en tabla |
| `frontend/src/components/AdminSuertes.svelte` | Modificado | Columna "Creado por" en tabla |
| `src/static/` | Actualizado | Bundle frontend recompilado |
| `tests/test_haciendas.py` | Modificado | 8 nuevos tests en clase `TestCreatedBy` |

## Impacto en features existentes

### Feature 4 — farm_lot_crud
- Modelos Hacienda y Suerte modificados: nueva columna `created_by` (nullable, no rompe compatibilidad).
- Schemas HaciendaResponse y SuerteResponse ampliados con campos opcionales.
- Funciones `create_hacienda` y `create_suerte` cambian firma (nuevo parámetro `user_id`).
  Compatibilidad hacia atrás mantenida: son funciones internas del módulo.

### Feature 38 — operator_hacienda_suerte_crud
- AdminHaciendas.svelte y AdminSuertes.svelte: nueva columna "Creado por".
  Compatible: solo muestra campo adicional, no cambia interfaz de componentes.

## Trazabilidad

| Requirement | Test |
|-------------|------|
| R1 | T1 (migración creada) |
| R2 | T2 (migración creada) |
| R3 | `test_create_hacienda_sets_created_by`, `test_create_hacienda_as_operator_sets_created_by` |
| R4 | `test_create_suerte_sets_created_by` |
| R5 | `test_create_hacienda_sets_created_by`, `test_list_haciendas_includes_created_by` |
| R6 | `test_create_suerte_sets_created_by`, `test_list_suertes_includes_created_by` |
| R7 | T13 (columna en AdminHaciendas.svelte) |
| R8 | T14 (columna en AdminSuertes.svelte) |
| R9 | `test_existing_records_have_null_created_by` |
| R10 | `test_create_hacienda_without_token_still_returns_401`, `test_create_suerte_without_token_still_returns_401` (también cubierto por `TestHaciendasAuth.test_create_hacienda_without_token`) |

## Verificación

- [x] Todos los tests pasan: `docker compose exec backend python -m unittest tests.test_haciendas -v` → 65 tests OK
- [x] Frontend compilado y copiado a `src/static/` con estructura `assets/` preservada
- [x] `tasks.md` con todos los checkboxes marcados
- [x] `init.ps1` ejecutado

## Skills consultados
- **svelte5** — Cargado desde `.opencode/skills/svelte5/SKILL.md`. Aplicado para:
  `$props()` (prop `allowDelete` en AdminHaciendas/AdminSuertes), `{#each}` (renderizado de filas con nueva columna "Creado por"), `{#if}` (fallback `|| "—"` cuando created_by_username es null).
