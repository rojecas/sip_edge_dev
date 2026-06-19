# Design — Frontend Admin: Dashboard y Navegación

> Feature 14 (14a) — Fundación del módulo administrativo: dashboard, sidebar,
> enrutamiento RBAC e interceptor 401. Código fuente existente en el repositorio.
> Esta feature verifica y consolida la infraestructura compartida.

---

## 1. Arquitectura general

```
App.svelte (raiz)
└── AdminLayout.svelte            [MODIFICADO: sidebar + header + slot]
    ├── Sidebar de navegacion     [nuevo en 14a, 6 enlaces]
    │   ├── Dashboard             → #/admin
    │   ├── Configuracion         → #/admin/config
    │   ├── Usuarios              → #/admin/usuarios
    │   ├── Haciendas             → #/admin/haciendas
    │   ├── Suertes               → #/admin/suertes
    │   └── Backup                → #/admin/backup
    │
    └── Slot de contenido (placeholder para 14b y 14c)
        └── AdminDashboard.svelte (#/admin, creado en 14a)
```

### Rutas del SPA (actualizacion)

| Ruta               | Componente             | Rol   | Feature responsable |
|--------------------|------------------------|-------|---------------------|
| `/admin`           | `AdminDashboard`       | admin | 14a (esta)         |
| `/admin/config`    | `AdminConfig`          | admin | 19 (14b)           |
| `/admin/usuarios`  | `AdminUsers`           | admin | 20 (14c)           |
| `/admin/haciendas` | `AdminHaciendas`       | admin | 20 (14c)           |
| `/admin/suertes`   | `AdminSuertes`         | admin | 20 (14c)           |
| `/admin/backup`    | `AdminBackup`          | admin | 19 (14b)           |

---

## 2. Archivos a verificar (ya existen del desarrollo de feature 14)

| Archivo                           | Proposito                                    |
|-----------------------------------|----------------------------------------------|
| `frontend/src/components/AdminDashboard.svelte` | Dashboard con 5 cards de acceso rapido |
| `frontend/src/components/AdminLayout.svelte`    | Layout con sidebar de navegacion       |

## 3. Archivos a verificar (modificados por feature 14)

| Archivo                           | Cambio                                       |
|-----------------------------------|----------------------------------------------|
| `frontend/src/App.svelte`         | Enrutamiento condicional para /admin/*       |
| `frontend/src/lib/constants.js`   | Endpoints de API admin agregados             |

## 4. Dependencias de infraestructura (compartidas con feature 13)

| Archivo                           | Proposito                                    |
|-----------------------------------|----------------------------------------------|
| `frontend/src/stores/auth.js`     | Store reactivo de autenticacion ($authStore) |
| `frontend/src/lib/api.js`         | Fetch wrapper con JWT + 401 interceptor      |
| `frontend/src/lib/router.js`      | Ruteo SPA basado en hash                     |

## 5. Backend: NO se modifican archivos en `src/` ni `tests/`

Todos los endpoints que consume esta feature ya existen.

## 6. Detalle de componentes a verificar

### 6.1 AdminLayout.svelte (verificar sidebar)

El sidebar vertical fijo a la izquierda DEBE:
- Tener 6 enlaces: Dashboard, Configuracion, Usuarios, Haciendas, Suertes, Backup
- Usar `navigate()` del router existente
- Resaltar la seccion activa con color de fondo distinto
- Ser visible en todas las rutas `/admin/*`
- Ancho fijo ~220px

### 6.2 AdminDashboard.svelte (verificar cards)

Grid de 5 cards responsive con:
- Icono + titulo + descripcion para cada seccion
- Al hacer clic, navega a la ruta correspondiente

### 6.3 App.svelte (verificar routing)

El bloque condicional para admin DEBE:
- Renderizar `AdminLayout` solo si `authStore.isAdmin` es true
- Dentro del layout, elegir el componente segun `currentRoute`
- Default a `AdminDashboard` si la ruta no coincide con ninguna sub-ruta

### 6.4 api.js (verificar interceptor 401)

El interceptor 401 existente DEBE:
- Detectar HTTP 401 en cualquier respuesta
- Llamar `authStore.logout()`
- Lanzar `ApiError` con mensaje "Sesion expirada o no autorizada"
- Funcionar en todas las vistas admin

## 7. Estado actual del codigo

El codigo para esta feature ya existe y fue desplegado como parte de la
feature 14 original. Esta feature es de **verificacion y consolidacion**:
- El codigo existe en `frontend/src/components/`
- El build (`npm run build`) es exitoso
- Los componentes se cargan correctamente en el navegador
- Sin embargo, los stores compartidos fueron retro-fitheados de Svelte 5
  runes a `svelte/store` durante la implementacion de feature 14, lo que
  requiere verificacion de que la reactividad sigue funcionando.

## 8. Alternativa descartada: Sidebar como componente independiente

**Alternativa:** Crear un componente `Sidebar.svelte` separado de `AdminLayout`.

**Descartada por:** El sidebar es parte intrinseca del layout admin. Separarlo
no aporta reutilizacion (solo existe en admin) y anade complejidad de
comunicacion entre componentes via props/stores.

## 9. Persistencia

Esta feature NO modifica la base de datos.

## 10. github_labels

```
frontend, svelte, admin, dashboard, sidebar, navigation
```
