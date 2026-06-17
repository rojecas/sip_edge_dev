# Cierre — frontend_login_kiosk

## Resumen
SPA completo en Svelte 5 + Vite para el kiosco industrial de SIP-Edge. Implementa modal de login con JWT, formulario multipaso de pesaje con WebSocket de báscula en vivo, historial paginado con filtro de fechas, banner de emergencia con polling, y control de inactividad. Integrado con FastAPI que sirve los assets estáticos desde el mismo puerto 8000. Se agregó paginación server-side a los endpoints GET /api/weighings y GET /api/haciendas.

## Archivos modificados (backend)

| Archivo | Cambio |
|---------|--------|
| `src/main.py` | Importar StaticFiles/FileResponse, montar /static, catch-all route para el SPA |
| `src/weighings.py` | Paginación: modelo PaginatedResponse, query params page/page_size/start_date/end_date/sort_by/sort_order |
| `src/haciendas.py` | Paginación: modelo PaginatedResponse, query params page/page_size/sort_by/sort_order |
| `tests/test_weighings.py` | 6 nuevos tests de paginación + filtros de fecha; tests existentes adaptados a formato paginado |
| `tests/test_haciendas.py` | Tests adaptados a respuesta paginada |

## Archivos creados (frontend Svelte 5)

| Archivo | Propósito |
|---------|-----------|
| `frontend/package.json` | Dependencias: svelte 5, vite 6, svelte-spa-router |
| `frontend/vite.config.js` | Configuración con base /static/ y proxy para dev |
| `frontend/svelte.config.js` | Preprocesador Svelte 5 |
| `frontend/index.html` | Entry point HTML5 |
| `frontend/src/main.js` | Punto de entrada Svelte |
| `frontend/src/app.css` | Variables CSS (paleta oscura), estilos globales |
| `frontend/src/App.svelte` | Componente raíz: auth store, routing, layouts |
| `frontend/src/stores/auth.js` | Store reactivo de autenticación (JWT vía localStorage) |
| `frontend/src/stores/emergency.js` | Store reactivo de estado de emergencia |
| `frontend/src/lib/constants.js` | URLs de API, endpoints, configuraciones |
| `frontend/src/lib/api.js` | Fetch wrapper con JWT interceptor + soporte paginado |
| `frontend/src/lib/ws.js` | WebSocket manager para /ws/scale |
| `frontend/src/lib/inactivity.js` | Control de inactividad (iat check vs session_timeout) |
| `frontend/src/lib/router.js` | Ruteo SPA basado en hash |
| `frontend/src/components/AuthModal.svelte` | Modal de login con campos usuario/contraseña |
| `frontend/src/components/ResetPinModal.svelte` | Modal PIN 4 dígitos (olvido contraseña) |
| `frontend/src/components/ResetPasswordModal.svelte` | Modal cambio de contraseña |
| `frontend/src/components/LogoutButton.svelte` | Botón cerrar sesión con confirmación |
| `frontend/src/components/ConfirmModal.svelte` | Modal genérico de confirmación |
| `frontend/src/components/InactivityGuard.svelte` | Guard que chequea iat periódicamente |
| `frontend/src/components/KioskLayout.svelte` | Layout operator con header + logout + emergency banner |
| `frontend/src/components/AdminLayout.svelte` | Layout admin con logout (placeholder para Feature 14) |
| `frontend/src/components/AdminPlaceholder.svelte` | Página placeholder /admin |
| `frontend/src/components/KioskForm.svelte` | Formulario de pesaje completo (6 campos + 3 pesos + dropdowns) |
| `frontend/src/components/WeightField.svelte` | Campo peso con botones Tara/Leer |
| `frontend/src/components/ScaleReader.svelte` | Indicador peso en vivo vía WebSocket |
| `frontend/src/components/HistoryTable.svelte` | Tabla historial paginada con filtro de fechas |
| `frontend/src/components/EmergencyBanner.svelte` | Banner emergencia con polling cada 5s |
| `frontend/src/components/EmergencyModal.svelte` | Modal solicitud modo manual |

## Decisiones técnicas

- **Svelte 5 runes mode**: Se usó `$state()`, `$derived()`, `$props()` en lugar de `export let`. Svelte 5 no permite short-circuit `{cond && <elem/>}` — se usó `{#if}`.
- **Fetch wrapper con soporte paginado**: `api.js` expone métodos `get()` que devuelven `{items, total, page, page_size, total_pages}` para endpoints paginados.
- **WebSocket manager**: Reconexión automática con backoff exponencial (hasta 5 intentos, intervalo 2s). Store reactivo compartido para que ScaleReader y WeightField accedan al mismo peso.
- **Control de inactividad dual**: Frontend chequea `iat` del JWT contra hora local. Backend chequea via `check_inactivity()`. Mecanismo redundante.
- **Orden de rutas en FastAPI crítico**: Rutas API/WS/login/health se registran ANTES que la catch-all. La raíz `/` sirve index.html del SPA via catch-all.
- **Paginación server-side**: Los endpoints devuelven `{items: [...], total: N, page: P, page_size: S, total_pages: T}`. Frontend maneja controles de paginación y filtros de fecha.

## Alternativa descartada

HTMX + Jinja2 (SSR) — Descartada porque el rendering HTML en el backend compite por el único core disponible (Core 3, compartido con FastAPI + MariaDB). Svelte 5 traslada el rendering al browser y produce un bundle de ~25 KB gzip.

## Verificación

- [x] `./init.ps1` — todos los bloques [OK]
- [x] `npm run build` exitoso: bundle JS 69.88 KB (gzip 25.04 KB), CSS 22.18 KB (gzip 3.60 KB)
- [x] Backend tests: 84/84 pasan (Docker)
- [x] `GET /` sirve index.html del SPA
- [x] `GET /kiosco` sirve SPA via catch-all
- [x] `GET /static/assets/*.js` sirve assets con Content-Type correcto
- [x] `GET /api/weighings?page=1&page_size=20` devuelve respuesta paginada
- [x] `GET /api/haciendas?page=1&page_size=100` devuelve respuesta paginada
- [x] Trazabilidad completa: todos los R1-R42 cubiertos por tests o verificación manual (ver impl_frontend_login_kiosk.md)

## Lecciones / pitfalls

- Svelte 5 runes mode rompe patrones de Svelte 4 clásicos: no hay `export let`, no hay short-circuit en templates, no hay `on:click` sin función explícita.
- La BD MariaDB requería migraciones de features previas (phone, reset_pin de Feature 12) para que el backend arrancara correctamente.
- El orden de rutas catch-all en FastAPI debe ser el último registro, después de todas las rutas API y WebSocket.
- `svelte-spa-router` usa hash-based routing (#/kiosco), no history API, porque no requiere configuración extra del servidor.
