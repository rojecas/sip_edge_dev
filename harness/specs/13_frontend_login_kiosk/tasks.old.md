# Tasks — Frontend: Login, Kiosco de Pesaje y Logout

> Marcar `[x]` al completar. Cada task referencia al menos un `R<n>`.

---

## Fase 1 — Scaffold e integracion con FastAPI

- [x] T1 — Crear proyecto Svelte 5 + Vite en `frontend/`: `npm create vite@latest frontend -- --template svelte`, instalar dependencias, verificar que `npm run build` produce `frontend/dist/`. Cubre: R36.

- [x] T2 — Configurar `vite.config.js` con `base: '/static/'` para que los assets compilados apunten a la ruta `/static/` correcta. Crear `svelte.config.js` si no existe. Cubre: R36.

- [x] T3 — Modificar `src/main.py` para:
  - Importar `StaticFiles` de `fastapi.staticfiles` y `FileResponse` + `JSONResponse`
  - Montar `StaticFiles` en `/static` apuntando a `src/static/`
  - Anadir catch-all route `GET /{full_path:path}` que sirva `src/static/index.html` para rutas no-API/WS/login/health
  - Mantener orden correcto de rutas
  Cubre: R36.

- [x] T4a — Crear `frontend/src/lib/constants.js` con URLs de API, endpoints, y configuraciones (session timeout default 30 min, WS reconnect attempts 5, polling interval 5000ms). Cubre: R1, R5, R14, R17, R23.

---

## Fase 1b — Modificaciones al backend para paginacion

- [x] T4b — Modificar `src/weighings.py` endpoint `GET /api/weighings` para aceptar parametros `page`, `page_size`, `start_date`, `end_date`, `sort_by`, `sort_order`. Retornar formato paginado `{items, total, page, page_size, total_pages}`. Cubre: R22, R38, R39.

- [x] T4c — Modificar `src/haciendas.py` endpoint `GET /api/haciendas` para aceptar parametros `page`, `page_size`, `sort_by`, `sort_order`. Retornar formato paginado `{items, total, page, page_size, total_pages}`. Cubre: R40.

- [x] T4d — Actualizar tests existentes en `tests/` para cubrir los nuevos parametros de paginacion y filtros de fecha. Cubre: verificacion Nivel 1.

---

## Fase 2 — Store de autenticacion y fetch wrapper

- [x] T5 — Crear `frontend/src/stores/auth.js` con store reactivo Svelte 5 (`$state`):
  - `token`, `role`, `username` desde localStorage al iniciar
  - `login(token, role)` — guarda en localStorage y actualiza store
  - `logout()` — elimina de localStorage, limpia store, llama a ws.disconnect()
  - `isAuthenticated()` — getter derivado
  Cubre: R1, R2, R3, R11, R34.

- [x] T6 — Crear `frontend/src/lib/api.js` con fetch wrapper:
  - `api.get(url)`, `api.post(url, body)`, `api.put(url, body)`, `api.del(url)`
  - Agrega `Authorization: Bearer <token>` desde auth store
  - Intercepta HTTP 401 → llama `auth.logout()` y redirige a login
  - Parseo automatico de JSON
  - Manejo de errores con mensaje del backend
  - Soporte para respuestas paginadas: exponer metodos para obtener `items`, `total`, `page`, `total_pages`
  Cubre: R4, R13, R29.

- [x] T7 — Crear `frontend/src/lib/ws.js` con WebSocket manager para `/ws/scale`:
  - `ws.connect(token)` — conecta al WebSocket con token
  - Store reactivo `scaleStore` con `{net_weight, is_stable, unit, connected}`
  - Reconexion automatica hasta 5 intentos con intervalo 2s
  - `ws.disconnect()` — cierra conexion
  Cubre: R17, R18, R35.

- [x] T8 — Crear `frontend/src/lib/inactivity.js`:
  - Funcion `checkInactivity(jwtPayload, sessionTimeoutMinutes)` que compara `iat` vs tiempo actual
  - Si expirado → llama `auth.logout()` con mensaje "Sesion expirada por inactividad"
  - Timer que ejecuta chequeo cada 60 segundos
  Cubre: R12.

- [x] T9 — Crear `frontend/src/lib/router.js` con ruteo SPA:
  - `/kiosco` → componente KioskForm (rol operator)
  - `/kiosco/historial` → componente HistoryTable (rol operator)
  - `/admin` → componente AdminPlaceholder (rol admin)
  - Redireccion automatica segun autenticacion y rol
  Cubre: R2, R33.

---

## Fase 3 — Componentes de autenticacion (modales login + reset)

