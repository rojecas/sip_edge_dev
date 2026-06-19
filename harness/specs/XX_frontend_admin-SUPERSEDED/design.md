# Design — Frontend: Panel de Administracion

> Decisiones tecnicas para el modulo administrativo del SPA Svelte 5.
> Esta feature agrega 6 nuevas vistas de administracion reutilizando la
> infraestructura existente (auth, api wrapper, router, layouts).

---

## 1. Arquitectura general

```
App.svelte (raiz)
└── AdminLayout.svelte (MODIFICADO: sidebar + header + slot)
    ├── Sidebar de navegacion (nuevo)
    │   ├── Dashboard       → #/admin
    │   ├── Configuracion   → #/admin/config
    │   ├── Usuarios        → #/admin/usuarios
    │   ├── Haciendas       → #/admin/haciendas
    │   ├── Suertes         → #/admin/suertes
    │   └── Backup          → #/admin/backup
    │
    └── Slot de contenido (segun ruta activa)
        ├── AdminDashboard.svelte   (#/admin)
        ├── AdminConfig.svelte      (#/admin/config)
        ├── AdminUsers.svelte       (#/admin/usuarios)
        ├── AdminHaciendas.svelte   (#/admin/haciendas)
        ├── AdminSuertes.svelte     (#/admin/suertes)
        └── AdminBackup.svelte      (#/admin/backup)
```

### Rutas del SPA (actualizacion)

| Ruta               | Componente actual       | Nuevo componente       | Rol   | Descripcion                           |
|--------------------|------------------------|------------------------|-------|---------------------------------------|
| `/admin`           | `AdminPlaceholder`     | `AdminDashboard`       | admin | Dashboard con cards de acceso rapido  |
| `/admin/config`    | —                      | `AdminConfig`          | admin | Configuracion de puertos y timeouts   |
| `/admin/usuarios`  | —                      | `AdminUsers`           | admin | CRUD de usuarios                      |
| `/admin/haciendas` | —                      | `AdminHaciendas`       | admin | CRUD de haciendas (soft-delete)       |
| `/admin/suertes`   | —                      | `AdminSuertes`         | admin | CRUD de suertes filtrable por hacienda|
| `/admin/backup`    | —                      | `AdminBackup`          | admin | Panel de backups con historial        |

---

## 2. Archivos a crear (todos en `frontend/src/components/`)

| Archivo                             | Proposito                                                    |
|-------------------------------------|--------------------------------------------------------------|
| `AdminDashboard.svelte`             | Dashboard con cards de acceso rapido a cada seccion          |
| `AdminConfig.svelte`                | Formulario de configuracion RS485, RS232, GSM + timeouts     |
| `AdminUsers.svelte`                 | Tabla de usuarios + modales crear/editar/desactivar          |
| `AdminHaciendas.svelte`             | Tabla de haciendas + modales crear/editar/eliminar           |
| `AdminSuertes.svelte`               | Dropdown hacienda + tabla suertes + modales CRUD             |
| `AdminBackup.svelte`                | Tabla de backups + boton ejecutar + boton refrescar          |
| `UserFormModal.svelte`              | Modal reutilizable para crear/editar usuario                 |
| `HaciendaFormModal.svelte`          | Modal reutilizable para crear/editar hacienda                |
| `SuerteFormModal.svelte`            | Modal reutilizable para crear/editar suerte                  |
| `ConfirmDeleteModal.svelte`         | Modal generico de confirmacion para eliminaciones            |

## 3. Archivos a modificar

| Archivo                             | Cambio                                                       |
|-------------------------------------|--------------------------------------------------------------|
| `frontend/src/App.svelte`           | Reemplazar `AdminPlaceholder` con enrutamiento condicional a los nuevos componentes segun `currentRoute`. Eliminar import de `AdminPlaceholder`. Anadir imports de todos los nuevos componentes admin. |
| `frontend/src/components/AdminLayout.svelte` | Anadir sidebar de navegacion lateral con enlaces a todas las secciones admin. El sidebar DEBE resaltar la seccion activa. El header actual se mantiene (username + logout). |
| `frontend/src/lib/constants.js`     | Anadir nuevos endpoints de API para admin: `CONFIG`, `CONFIG_TEST`, `SETUP_SESSION`, `SETUP_SCALE`, `USERS`, `USERS_BY_ID`, `HACIENDAS`, `HACIENDAS_BY_ID`, `SUERTES`, `SUERTES_BY_ID`, `BACKUP_STATUS`, `BACKUP_RUN`. |

