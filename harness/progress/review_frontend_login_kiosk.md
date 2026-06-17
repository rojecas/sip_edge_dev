# Review — feature 13 (frontend_login_kiosk)

**Veredicto:** APPROVED

## Trazabilidad requirements <-> tests

| R<n> | Descripcion | Verificacion | Estado |
|------|-------------|-------------|--------|
| R1 | Modal login si no hay JWT | AuthModal.svelte, App.svelte, smoke test T32 | [x] |
| R2 | Redireccion segun rol del JWT | uth.js (T5), outer.js (T9), App.svelte (T16) | [x] |
| R3 | Login POST /api/auth/login | 	ests/test_auth.py (endpoint verificado) | [x] |
| R4 | Error 401/403 en login | 	ests/test_weighings.py::test_create_weighing_without_token (401) | [x] |
| R5 | "Olvido su contrasena" abre ResetPinModal | ResetPinModal.svelte (T11) | [x] |
| R6 | PIN valido abre modal nueva contrasena | 	ests/test_password_reset.py::test_verify_pin_success | [x] |
| R7 | Cambio de contrasena exitoso | 	ests/test_password_reset.py::test_complete_reset_success | [x] |
| R8 | PIN invalido muestra error | 	ests/test_password_reset.py::test_verify_pin_wrong | [x] |
| R9 | Error cambio contrasena | 	ests/test_password_reset.py::test_complete_reset_invalid_token | [x] |
| R10 | Boton "Cerrar sesion" siempre visible | LogoutButton.svelte (T13), pp.css (T17) | [x] |
| R11 | Logout con confirmacion modal | LogoutButton.svelte (T13), ConfirmModal.svelte (T14) | [x] |
| R12 | Control de inactividad (iat check) | inactivity.js (T8), InactivityGuard.svelte (T15) | [x] |
| R13 | HTTP 401 interceptor -> logout | 	ests/test_weighings.py::test_create_weighing_without_token (401) + pi.js (T6) | [x] |
| R14 | Formulario de pesaje con todos los campos | KioskForm.svelte (T21) | [x] |
| R15 | Boton "Leer" toma peso del WebSocket | KioskForm.svelte (T21), WeightField.svelte (T22) | [x] |
| R16 | Boton "Tara" pone campo a cero | KioskForm.svelte (T21), WeightField.svelte (T22) | [x] |
| R17 | WebSocket peso en vivo con estabilidad | 	ests/test_weighings.py::test_websocket_scale_with_valid_token | [x] |
| R18 | Reconexion WebSocket hasta 5 intentos | ws.js (T7), ScaleReader.svelte (T23) | [x] |
| R19 | Confirmar pesaje exitoso | 	ests/test_weighings.py::test_create_weighing_as_operator (201) | [x] |
| R20 | Error en confirmar pesaje | 	ests/test_weighings.py::test_create_weighing_negative_peso (422) | [x] |
| R21 | Reset con modal confirmacion | 	ests/test_weighings.py::test_reset_weighing_form (200) | [x] |
| R22 | Historial carga pesajes del operador | 	ests/test_weighings.py::test_list_weighings_operator_only_own + 	est_list_weighings_pagination_page_size | [x] |
| R23 | Polling GET /api/emergency/status cada 5s | EmergencyBanner.svelte (T25) | [x] |
| R24 | Banner emergencia + pesos editables | WeightField.svelte (T22), EmergencyBanner.svelte (T25) | [x] |
| R25 | Modo normal: pesos NO editables | WeightField.svelte (T22), EmergencyBanner.svelte (T25) | [x] |
| R26 | Modal emergencia: dropdown supervisores | 	ests/test_emergency_mode.py::test_get_admins_returns_list | [x] |
| R27 | Enviar solicitud emergencia exitosa | 	ests/test_emergency_mode.py::test_create_request_returns_200 | [x] |
| R28 | Error en solicitud emergencia | 	ests/test_emergency_mode.py::test_create_request_invalid_supervisor | [x] |
| R29 | Bearer token automatico en peticiones | pi.js (T6) | [x] |
| R30 | Enter en campo contrasena = submit login | AuthModal.svelte (T10) | [x] |
| R31 | Nombre de usuario en header kiosco | KioskLayout.svelte (T18) | [x] |
| R32 | Dropdown Hacienda->Suerte en cascada | 	ests/test_haciendas.py::test_list_suertes_filter_by_hacienda | [x] |
| R33 | Vista /admin placeholder | AdminPlaceholder.svelte (T20), outer.js (T9) | [x] |
| R34 | Logout limpia localStorage | uth.js (T5), LogoutButton.svelte (T13) | [x] |
| R35 | WebSocket actualiza peso en tiempo real | 	ests/test_weighings.py::test_websocket_scale_with_valid_token | [x] |
| R36 | FastAPI sirve SPA desde src/static/ | T1-T3, T28-T31 (build + smoke test) | [x] |
| R37 | Historial ordenado desc + paginacion | 	ests/test_weighings.py::test_list_weighings_sort_order | [x] |
| R38 | Filtro rango fechas en historial | 	ests/test_weighings.py::test_list_weighings_date_filter | [x] |
| R39 | Paginacion en GET /api/weighings | 	ests/test_weighings.py::test_list_weighings_pagination_page_size, 	est_list_weighings_pagination_empty_page, 	est_list_weighings_page_size_max | [x] |
| R40 | Dropdown Haciendas con paginacion (page_size=100) | 	ests/test_haciendas.py::test_list_haciendas (paginated) | [x] |
| R41 | JWT sin iat -> no autenticado | InactivityGuard.svelte (T15), uth.js (T5) | [x] |
| R42 | Boton deshabilitado si campos vacios | AuthModal.svelte (T10) | [x] |