- [x] T10 — Crear `frontend/src/components/AuthModal.svelte`:
  - Modal centrado con campos Usuario + Contrasena
  - Boton "Iniciar Sesion" (deshabilitado si campos vacios)
  - Submit via Enter en campo contrasena
  - Llamada a `POST /api/auth/login`
  - Manejo de errores (401/403) con mensaje en pantalla
  - Enlace "Olvido su contrasena" que abre ResetPinModal
  - Exito → guardar token + rol + username → redirigir segun rol
  Cubre: R1, R3, R4, R30, R42.

- [x] T11 — Crear `frontend/src/components/ResetPinModal.svelte`:
  - Modal con campo Usuario + campo PIN (4 digitos, inputmode numeric, maxlength 4)
  - Boton "Verificar PIN"
  - Llamada a `POST /api/auth/verify-reset-pin`
  - Exito → cerrar este modal, abrir ResetPasswordModal con reset_token
  - Error → mostrar mensaje en modal
  Cubre: R5, R6, R8.

- [x] T12 — Crear `frontend/src/components/ResetPasswordModal.svelte`:
  - Modal con campos Nueva Contrasena + Confirmar Contrasena
  - Boton "Cambiar Contrasena"
  - Llamada a `POST /api/auth/complete-reset`
  - Exito → mensaje de exito, cerrar tras 2s, mostrar modal login
  - Error → mostrar mensaje en modal
  Cubre: R7, R9.

- [x] T13 — Crear `frontend/src/components/LogoutButton.svelte`:
  - Boton fijo en esquina superior derecha con texto "Cerrar sesion"
  - Al hacer clic → mostrar modal de confirmacion (ConfirmModal)
  - Confirmar → `auth.logout()` + recargar SPA a estado login
  - Cancelar → cerrar modal
  Cubre: R10, R11, R34.

- [x] T14 — Crear `frontend/src/components/ConfirmModal.svelte`:
  - Componente generico reutilizable con props: `show`, `title`, `message`, `confirmText`, `cancelText`, `onConfirm`, `onCancel`
  - Overlay oscuro detras del modal
  - Boton X para cerrar (llama onCancel)
  Cubre: R11, R21.

- [x] T15 — Crear `frontend/src/components/InactivityGuard.svelte`:
  - Componente que se monta al autenticarse
  - Decodifica JWT para obtener `iat` (issued at)
  - Ejecuta `checkInactivity()` cada 60 segundos
  - Si expira, llama `auth.logout()` y muestra "Sesion expirada por inactividad"
  Cubre: R12, R41.

---

## Fase 4 — Layout y componentes del kiosco

- [x] T16 — Crear `frontend/src/App.svelte` (componente raiz):
  - Inicializa auth store desde localStorage
  - Si no autenticado → muestra AuthModal
  - Si autenticado → muestra layout segun rol (KioskLayout o AdminLayout)
  - Monta InactivityGuard
  - Carga estilos globales desde `app.css`
  Cubre: R1, R2.

- [x] T17 — Crear `frontend/src/app.css` con variables CSS (paleta de colores), estilos globales (body, inputs, botones, modales), clases utilitarias. Cubre: R10 (consistencia visual).

- [x] T18 — Crear `frontend/src/components/KioskLayout.svelte`:
  - Header con nombre de usuario (izquierda) + LogoutButton (derecha)
  - EmergencyBanner en la parte superior (condicional)
  - Slot para contenido (/kiosco o /kiosco/historial)
  - Estilo: fondo oscuro, texto claro
  Cubre: R10, R31.

- [x] T19 — Crear `frontend/src/components/AdminLayout.svelte`:
  - Header con LogoutButton (derecha)
  - Slot para contenido admin (placeholder)
  Cubre: R10, R33.

- [x] T20 — Crear `frontend/src/components/AdminPlaceholder.svelte`:
  - Pagina simple con titulo "Panel de Administracion"
  - Mensaje "Modulo en construccion — Proximamente"
  Cubre: R33.

---

## Fase 5 — Formulario de pesaje (/kiosco)

- [x] T21 — Crear `frontend/src/components/KioskForm.svelte`:
  - Formulario con campos: Tractomula (text), Vagon (text), Guia (text)
  - Dropdown Hacienda → carga via `GET /api/haciendas` con paginacion (page, page_size=100) y carga paginas adicionales en segundo plano si es necesario
  - Dropdown Suerte → se carga via `GET /api/suertes?hacienda_id=X` al seleccionar Hacienda
  - 3 componentes WeightField: Peso Muestra, Peso Mineral, Peso Vegetal
  - ScaleReader para mostrar peso en vivo
  - Boton "Confirmar" (grande, destacado)
  - Boton "Reset" (con ConfirmModal)
  - Estados de carga y error en cada operacion
  Cubre: R14, R15, R16, R19, R20, R21, R32, R40.