## 4. Archivos NO modificados

- `frontend/src/lib/api.js` — Reutilizado tal cual. Ya soporta GET, POST, PUT, DELETE con JWT y 401 interceptor.
- `frontend/src/lib/router.js` — Reutilizado tal cual. El enrutamiento por hash ya funciona.
- `frontend/src/lib/ws.js` — No se modifica. El WebSocket de bascula no es necesario en admin.
- `frontend/src/lib/inactivity.js` — No se modifica. El control de inactividad ya funciona globalmente.
- `frontend/src/stores/auth.js` — No se modifica. El store de autenticacion ya funciona.
- `frontend/src/app.css` — No se modifica. Los estilos globales existentes son suficientes. Los componentes nuevos usan estilos scoped de Svelte.
- `frontend/src/components/LogoutButton.svelte` — No se modifica. Reutilizado en AdminLayout.
- `frontend/src/components/ConfirmModal.svelte` — No se modifica. Reutilizado para confirmaciones de delete.
- `frontend/src/components/KioskLayout.svelte` y `KioskForm.svelte` etc. — No se modifican.

## 5. Backend: NO se modifican archivos en `src/` ni `tests/`

Todos los endpoints que consume esta feature ya existen en el backend:

| Metodo | Endpoint | Proposito | Requirement |
|--------|----------|-----------|-------------|
| GET    | `/api/config` | Obtener configuracion actual del sistema | R8, R12 |
| PUT    | `/api/config` | Guardar configuracion de puertos | R9 |
| POST   | `/api/config/test/{port}` | Probar conectividad de puerto | R10 |
| PUT    | `/api/setup/session` | Guardar timeout de sesion | R11 |
| PUT    | `/api/setup/scale` | Guardar timeout de bascula | R11 |
| GET    | `/api/users` | Listar todos los usuarios | R13 |
| POST   | `/api/users` | Crear nuevo usuario | R15 |
| PUT    | `/api/users/{id}` | Actualizar usuario | R17 |
| DELETE | `/api/users/{id}` | Desactivar usuario (soft) | R18 |
| GET    | `/api/haciendas` | Listar haciendas activas (paginado) | R19 |
| POST   | `/api/haciendas` | Crear hacienda | R21 |
| PUT    | `/api/haciendas/{id}` | Actualizar hacienda | R22 |
| DELETE | `/api/haciendas/{id}` | Eliminar hacienda (soft-delete) | R23 |
| GET    | `/api/suertes` | Listar suertes (filtrable por hacienda_id) | R25 |
| POST   | `/api/suertes` | Crear suerte | R27 |
| PUT    | `/api/suertes/{id}` | Actualizar suerte | R28 |
| DELETE | `/api/suertes/{id}` | Eliminar suerte (soft-delete) | R29 |
| GET    | `/api/backup/status` | Obtener ultimos 10 backups | R30 |
| POST   | `/api/backup/run` | Ejecutar backup en background | R31 |

---

## 6. Detalle de componentes

### 6.1 AdminLayout.svelte (modificado)

Se agrega un sidebar vertical fijo a la izquierda con los siguientes enlaces:

```
[ Dashboard ]    → #/admin
[ Configuracion ] → #/admin/config
[ Usuarios ]     → #/admin/usuarios
[ Haciendas ]    → #/admin/haciendas
[ Suertes ]      → #/admin/suertes
[ Backup ]       → #/admin/backup
```

El sidebar DEBE:
- Tener un ancho fijo de ~220px.
- Mostrar el nombre de la seccion activa con un color de fondo resaltado.
- Ser visible en todas las rutas `/admin/*`.
- Incluir el nombre del usuario y rol en la parte superior o inferior.
- Usar `navigate()` de `router.js` para la navegacion.

