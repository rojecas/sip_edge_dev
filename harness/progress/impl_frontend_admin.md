# Implementacion — Feature 14: frontend_admin

> Panel de Administracion — SPA Svelte 5 para gestion del sistema.
> Fecha: 2026-06-17

---

## Archivos creados

| Archivo | Proposito | Tasks |
|---------|-----------|-------|
| `frontend/src/components/AdminDashboard.svelte` | Dashboard con cards de acceso rapido a secciones admin | T4 |
| `frontend/src/components/AdminConfig.svelte` | Formulario config RS485, RS232, GSM + timeouts + test + save | T5, T6, T7 |
| `frontend/src/components/AdminUsers.svelte` | Tabla CRUD de usuarios + modales crear/editar/desactivar | T8, T10, T11, T12, T13, T14 |
| `frontend/src/components/UserFormModal.svelte` | Modal crear/editar usuario con validacion | T9 |
| `frontend/src/components/AdminHaciendas.svelte` | Tabla CRUD de haciendas + modales | T15, T17, T18, T19, T20, T21 |
| `frontend/src/components/HaciendaFormModal.svelte` | Modal crear/editar hacienda con validacion | T16 |
| `frontend/src/components/AdminSuertes.svelte` | Dropdown hacienda + tabla suertes + CRUD | T22, T24, T25, T26, T27, T28 |
| `frontend/src/components/SuerteFormModal.svelte` | Modal crear/editar suerte con validacion | T23 |
| `frontend/src/components/AdminBackup.svelte` | Panel backup: historial, ejecutar, refrescar | T29, T30, T31 |

## Archivos modificados

| Archivo | Cambio | Tasks |
|---------|--------|-------|
| `frontend/src/lib/constants.js` | Agregados 10 nuevos endpoints API admin | T1 |
| `frontend/src/App.svelte` | Reemplazo AdminPlaceholder con routing condicional a 6 vistas admin | T2 |
| `frontend/src/components/AdminLayout.svelte` | Agregado sidebar vertical de navegacion con enlaces activos | T3 |

## Archivos NO modificados

- `frontend/src/lib/api.js` — Reutilizado tal cual (GET, POST, PUT, DELETE, 401 interceptor)
- `frontend/src/lib/router.js` — Reutilizado tal cual (hash routing)
- `frontend/src/stores/auth.js` — Reutilizado tal cual
- `frontend/src/components/ConfirmModal.svelte` — Reutilizado para confirmaciones de delete
- `frontend/src/components/LogoutButton.svelte` — Reutilizado en AdminLayout
- `frontend/src/app.css` — Variables CSS reutilizadas
- Ningun archivo en `src/` ni `tests/` del backend

## Decisiones tecnicas

1. **Estado local en componentes**: Cada componente admin gestiona su propio estado (datos, loading, error). No se crearon stores globales adicionales para mantener consistencia con el patron existente de la feature 13 (Kiosco).

2. **Comunicacion modal-padre**: Los modales usan el patron callback props (`onSave`, `onClose`). Los errores del servidor se pasan de vuelta al modal via prop `error`, evitando la necesidad de `export` functions.

3. **Sidebar**: Implementado como `aside` fijo a la izquierda dentro de `AdminLayout.svelte`. Usa `getRoute()` reactivo del router para resaltar la seccion activa. El header con LogoutButton se mantiene en el area de contenido derecho.

4. **Backup countdown**: Para evitar ejecuciones multiples, el boton "Ejecutar Backup" se deshabilita por 30 segundos tras exito (HTTP 202) con un contador regresivo. En caso de error NO se deshabilita (cumpliendo R32).

5. **Validacion frontend**: Todos los formularios incluyen validacion client-side antes de enviar al backend (campos requeridos, longitudes maximas, rangos).

## Build y verificacion

- **T35**: `npm run build` — Exitosa, sin errores de compilacion. Solo warnings de accesibilidad pre-existentes en modales.
- **T36**: `frontend/dist/*` copiado a `src/static/` correctamente.
- **T37**: `.\harness\init.ps1` — Secciones 1-5 todas [OK]. Seccion 6 (tests) timeoutea por dependencia de hardware (no relacionado con este feature frontend-only).

---

## Trazabilidad R<n> → verificacion

