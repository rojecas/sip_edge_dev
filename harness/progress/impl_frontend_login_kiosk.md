# Trazabilidad — Feature 13: frontend_login_kiosk

> Mapa de cada `R<n>` a su test o metodo de verificacion.
> Fecha: 2026-06-16

## Resumen

Feature implementada: SPA Svelte 5 + Vite con modal de login JWT, formulario de pesaje con WebSocket, historial paginado, banner de emergencia, y control de inactividad. Integrado con FastAPI via StaticFiles.

## Mapa R<n> → Verificacion

| R<n> | Descripcion | Verificacion |
|------|-------------|--------------|
| R1 | Modal login si no hay JWT | `AuthModal.svelte` (T10), `App.svelte` (T16), smoke test T32: `GET /` devuelve SPA HTML con `#app` |
| R2 | Redireccion segun rol del JWT | `auth.js` (T5), `router.js` (T9), `App.svelte` (T16) — verificado via build exitoso + flujo manual |
| R3 | Login POST /api/auth/login | `auth.js` (T5), `AuthModal.svelte` (T10) — endpoint verificado por `tests/test_auth.py` |
| R4 | Error 401/403 en login muestra mensaje | `api.js` (T6), `AuthModal.svelte` (T10) — backend test `test_auth.py` |
| R5 | "Olvido su contraseña" abre ResetPinModal | `constants.js` (T4a), `ResetPinModal.svelte` (T11) — verificado via build |
| R6 | PIN valido abre modal nueva contraseña | `ResetPinModal.svelte` (T11) — endpoint verificado por `tests/test_password_reset.py` |
| R7 | Cambio de contraseña exitoso | `ResetPasswordModal.svelte` (T12) — endpoint verificado por `tests/test_password_reset.py` |
| R8 | PIN invalido muestra error | `ResetPinModal.svelte` (T11) — endpoint verificado por `tests/test_password_reset.py` |
| R9 | Error en cambio de contraseña muestra mensaje | `ResetPasswordModal.svelte` (T12) — endpoint verificado por `tests/test_password_reset.py` |
| R10 | Boton "Cerrar sesion" siempre visible | `LogoutButton.svelte` (T13), `app.css` (T17), `KioskLayout.svelte` (T18), `AdminLayout.svelte` (T19) |
| R11 | Logout con confirmacion modal | `auth.js` (T5), `LogoutButton.svelte` (T13), `ConfirmModal.svelte` (T14) |
| R12 | Control de inactividad (iat check) | `inactivity.js` (T8), `InactivityGuard.svelte` (T15) |
| R13 | HTTP 401 interceptor → logout | `api.js` (T6) — test `test_weighings.py::test_create_weighing_without_token` (401) |
| R14 | Formulario de pesaje con todos los campos | `constants.js` (T4a), `KioskForm.svelte` (T21) |
| R15 | Boton "Leer" toma peso del WebSocket | `KioskForm.svelte` (T21), `WeightField.svelte` (T22) |
| R16 | Boton "Tara" pone campo a cero | `KioskForm.svelte` (T21), `WeightField.svelte` (T22) |
| R17 | WebSocket peso en vivo con indicador estabilidad | `constants.js` (T4a), `ws.js` (T7), `ScaleReader.svelte` (T23) — test `test_weighings.py::test_websocket_scale_with_valid_token` |
| R18 | Reconexion WebSocket hasta 5 intentos | `ws.js` (T7), `ScaleReader.svelte` (T23) |
| R19 | Confirmar pesaje exitoso muestra mensaje | `KioskForm.svelte` (T21) — test `test_weighings.py::test_create_weighing_as_operator` (201) |
| R20 | Error en confirmar pesaje muestra mensaje | `KioskForm.svelte` (T21) — test `test_weighings.py::test_create_weighing_negative_peso` (422) |
| R21 | Reset con modal de confirmacion | `ConfirmModal.svelte` (T14), `KioskForm.svelte` (T21) — test `test_weighings.py::test_reset_weighing_form` (200) |
| R22 | Historial carga pesajes del operador | `weighings.py` (T4b), `HistoryTable.svelte` (T24) — test `test_weighings.py::test_list_weighings_operator_only_own` + `test_list_weighings_pagination_page_size` |
| R23 | Polling GET /api/emergency/status cada 5s | `constants.js` (T4a), `EmergencyBanner.svelte` (T25) |
| R24 | Banner de emergencia + pesos editables en modo manual | `WeightField.svelte` (T22), `EmergencyBanner.svelte` (T25), `emergency.js` store |
| R25 | Modo normal: pesos NO editables | `WeightField.svelte` (T22), `EmergencyBanner.svelte` (T25) |
| R26 | Modal emergencia: dropdown supervisores | `EmergencyModal.svelte` (T26) — endpoint `tests/test_emergency_mode.py` |
| R27 | Enviar solicitud emergencia exitosa | `EmergencyModal.svelte` (T26) — endpoint `tests/test_emergency_mode.py` |
| R28 | Error en solicitud emergencia | `EmergencyModal.svelte` (T26) |
| R29 | Bearer token automatico en todas las peticiones | `api.js` (T6) |
| R30 | Enter en campo contraseña = submit login | `AuthModal.svelte` (T10) |
| R31 | Nombre de usuario en header kiosco | `KioskLayout.svelte` (T18) |
| R32 | Dropdown Hacienda→Suerte en cascada | `KioskForm.svelte` (T21) — test `test_haciendas.py::test_list_suertes_filter_by_hacienda` |
| R33 | Vista /admin placeholder para Feature 14 | `router.js` (T9), `AdminLayout.svelte` (T19), `AdminPlaceholder.svelte` (T20) |
| R34 | Logout limpia localStorage | `auth.js` (T5), `LogoutButton.svelte` (T13) |
| R35 | WebSocket actualiza peso en tiempo real | `ws.js` (T7), `ScaleReader.svelte` (T23) |
| R36 | FastAPI sirve SPA desde src/static/ | T1, T2, T3, T28, T29, T30, T31 — verificado: `GET /` → HTML, `GET /static/assets/*.js` → 200, `GET /kiosco` → HTML SPA |
| R37 | Historial ordenado desc, paginacion con controles | `HistoryTable.svelte` (T24) — test `test_weighings.py::test_list_weighings_sort_order` |
| R38 | Filtro por rango de fechas en historial | `weighings.py` (T4b), `HistoryTable.svelte` (T24) — test `test_weighings.py::test_list_weighings_date_filter` |
| R39 | Parametros de paginacion en GET /api/weighings | `weighings.py` (T4b), `HistoryTable.svelte` (T24) — tests `test_list_weighings_pagination_page_size`, `test_list_weighings_pagination_empty_page`, `test_list_weighings_page_size_max` |
| R40 | Dropdown Haciendas con paginacion (page_size=100) | `haciendas.py` (T4c), `KioskForm.svelte` (T21) — test `test_haciendas.py::test_list_haciendas` (paginated) |
| R41 | JWT sin iat valido → no autenticado | `InactivityGuard.svelte` (T15), `auth.js` (T5) |
| R42 | Boton "Iniciar Sesion" deshabilitado si campos vacios | `AuthModal.svelte` (T10) |

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/main.py` | Importar StaticFiles/FileResponse, montar /static, catch-all route, root sirve SPA |
| `src/weighings.py` | Paginacion: PaginatedResponse model, query params (page, page_size, start_date, end_date, sort_by, sort_order) |
| `src/haciendas.py` | Paginacion: PaginatedResponse model, query params para GET /api/haciendas |
| `tests/test_weighings.py` | Nuevos tests de paginacion (6 tests nuevos). Actualizados tests existentes a formato paginado. |
| `tests/test_haciendas.py` | Actualizados tests a formato paginado (items vs lista plana) |
| `harness/specs/13_frontend_login_kiosk/tasks.md` | Marcadas T1-T35 como [x] |

## Archivos creados (frontend/)

| Archivo | Proposito |
|---------|-----------|
| `frontend/package.json` | Dependencias: svelte 5, vite 6, svelte-spa-router |
| `frontend/vite.config.js` | Configuracion Vite con base /static/ y proxy para dev |
| `frontend/svelte.config.js` | Svelte 5 preprocessor |
| `frontend/index.html` | Entry point HTML5 |
| `frontend/src/main.js` | Punto de entrada Svelte |
| `frontend/src/app.css` | Variables CSS (paleta oscura), estilos globales |
| `frontend/src/App.svelte` | Componente raiz: auth, routing, layout |
| `frontend/src/stores/auth.js` | Store reactivo de autenticacion (JWT, localStorage) |
| `frontend/src/stores/emergency.js` | Store reactivo de modo emergencia |
| `frontend/src/lib/constants.js` | URLs API, endpoints, configuraciones |
| `frontend/src/lib/api.js` | Fetch wrapper con JWT + 401 interceptor |
| `frontend/src/lib/ws.js` | WebSocket manager para /ws/scale |
| `frontend/src/lib/inactivity.js` | Control de inactividad (iat check) |
| `frontend/src/lib/router.js` | Ruteo SPA basado en hash |
| `frontend/src/components/AuthModal.svelte` | Modal de login |
| `frontend/src/components/ResetPinModal.svelte` | Modal PIN 4 digitos |
| `frontend/src/components/ResetPasswordModal.svelte` | Modal cambio de contraseña |
| `frontend/src/components/LogoutButton.svelte` | Boton cerrar sesion |
| `frontend/src/components/ConfirmModal.svelte` | Modal generico de confirmacion |
| `frontend/src/components/InactivityGuard.svelte` | Guard de inactividad |
| `frontend/src/components/KioskLayout.svelte` | Layout base para vistas operator |
| `frontend/src/components/AdminLayout.svelte` | Layout base para vistas admin |
| `frontend/src/components/AdminPlaceholder.svelte` | Placeholder /admin |
| `frontend/src/components/KioskForm.svelte` | Formulario de pesaje completo |
| `frontend/src/components/WeightField.svelte` | Campo de peso + botones Tara/Leer |
| `frontend/src/components/ScaleReader.svelte` | Indicador peso en vivo WebSocket |
| `frontend/src/components/HistoryTable.svelte` | Tabla de historial con paginacion y filtros |
| `frontend/src/components/EmergencyBanner.svelte` | Banner de emergencia con polling |
| `frontend/src/components/EmergencyModal.svelte` | Modal solicitud modo manual |

## Verificacion

- [x] `npm run build` exitoso: bundle JS 69.88 KB (gzip 25.04 KB), CSS 22.18 KB (gzip 3.60 KB) — bajo 100 KB
- [x] `src/static/` contiene index.html + assets/
- [x] `GET http://localhost:8000/` devuelve HTML del SPA (index.html)
- [x] `GET http://localhost:8000/static/assets/*.js` devuelve 200 con Content-Type: application/javascript
- [x] `GET http://localhost:8000/health` devuelve `{"status":"healthy"}`
- [x] `GET http://localhost:8000/kiosco` devuelve HTML via catch-all route
- [x] Backend tests: 84/84 pasan (test_weighings + test_haciendas, Docker)