### 6.2 AdminDashboard.svelte

Grid de cards (2-3 columnas responsive) con:
- Icono + titulo + descripcion breve para cada seccion.
- Al hacer clic, navega a la ruta correspondiente via `router.navigate()`.

Cards:
| Seccion       | Icono   | Ruta             |
|---------------|---------|------------------|
| Configuracion | ⚙️      | `/admin/config`  |
| Usuarios      | 👥       | `/admin/usuarios`|
| Haciendas     | 🏠       | `/admin/haciendas`|
| Suertes       | 🌱       | `/admin/suertes`  |
| Backup        | 💾       | `/admin/backup`   |

### 6.3 AdminConfig.svelte

Formulario dividido en 3 secciones con bordes/cards:

1. **RS485**: 5 selects + input path + boton "Test RS485"
2. **RS232**: 5 selects + input path + boton "Test RS232"
3. **GSM**: input numerico modem_index + boton "Test GSM"
4. **Timeouts**: session timeout (numerico) + scale timeout (numerico 1-10)

Comportamiento:
- Al montar, carga `GET /api/config` y pobla todos los campos.
- Cada seccion tiene su propio boton "Guardar" (para puertos guarda todo el JSON, para timeouts guarda individualmente).
- Los botones Test muestran el resultado (ok/fail) inline junto al boton.
- Validacion frontend: baudrate, paridad, data_bits, stop_bits solo aceptan valores de la lista predefinida.
- Estados: loading, error, success para cada operacion.

### 6.4 AdminUsers.svelte

Tabla con datos de usuarios + botones de accion en cada fila:
- "Editar" → abre `UserFormModal` en modo edicion
- "Desactivar" → abre `ConfirmModal` y luego llama DELETE

Boton "Nuevo Usuario" sobre la tabla → abre `UserFormModal` en modo creacion.

### 6.5 AdminHaciendas.svelte

Tabla con haciendas activas + botones "Editar" y "Eliminar" por fila.
Boton "Nueva Hacienda" sobre la tabla.

### 6.6 AdminSuertes.svelte

Dropdown de seleccion de hacienda en la parte superior. Al seleccionar,
carga las suertes de esa hacienda. Botones "Nueva Suerte", "Editar",
"Eliminar" por fila.

### 6.7 AdminBackup.svelte

Tabla con ultimos 10 backups. Dos botones sobre la tabla:
- "Ejecutar Backup" → POST /api/backup/run
- "Refrescar" → recarga GET /api/backup/status

La tabla muestra todas las columnas del response de backup/status.

### 6.8 UserFormModal.svelte

Modal reutilizable que recibe props:
- `show` (boolean)
- `mode` ("create" | "edit")
- `user` (objeto con datos del usuario, solo en modo edit)
- `onClose` (callback)
- `onSave` (callback con datos del formulario)

Campos en modo create: username, password, full_name, document, role
Campos en modo edit: full_name, document, role, is_active, new_password (opcional)

### 6.9 HaciendaFormModal.svelte

Modal reutilizable:
- Props: `show`, `mode`, `hacienda`, `onClose`, `onSave`
- Campos: codigo (max 8 chars), nombre (max 255 chars)

### 6.10 SuerteFormModal.svelte

Modal reutilizable:
- Props: `show`, `mode`, `suerte`, `haciendaId` (readonly en create), `onClose`, `onSave`
- Campos: codigo_suerte (max 4 chars), hacienda_id (select, readonly en edit)

---

## 7. Manejo de errores y estados

Cada componente admin debe manejar los siguientes estados para cada operacion:

| Estado | Comportamiento |
|--------|----------------|
| **Loading** | Spinner o skeleton mientras carga datos iniciales |
| **Submitting** | Boton deshabilitado + spinner durante envio de formulario |
| **Success** | Mensaje de exito toast/notificacion (duracion ~3s, auto-dismiss) |
| **Error** | Mensaje de error en rojo, sin perder datos del formulario |
| **Empty** | Mensaje "No hay X registrados" con icono informativo |
| **Network Error** | Mensaje "Error de conexion" + boton "Reintentar" |