- [x] T22 — Crear `frontend/src/components/WeightField.svelte`:
  - Props: `fieldName` (string), `bind:value` (number), `disabled` (boolean)
  - Input numerico con formato (3 decimales)
  - Boton "Tara" → pone el campo a 0
  - Boton "Leer" → toma el peso actual del ScaleReader (store)
  - Input deshabilitado si modo normal, habilitado si modo manual
  Cubre: R15, R16, R24, R25.

- [x] T23 — Crear `frontend/src/components/ScaleReader.svelte`:
  - Indicador de peso en vivo (fuente grande ~32px, destacado)
  - Indicador de estabilidad: verde "Estable" si `is_stable`, amarillo "Inestable" si no
  - Conecta al WebSocket al montar el componente
  - Desconecta al desmontar
  - Muestra "Bascula desconectada" si ws.connected === false tras reintentos
  Cubre: R17, R18, R35.

---

## Fase 6 — Historial (/kiosco/historial)

- [x] T24 — Crear `frontend/src/components/HistoryTable.svelte`:
  - Tabla responsive con columnas: Fecha, Hora, Tractomula, Vagon, Guia, Hacienda, Suerte, Peso Muestra, Peso Mineral, Peso Vegetal
  - Selector de rango de fechas (inputs type="date" para "Desde" y "Hasta") con boton "Filtrar"
  - Carga datos via `GET /api/weighings?page=1&page_size=20&start_date=&end_date=`
  - Controles de paginacion: botones "Anterior"/"Siguiente", indicador "Pagina X de Y", selector page_size (10,20,50)
  - Orden descendente por fecha
  - Mensaje "No hay pesajes registrados" si lista vacia
  - Mensaje "No se encontraron registros para el filtro seleccionado" si filtro da 0 resultados
  - Estado de carga (spinner o skeleton)
  - Estado de error con reintento
  - Al cambiar filtro de fecha, reiniciar a pagina 1
  Cubre: R22, R37, R38, R39.

---

## Fase 7 — Emergencia: banner + modal

- [x] T25 — Crear `frontend/src/components/EmergencyBanner.svelte`:
  - Polling cada 5s a `GET /api/emergency/status`
  - Si `manual_mode: true` → muestra banner rojo/amarillo con mensaje y tiempo restante
  - Si `manual_mode: false` → banner oculto
  - Boton "Solicitar emergencia" dentro del banner → abre EmergencyModal
  - Cuando modo manual activo, expone evento o store para que WeightField se vuelva editable
  Cubre: R23, R24, R25.

- [x] T26 — Crear `frontend/src/components/EmergencyModal.svelte`:
  - Modal que carga `GET /api/emergency/admins` para dropdown de supervisores
  - Campo de texto "Motivo" (obligatorio, con validacion)
  - Boton "Enviar solicitud"
  - Llamada a `POST /api/emergency/request` con `{admin_id, reason}`
  - Exito → mensaje de confirmacion y cierre del modal
  - Error → mensaje en modal sin cerrar
  Cubre: R26, R27, R28.

---

## Fase 8 — Integracion final, build y verificacion

- [x] T27 — Crear `frontend/src/main.js` (entry point Svelte):
  - `import App from './App.svelte'`
  - `import './app.css'`
  - Montar App en `document.getElementById('app')`
  Cubre: R1 (punto de entrada).

- [x] T28 — Crear `frontend/index.html` (entry point del build):
  - Minimal HTML5 con `<div id="app"></div>`
  - `<script type="module" src="/src/main.js"></script>` (Vite lo transforma en el build)
  - Meta charset utf-8, viewport, lang="es"
  Cubre: R36.

- [x] T29 — Ejecutar `npm run build` en `frontend/` y verificar que produce `dist/index.html`, `dist/bundle.js`, `dist/bundle.css`. Cubre: R36.

- [x] T30 — Copiar `frontend/dist/*` a `src/static/` y verificar que los archivos esten en la ubicacion correcta. Cubre: R36.

- [x] T31 — Reiniciar el backend y verificar que `http://localhost:8000` sirve el SPA (index.html) y que `http://localhost:8000/static/bundle.js` existe. Cubre: R36.

- [x] T32 — Smoke test manual: abrir `http://localhost:8000` en Chrome, verificar que se muestra el modal de login. Cubre: R1.

- [x] T33 — Verificar que `npm run build` no produce errores y que el bundle final es < 100 KB (min+gz). Cubre: ADR-02 de frontend-architecture.md.

- [x] T34 — Ejecutar `./init.ps1` — todos los bloques `[OK]`. Cubre: verificacion Nivel 3.

- [x] T35 — Verificar trazabilidad completa en `progress/impl_frontend_login_kiosk.md`: mapear cada `R<n>` a su test o verificacion manual. Cubre: trazabilidad.
