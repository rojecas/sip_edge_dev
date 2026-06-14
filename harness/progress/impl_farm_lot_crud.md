# Implementation — farm_lot_crud (id: 4)

## Traceability Map

### Requirements coverage

| Requirement | Test(s) |
|-------------|---------|
| R1 | `test_list_haciendas`, `test_list_haciendas_excludes_deleted` |
| R2 | `test_create_hacienda` |
| R3 | `test_get_hacienda` |
| R4 | `test_get_hacienda_not_found`, `test_get_hacienda_soft_deleted` |
| R5 | `test_update_hacienda` |
| R6 | `test_update_hacienda_not_found`, `test_update_hacienda_soft_deleted` |
| R7 | `test_soft_delete_hacienda`, `test_list_haciendas_excludes_deleted` |
| R8 | `test_soft_delete_hacienda_not_found`, `test_soft_delete_hacienda_already_deleted` |
| R9 | `test_create_hacienda_duplicate_codigo`, `test_update_hacienda_duplicate_codigo` |
| R10 | `test_list_suertes`, `test_list_suertes_excludes_deleted` |
| R11 | `test_list_suertes_filter_by_hacienda` |
| R12 | `test_create_suerte` |
| R13 | `test_create_suerte_invalid_hacienda`, `test_create_suerte_deleted_hacienda` |
| R14 | `test_get_suerte` |
| R15 | `test_get_suerte_not_found`, `test_get_suerte_soft_deleted` |
| R16 | `test_update_suerte` |
| R17 | `test_update_suerte_not_found`, `test_update_suerte_soft_deleted` |
| R18 | `test_soft_delete_suerte`, `test_list_suertes_excludes_deleted` |
| R19 | `test_soft_delete_suerte_not_found`, `test_soft_delete_suerte_already_deleted` |
| R20 | `test_create_suerte_duplicate_codigo`, `test_create_suerte_same_codigo_different_hacienda` |
| R21 | All `*_without_token` tests (20 tests) |
| R22 | All `*_as_operator` tests (10 tests) |
| R23 | `test_hacienda_response_fields` |
| R24 | `test_suerte_response_fields` |

## Files created/modified

| File | Action |
|------|--------|
| `src/models.py` | Modified — added `Hacienda` and `Suerte` ORM models |
| `src/haciendas.py` | Created — Pydantic schemas, CRUD functions, routers |
| `src/main.py` | Modified — registered `haciendas_router` and `suertes_router` |
| `database/migrations/2026_06_13_000001_create_haciendas.py` | Created |
| `database/migrations/2026_06_13_000002_create_suertes.py` | Created |
| `tests/test_haciendas.py` | Created — 144 total tests across 3 test classes |

## Verification

- `python -m unittest discover -s tests -v` — Ran 144 tests, OK (137.594s)
- `./init.ps1` — All blocks `[OK]` (steps 1–5)