Los mensajes de error y exito pueden implementarse como notificaciones
toast inline o como un componente `NotificationToast.svelte` reutilizable
(opcional, no requerido).

---

## 8. Routing condicional en App.svelte

El bloque actual en `App.svelte` para admin:

```svelte
{#if authStore.isAdmin}
  <AdminLayout>
    <AdminPlaceholder />
  </AdminLayout>
{/if}
```

Debe reemplazarse por:

```svelte
{#if authStore.isAdmin}
  <AdminLayout>
    {#if currentRoute === "/admin"}
      <AdminDashboard />
    {:else if currentRoute === "/admin/config"}
      <AdminConfig />
    {:else if currentRoute === "/admin/usuarios"}
      <AdminUsers />
    {:else if currentRoute === "/admin/haciendas"}
      <AdminHaciendas />
    {:else if currentRoute === "/admin/suertes"}
      <AdminSuertes />
    {:else if currentRoute === "/admin/backup"}
      <AdminBackup />
    {:else}
      <AdminDashboard />
    {/if}
  </AdminLayout>
{/if}
```

---

## 9. Integracion con el sidebar de navegacion

El sidebar en `AdminLayout.svelte` debe usar `navigate()` del router
existente. Para resaltar la seccion activa, se puede hacer:

```svelte
<script>
  import { navigate, getRoute } from "../lib/router.js";
  let currentRoute = $derived(getRoute());
</script>

<nav class="sidebar">
  <a
    class:active={currentRoute === "/admin"}
    onclick={() => navigate("/admin")}
  >Dashboard</a>
  <a
    class:active={currentRoute === "/admin/config"}
    onclick={() => navigate("/admin/config")}
  >Configuracion</a>
  <!-- ... -->
</nav>
```

---

## 10. Alternativa descartada: Componentes modulares con stores globales

**Alternativa:** Crear un store global de notificaciones/toasts y stores
individuales para cada seccion admin (usersStore, configStore, etc.),
separando la logica de negocio de los componentes de presentacion.

**Descartada por:**
1. **Complejidad innecesaria:** Cada seccion admin es independiente y no
   comparte estado entre si. Crear stores separados anade boilerplate sin
   beneficio real.
2. **Sencillez del alcance:** No hay operaciones que crucen secciones
   (ej: crear suerte no afecta la lista de usuarios). El estado local del
   componente es suficiente.
3. **Consistencia con Feature 13:** El kiosco existente maneja todo el
   estado localmente en cada componente (KioskForm, HistoryTable, etc.).
   Mantener el mismo patron evita confusion.
4. **Rendimiento:** Los stores globales re-renderizarian componentes que no
   necesitan actualizarse. El estado local via `$state` es mas eficiente.

**Beneficio de la alternativa elegida (estado local en cada componente):**
- Cada componente admin gestiona su propia carga, error y datos.
- Sin stores adicionales que mantener.
- Coherencia con el patron existente en el proyecto.
- Facil de entender y mantener.

---

## 11. Alternativa descartada: Rutas de admin como SPA independiente

**Alternativa:** Servir el panel de administracion como un SPA separado
en `/admin/index.html` con su propio bundle JS.

**Descartada por:**
1. **Duplicacion de infraestructura:** Habria que duplicar el auth store,
   api wrapper, router, y componentes compartidos (LogoutButton, modales).
2. **Mantenimiento:** Dos SPAs significan dos builds, dos bundles, dos
   puntos de entrada. Mayor superficie de errores.
3. **Experiencia de usuario:** Recargar todo el SPA al navegar entre admin
   y kiosco rompe la sensacion de aplicacion unica.
4. **Simplicidad del routing actual:** El routing por hash existente en
   `App.svelte` ya permite separar vistas de operador y admin dentro del
   mismo SPA. Anadir otro SPA es innecesario.

---

## 12. Persistencia

Esta feature NO modifica la base de datos. Toda la persistencia es
gestionada por el backend a traves de los endpoints API existentes.
El frontend solo consume y presenta datos.

---

## 13. github_labels

```
frontend, svelte, admin, dashboard, config, users, haciendas, suertes, backup
```