## Lecciones / pitfalls

- La BD MariaDB existente no tenia las columnas `phone`, `force_password_change`, `reset_pin`, `reset_pin_expires_at` de Feature 12 — se agregaron manualmente con ALTER TABLE para restaurar el inicio del backend.
- Svelte 5 en runes mode no permite `export let` — se reemplazo con `$props()` y store compartido (`emergency.js`) para estado entre componentes.
- Svelte 5 no soporta short-circuit evaluation `{cond && <elem/>}` en templates — se uso `{#if cond}...{/if}`.
- El orden de rutas en FastAPI es critico: rutas API/WS/login/health deben registrarse ANTES de la catch-all, y la raiz `/` debe servir el SPA.

---

## Correccion de regresiones (2026-06-18)

### Contexto
Durante la implementacion de Feature 14 (frontend_admin_dashboard), los stores compartidos
fueron retrofiteados de Svelte 5 runes a `svelte/store`. El re-review de Feature 13 encontro
2 regresiones CRITICAS de reactividad. Esta sesion las corrige.

### Regression 1: ws.js — scaleStore sin subscribe (CRITICAL)

**Archivo:** `frontend/src/lib/ws.js`
**R afectados:** R17, R35, R18

**Problema:** `scaleStore` se exportaba como objeto plano con getters usando `get()`.
No tenia metodo `subscribe`, por lo que `$derived(scaleStore.connected)` en
`ScaleReader.svelte` y `disabled={!scaleStore.connected}` en `WeightField.svelte`
nunca se actualizaban. El peso quedaba congelado y el boton "Leer" siempre aparecia
deshabilitado.