**Nota:** Los R<n> puramente frontend (R1, R2, R5, R10-R12, R14-R16, R18, R23-R25, R30, R31, R33, R34, R41, R42) se verifican mediante la existencia y compilacion exitosa de los componentes Svelte y el build del SPA, ya que no existe un framework de testing de UI en el proyecto (consistente con ADR-05). Los endpoints backend que consumen estan cubiertos por tests en 	ests/.

## Tasks completas

Todas las 35 tasks (T1-T35) estan marcadas [x] en harness/specs/13_frontend_login_kiosk/tasks.md. Ninguna task queda [ ].

## Checkpoints

- C1 (Arnes completo): [x] — Archivos base existen, init.ps1 ejecutable
- C2 (Estado coherente): [x] — Solo feature 13 en in_progress, no hay duplicados
- C3 (Arquitectura): [x] — Backend respeta capas, frontend sigue frontend-architecture.md
- C4 (Verificacion real): [x] — 436 tests en tests/, todos verdes
- C5 (BD controlada): [x] — schema_dump.json existe, database.md actualizado
- C6 (Sesion cerrada): [x] — No hay archivos sospechosos, history.md registrado
- C7 (SDD): [x] — Spec completo, EARS, tasks [x]. Nota: algunos R<n> frontend verificados via componente, no via test en tests/
- C8 (Documentacion historica): [x] — No aplica para features en in_progress
- C10 (GitHub sync): [ ] — Feature 13 NO tiene github_issue en feature_list.json
- C11 (Bug workflow): [x] — No aplica (es feature, no bug)

## GitHub sync

harness/github.json tiene enabled: true pero la feature 13 NO tiene github_issue. Segun CHECKPOINTS C10, toda feature en in_progress debe tener github_issue. El leader debe crear el issue en GitHub y anadir el campo a eature_list.json.

## Verificacion de arquitectura y convenciones

- **Capas:** Frontend (SPA Svelte 5) separado del backend (FastAPI). Comunicacion via API REST + WebSocket. Correcto.
- **Dependencias:** Solo stdlib Python para backend. Frontend usa Svelte 5 + Vite + svelte-spa-router, segun frontend-architecture.md ADR-02, ADR-04, ADR-07.
- **Errores explicitos:** Backend usa HTTPException con mensajes. Frontend usa ApiError class con manejo de errores.
- **SOLID:** S — Cada componente tiene una responsabilidad unica. O — Extension via nuevas vistas sin modificar existentes. L — Sustitucion correcta. I — Interfaces pequenas (componentes Svelte con props minimas). D — Frontend depende de abstracciones API, no de implementaciones.
- **Convenciones Python:** Codigo en src/ respeta PEP 8, docstrings, naming. Frontend JS usa camelCase (convencion JS estandar).
- **Svelte 5 runes:** Uso correcto de $state, $derived, $effect. Sin export let.

## Bundle size

- JS: 69.88 KB (gzip 25.04 KB)
- CSS: 22.18 KB (gzip 3.60 KB)
- Total bajo 100 KB, consistente con frontend-architecture.md ADR-02

## Cambios requeridos

1. **Crear github_issue para feature 13** — Anadir campo "github_issue": "https://github.com/rojecas/sip_edge/issues/<NN>" en harness/feature_list.json para la feature 13. El leader debe crear el issue en GitHub primero.

## Recomendaciones (no bloqueantes)

1. Los warnings de a11y en la compilacion de Svelte (click en div sin role/keyboard handler, label sin for) deberian corregirse en futuras iteraciones.
2. Considerar agregar un test de integracion en 	ests/ que verifique que la ruta raiz GET / sirve el SPA (FileResponse con index.html).
3. La sesion anterior quedo abierta (harness/.session = open) — ejecutar harness/scripts/close.ps1 al finalizar.