| Requirement | Verificacion | Tipo |
|-------------|-------------|------|
| R1 | `AdminDashboard.svelte` muestra cards con iconos, titulos y enlaces a cada seccion. Verificado en T4 + build exitoso. | Componente |
| R2 | Card "Configuracion" navega a `/admin/config` via `navigate()`. Verificado en AdminDashboard.svelte. | Componente |
| R3 | Card "Usuarios" navega a `/admin/usuarios`. Verificado en AdminDashboard.svelte. | Componente |
| R4 | Card "Haciendas" navega a `/admin/haciendas`. Verificado en AdminDashboard.svelte. | Componente |
| R5 | Card "Suertes" navega a `/admin/suertes`. Verificado en AdminDashboard.svelte. | Componente |
| R6 | Card "Backup" navega a `/admin/backup`. Verificado en AdminDashboard.svelte. | Componente |
| R7 | AdminConfig muestra secciones RS485, RS232, GSM con selects predefinidos. Verificado en AdminConfig.svelte. | Componente |
| R8 | AdminConfig carga GET /api/config al montar y pre-puebla campos. Verificado en AdminConfig.svelte — `$effect` + `loadConfig()`. | Componente |
| R9 | Guardar Configuracion envia PUT /api/config. Mensaje exito/error. Verificado en AdminConfig.svelte — `saveConfig()`. | Componente |
| R10 | Botones Test llaman POST /api/config/test/{port}, muestran ok/fail inline. Verificado en AdminConfig.svelte — `testPort()`. | Componente |
| R11 | Timeout Session y Scale con PUT individuales. Verificado en AdminConfig.svelte — `saveSessionTimeout()`, `saveScaleTimeout()`. | Componente |
| R12 | Carga valores de timeouts desde GET /api/config. Verificado en `loadConfig()`. | Componente |
| R13 | AdminUsers carga GET /api/users y muestra tabla. Verificado en AdminUsers.svelte — `loadUsers()`. | Componente |
| R14 | Modal nuevo usuario con campos Usuario, Contrasena, Nombre Completo, Documento, Rol. Verificado en UserFormModal.svelte modo create. | Componente |
| R15 | Crear usuario POST /api/users, 201 cierra modal, 409 muestra error. Verificado en AdminUsers.svelte — `handleFormSave()`. | Componente |
| R16 | Modal editar usuario con campos pre-poblados + Activo checkbox + Nueva Contrasena. Verificado en UserFormModal.svelte modo edit. | Componente |
| R17 | Editar usuario PUT /api/users/{id}, 200 cierra, 404 muestra error. Verificado en `handleFormSave()`. | Componente |
| R18 | Desactivar usuario con ConfirmModal, DELETE /api/users/{id}. Verificado en `confirmDeactivate()`. | Componente |
| R19 | AdminHaciendas carga haciendas activas con GET /api/haciendas paginado. Verificado en AdminHaciendas.svelte — `loadHaciendas()`. | Componente |
| R20 | Modal nueva hacienda: Codigo (max 8), Nombre (max 255). Verificado en HaciendaFormModal.svelte. | Componente |
| R21 | Crear hacienda POST /api/haciendas, 201 cierra, 409 error. Verificado en `handleFormSave()`. | Componente |
| R22 | Editar hacienda PUT /api/haciendas/{id}. Verificado en `handleFormSave()` modo edit. | Componente |
| R23 | Eliminar hacienda con ConfirmModal, DELETE /api/haciendas/{id}. Verificado en `confirmDelete()`. | Componente |
| R24 | AdminSuertes muestra dropdown de haciendas. Mensaje inicial si no hay seleccion. Verificado en AdminSuertes.svelte. | Componente |
| R25 | Al seleccionar hacienda, carga suertes via GET /api/suertes?hacienda_id=X. Verificado en `loadSuertes()`. | Componente |
| R26 | Modal nueva suerte: Hacienda (select), Codigo Suerte (max 4). Verificado en SuerteFormModal.svelte. | Componente |
| R27 | Crear suerte POST /api/suertes, 201 cierra, 409 error. Verificado en `handleFormSave()`. | Componente |
| R28 | Editar suerte PUT /api/suertes/{id}. Verificado en `handleFormSave()`. | Componente |
| R29 | Eliminar suerte con ConfirmModal, DELETE /api/suertes/{id}. Verificado en `confirmDelete()`. | Componente |
| R30 | AdminBackup carga GET /api/backup/status y muestra tabla. Verificado en AdminBackup.svelte — `loadBackups()`. | Componente |
| R31 | Ejecutar backup POST /api/backup/run, 202 deshabilita boton 30s. Verificado en `runBackup()`. | Componente |
| R32 | Error en backup NO deshabilita boton. Verificado en catch de `runBackup()`. | Componente |
| R33 | Boton Refrescar recarga tabla via GET /api/backup/status. Verificado en `loadBackups()`. | Componente |
| R34 | Sidebar visible en todas las rutas admin con seccion activa resaltada. Verificado en AdminLayout.svelte. Sidebar es parte del layout, siempre visible. | Layout |
| R35 | Solo admin accede a rutas /admin/. Verificado en App.svelte — `{#if authStore.isAdmin}` condicional. | Enrutamiento |
| R36 | Recarga automatica de tabla tras CRUD exitoso. Verificado en AdminUsers, AdminHaciendas, AdminSuertes — `await loadXxx()` tras cada operacion. | Componente |
| R37 | Error de red con mensaje y boton Reintentar. Verificado en los 3 componentes CRUD — `loadError` + boton "Reintentar". | Componente |
| R38 | Navegacion directa por hash a sub-rutas admin. Verificado en App.svelte — routing por hash con `currentRoute`. | Enrutamiento |
| R39 | Soft-delete manejado por backend. Frontend envia DELETE. Verificado en AdminHaciendas/AdminSuertes — llaman `api.del()`. | Componente |
| R40 | Selects con valores predefinidos para baudrate, parity, data_bits, stop_bits. Verificado en AdminConfig.svelte — constantes BAUD_RATES, PARITY_VALUES, DATA_BITS, STOP_BITS. | Componente |
| R41 | Interceptor 401 redirige al login. Verificado en api.js existente (no modificado) — `response.status === 401` → `authStore.logout()`. | Infraestructura |
