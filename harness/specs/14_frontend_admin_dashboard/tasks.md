# Tasks — Frontend Admin: Dashboard y Navegación

> Marcar `[x]` al completar. Cada task referencia al menos un `R<n>`.
> NOTA: El codigo fuente ya existe del desarrollo de feature 14. Estas tasks
> verifican su correcto funcionamiento y corrigen problemas conocidos.

---

## Fase 1 — Verificacion de componentes existentes

- [x] T1 — Verificar `AdminDashboard.svelte`:
  - Renderiza 5 cards (Configuracion, Usuarios, Haciendas, Suertes, Backup)
  - Cada card tiene icono + titulo + descripcion
  - Al hacer clic navega a la ruta correcta via `router.navigate()`
  - Grid responsive (2-3 columnas)
  Cubre: R1, R2, R3, R4, R5, R6.

- [x] T2 — Verificar `AdminLayout.svelte` (sidebar):
  - Sidebar visible en todas las rutas /admin/*
  - 6 enlaces funcionales: Dashboard, Configuracion, Usuarios, Haciendas, Suertes, Backup
  - Seccion activa resaltada visualmente (background distinto)
  - Header con LogoutButton se mantiene
  - Variables CSS existentes reutilizadas (`--bg-secondary`, `--text-primary`, etc.)
  Cubre: R7.

## Fase 2 — Verificacion de enrutamiento y RBAC

- [x] T3 — Verificar `App.svelte` routing condicional para admin:
  - Solo renderiza `AdminLayout` si `authStore.isAdmin` es true
  - `currentRoute` determina que componente admin se muestra
  - Default a `AdminDashboard` si ruta no coincide
  - Navegacion directa por hash a sub-rutas funciona (R9)
  Cubre: R8, R9.

- [x] T4 — Verificar RBAC:
  - Usuario con rol "operator" NO puede acceder a /admin/*
  - Redirige a /kiosco al intentar
  - Usuario con rol "admin" SI puede acceder a todas las sub-rutas admin
  Cubre: R8.

## Fase 3 — Verificacion del interceptor 401

- [x] T5 — Verificar interceptor HTTP 401 en vistas admin:
  - Si el token expira, `api.js` detecta HTTP 401
  - Llama `authStore.logout()`
  - Redirige al modal de login con mensaje "Sesion expirada o no autorizada"
  Cubre: R10.

## Fase 4 — Verificacion de stores compartidos (regresion post-feature 14)

- [x] T6 — Verificar que `auth.js` (convertido a svelte/store) funciona correctamente:
  - `$authStore.isAuthenticated` es reactivo
  - `$authStore.isAdmin` y `$authStore.isOperator` se actualizan al cambiar rol
  - `authStore.login()` y `authStore.logout()` persisten en localStorage
  - Auto-subscription con prefijo `$` funciona en todos los componentes
  Cubre: R8.

- [x] T7 — Verificar que `router.js` (convertido a svelte/store) funciona:
  - `navigate()` cambia la ruta correctamente
  - `getRoute()` devuelve la ruta actual
  - `isRoute()` funciona en condicionales de template
  Cubre: R9.

## Fase 5 — Build y verificacion

- [x] T8 — Ejecutar `npm run build` en `frontend/`:
  - Sin errores de compilacion
  - Sin warnings de accesibilidad nuevos
  - Bundle JS < 100 KB (gzip)
  Cubre: verificacion Nivel 1.

- [x] T9 — Copiar `frontend/dist/*` a `src/static/`:
  - Archivos copiados correctamente
  - `src/static/index.html` existe
  Cubre: verificacion despliegue.

- [x] T10 — Ejecutar `./init.ps1`:
  - Todos los bloques `[OK]`
  - Tests del backend pasan (Docker)
  Cubre: verificacion Nivel 3.

- [x] T11 — Verificar trazabilidad completa en `progress/impl_frontend_admin_dashboard.md`:
  - Mapear cada `R<n>` a su test o verificacion manual
  Cubre: trazabilidad.