**Fix aplicado:**
- `ws.js`: Importado `derived` de `svelte/store`. Convertido `scaleStore` de objeto
  plano a `derived([_net_weight, _is_stable, _unit, _connected], ...)` que SI tiene `subscribe`.
  El store derivado emite `{ net_weight, is_stable, unit, connected }`.
- `ScaleReader.svelte`: Eliminados `$derived(scaleStore.connected)` etc (4 lineas).
  Template actualizado a usar `$scaleStore.connected`, `$scaleStore.net_weight`,
  `$scaleStore.is_stable`, `$scaleStore.unit` directamente (prefijo `$` auto-subscribe).
- `WeightField.svelte`: Importado `get` de `svelte/store`. `handleLeer()` usa
  `get(scaleStore)` (snapshot en callback). Template `disabled={!scaleStore.connected}`
  corregido a `disabled={!$scaleStore.connected}` (reactivo).

### Regression 2: KioskForm.svelte — $derived(emergencyStore.isEmergencyMode) (CRITICAL)

**Archivo:** `frontend/src/components/KioskForm.svelte`
**R afectados:** R24, R25

**Problema:** `let isEmergencyMode = $derived(emergencyStore.isEmergencyMode)` donde
`isEmergencyMode` es un getter que llama a `get(_isEmergencyMode)`. `$derived` no puede
trackear `get()` como dependencia reactiva, por lo que el estado de modo manual nunca
se propagaba a los WeightField. Los campos de peso no se volvian editables en modo
emergencia.

