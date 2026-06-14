# Implementation — Weighing Capture (Feature 6)

## Trazabilidad

| Requirement | Test(s) |
|-------------|---------|
| R1 | `test_list_haciendas_as_operator` (test_weighings + test_haciendas) |
| R2 | `test_list_suertes_as_operator` (test_weighings + test_haciendas) |
| R3 | `test_create_weighing_as_operator` |
| R4 | `test_create_weighing_rs232_stub_import_error` |
| R5 | `test_create_weighing_as_operator` |
| R6 | `test_create_weighing_invalid_hacienda`, `test_create_weighing_invalid_suerte` |
| R7 | `test_create_weighing_rs232_stub_import_error` |
| R8 | `test_create_weighing_without_token` |
| R9 | `test_create_weighing_as_admin` |
| R10 | `test_list_weighings_operator_only_own` |
| R11 | `test_list_weighings_admin_sees_all` |
| R12 | `test_get_weighing_operator_own` |
| R13 | `test_get_weighing_admin_any` |
| R14 | `test_get_weighing_not_found` |
| R15 | `test_get_weighing_operator_other_404` |
| R16 | `test_reset_weighing_form`, `test_reset_weighing_form_admin` |
| R17 | `test_websocket_scale_with_valid_token` |
| R18 | `test_websocket_scale_with_valid_token` |
| R19 | `test_websocket_scale_without_token` |
| R20 | `test_create_weighing_negative_peso` |
| R21 | `test_create_weighing_as_operator` (verifies `fecha`/`hora` auto-set) |
| R22 | `test_create_weighing_as_operator` (verifies `usuario_id` auto-set) |
| R23 | `test_create_weighing_rs232_stub_import_error` |

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/models.py` | Anadido modelo ORM `Weighing` con todos los campos y FKs |
| `src/auth.py` | Anadido helper `require_any_role(*roles)` |
| `src/weighings.py` | **Nuevo.** Schemas Pydantic + endpoints CRUD + RS232 stub |
| `src/main.py` | Registrado `weighings_router`, anadido `scale_clients`, WebSocket `/ws/scale`, callback ScaleService, import `Weighing` |
| `src/haciendas.py` | Cambiados GET endpoints a `require_any_role("admin", "operator")` |
| `tests/test_haciendas.py` | Actualizados tests de operator GET para esperar 200 |
| `tests/test_weighings.py` | **Nuevo.** 21 tests para weighings CRUD, WebSocket, haciendas/suertes read |
| `database/migrations/2026_06_13_000003_create_weighings.py` | **Nuevo.** Migracion de tabla weighings |

## Tasks completadas

- [x] T1 — Modelo ORM `Weighing` en `src/models.py`
- [x] T2 — Schemas Pydantic en `src/weighings.py`
- [x] T3 — Helper `require_any_role` en `src/auth.py`
- [x] T4 — Endpoint `POST /api/weighings` con validacion y RS232 stub
- [x] T5 — Endpoint `GET /api/weighings` con filtro por rol
- [x] T6 — Endpoint `GET /api/weighings/{id}` con visibilidad segun rol
- [x] T7 — Endpoint `POST /api/weighings/reset`
- [x] T8 — Registro de `weighings_router` en `src/main.py`
- [x] T9 — Refactor de GET endpoints en haciendas/suertes para rol operator
- [x] T10 — WebSocket `/ws/scale` con autenticacion y callback ScaleService
- [x] T11 — Stub RS232 con try/except ImportError
- [x] T12 — `tests/test_weighings.py` con helper `_build_test_app`
- [x] T13 — Test: POST create weighing as operator
- [x] T14 — Test: POST con peso negativo → 422
- [x] T15 — Test: POST sin token → 401
- [x] T16 — Test: POST como admin funciona
- [x] T17 — Test: GET operator solo ve propios
- [x] T18 — Test: GET admin ve todos
- [x] T19 — Test: GET /{id} operator ve propio
- [x] T20 — Test: GET /{id} operator 404 para otro
- [x] T21 — Test: GET /{id} admin ve cualquiera
- [x] T22 — Test: GET /9999 → 404
- [x] T23 — Test: POST /reset → confirmacion
- [x] T24 — Test: RS232 stub → enviado_pc=False
- [x] T25 — Test: GET /api/haciendas como operator → 200
- [x] T26 — Test: GET /api/suertes como operator → 200
- [x] T27 — Test: WebSocket con token valido
- [x] T28 — Test: WebSocket sin token → 4001
- [x] T29 — Test: transaccion atomica (validacion FKs)
- [x] T30 — Trazabilidad documentada (este archivo)
- [x] T31 — `python -m unittest discover -s tests -v` — 195 tests OK
- [x] T32 — `./init.ps1` — bloques 1-5 OK
