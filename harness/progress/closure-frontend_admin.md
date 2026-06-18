# Cierre — Feature 14: frontend_admin

- **Fecha:** 2026-06-18
- **Feature ID:** 14
- **Nombre:** frontend_admin
- **Título:** Frontend - Panel de Administracion
- **Status final:** done (registrado por release-manager)

---

## Resumen

Panel de administracion SPA (Svelte 5) con:
- Dashboard con cards de acceso rapido
- Configuracion RS485/RS232/GSM con botones Test
- CRUD de Usuarios (crear, editar, desactivar)
- CRUD de Haciendas con soft-delete y paginacion
- CRUD de Suertes filtrable por hacienda con paginacion
- Panel de Backups con historial y ejecucion
- Sidebar de navegacion con resaltado de seccion activa

## Archivos creados

| Archivo | Descripcion |
|---------|-------------|
| frontend/src/components/AdminDashboard.svelte | Dashboard con 5 cards |
| frontend/src/components/AdminConfig.svelte | Formulario config + timeouts + test |
| frontend/src/components/AdminUsers.svelte | CRUD usuarios con paginacion |
| frontend/src/components/UserFormModal.svelte | Modal crear/editar usuario |
| frontend/src/components/AdminHaciendas.svelte | CRUD haciendas con paginacion |
| frontend/src/components/HaciendaFormModal.svelte | Modal crear/editar hacienda |
| frontend/src/components/AdminSuertes.svelte | CRUD suertes con paginacion |
| frontend/src/components/SuerteFormModal.svelte | Modal crear/editar suerte |
| frontend/src/components/AdminBackup.svelte | Panel de backups |

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| frontend/src/App.svelte | Routing condicional,  en templates |
| frontend/src/components/AdminLayout.svelte | Sidebar + navegacion |
| frontend/src/components/KioskLayout.svelte | Username prop |
| frontend/src/lib/constants.js | Nuevos endpoints admin |
| frontend/src/main.js | Fix: new App() -> mount() (Svelte 5 API) |
| frontend/src/stores/auth.js | Cambio de  a writable/derived |
| frontend/src/stores/emergency.js | Cambio a svelte/store |
| frontend/src/lib/router.js | Cambio a svelte/store |
| frontend/src/lib/ws.js | Cambio a svelte/store |
| src/main.py | GET /api/config incluye session/scale timeouts |

## Problemas conocidos pendientes

1. **CRUD Usuarios**: falta paginacion (solo AdminHaciendas y AdminSuertes la tienen)
2. **AdminBackup**: respuesta API puede no extraer .items correctamente
3. **EdgeBox**: emojis requieren fuente NotoColorEmoji (instalada via ~/.fonts/)
4. **DB**: 618 haciendas + 3821 suertes importadas en entorno local Docker

## Decisiones tecnicas

- Se uso svelte/store (writable/derived) en vez de  en .svelte.js por problemas de effect_orphan en build prod
- main.js requirio mount() de Svelte 5 en vez de new App() de Svelte 4
-  con prefix $ para auto-suscripcion reactiva
- Paginacion con selector de page size (10/20/50/100), default 20

## Verificacion

- [x] SDD: spec completo en harness/specs/14_frontend_admin/
- [x] Build: npm run build exitoso
- [x] Local (vite dev): login, dashboard, config, haciendas funcionan
- [ ] EdgeBox: desplegado pero requiere CI completo