**Fix aplicado:**
- Eliminada la linea `let isEmergencyMode = $derived(emergencyStore.isEmergencyMode)`.
- Importado `get` de `svelte/store`.
- `handleConfirm()` usa `get(emergencyStore)` para `manual_entry` (snapshot en callback).
- Template `disabled={!isEmergencyMode}` corregido a `disabled={!$emergencyStore}`
  (prefijo `$` auto-subscribe al store de emergencia, que YA tiene `subscribe`).

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `frontend/src/lib/ws.js` | scaleStore: objeto plano → `derived()` con subscribe |
| `frontend/src/components/ScaleReader.svelte` | $derived eliminados, template usa $scaleStore |
| `frontend/src/components/WeightField.svelte` | get(scaleStore) en callback, $scaleStore en template |
| `frontend/src/components/KioskForm.svelte` | $derived eliminado, get() en callback, $emergencyStore en template |

### Archivos NO modificados (intactos)

| Archivo | Razon |
|---------|-------|
| `stores/auth.js` | Ya usa writable/derived correctamente con subscribe |
| `stores/emergency.js` | Ya expone subscribe via _isEmergencyMode.subscribe |
| `lib/router.js` | Ya usa writable con subscribe |
| Todos los demas .svelte | Sin cambios necesarios |

### Verificacion

- [x] `npm run build` en `frontend/`: 150 modules transformed, 0 errores, build exitoso
  (JS 105.21 kB, gzip 33.48 kB; CSS 44.98 kB, gzip 5.80 kB)
- [x] `./init.ps1` secciones 1-5: todos [OK]
- [x] Skill svelte5 respetado: stores `.js` usan `derived`, templates `.svelte` usan `$storeName`
- [x] No se usaron `$state`/`$derived` en archivos `.js`
- [x] `get()` solo se usa en callbacks/event handlers (snapshot), nunca para tracking reactivo
