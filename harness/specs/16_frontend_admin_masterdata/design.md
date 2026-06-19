# Design — Frontend Admin: CRUD de Datos Maestros

> Feature 16 (14c) — CRUD completo de Usuarios, Haciendas y Suertes. Código
> fuente existente del desarrollo de feature 14. Esta feature verifica y
> corrige el funcionamiento de los CRUDs y sus modales asociados.

---

## 1. Arquitectura general

```
App.svelte
└── AdminLayout.svelte             [de Feature 14 / 14a]
    ├── Sidebar                    [de Feature 14 / 14a]
    └── Slot de contenido          [segun currentRoute]
        ├── AdminUsers.svelte      [/admin/usuarios, Feature 16]
        │   └── UserFormModal      [modal reutilizable crear/editar]
        ├── AdminHaciendas.svelte  [/admin/haciendas, Feature 16]
        │   └── HaciendaFormModal  [modal reutilizable crear/editar]
        ├── AdminSuertes.svelte    [/admin/suertes, Feature 16]
        │   └── SuerteFormModal    [modal reutilizable crear/editar]
        └── ConfirmModal           [compartido, de feature 13]
```

## 2. Archivos a verificar (ya existen)

| Archivo                             | Proposito                                    |
|-------------------------------------|----------------------------------------------|
| `frontend/src/components/AdminUsers.svelte`      | CRUD de usuarios con tabla + modales |
| `frontend/src/components/UserFormModal.svelte`   | Modal crear/editar usuario           |
| `frontend/src/components/AdminHaciendas.svelte`  | CRUD de haciendas con tabla + modales|
| `frontend/src/components/HaciendaFormModal.svelte`| Modal crear/editar hacienda          |
| `frontend/src/components/AdminSuertes.svelte`    | CRUD de suertes filtrable por hacienda|
| `frontend/src/components/SuerteFormModal.svelte` | Modal crear/editar suerte            |
| `frontend/src/components/ConfirmModal.svelte`    | Modal generico de confirmacion       |

## 3. Archivos a modificar (si es necesario)

| Archivo                             | Correccion posible                    |
|-------------------------------------|---------------------------------------|
| `frontend/src/components/AdminUsers.svelte` | Problema conocido: falta paginacion en tabla de usuarios |

## 4. Backend: NO se modifican archivos en `src/` ni `tests/`

Todos los endpoints ya existen. Esta feature es frontend-only.

## 5. Detalle de componentes a verificar

### 5.1 AdminUsers.svelte

Tabla de usuarios + operaciones CRUD:
- Carga `GET /api/users` al montar
- Tabla: ID, Usuario, Nombre, Documento, Rol, Activo (SI/NO), Creado, Actualizado
- Boton "Nuevo Usuario" → abre UserFormModal en modo create
- Boton "Editar" por fila → abre UserFormModal en modo edit
- Boton "Desactivar" por fila → ConfirmModal → DELETE /api/users/{id}
- Problema conocido: falta paginacion en tabla (mostrar solo primeros N)

### 5.2 UserFormModal.svelte

Modal reutilizable:
- Create mode: username, password, full_name, document, role
- Edit mode: full_name, document, role, is_active, new_password (opcional)
- Validacion frontend: campos requeridos no vacios
- Callbacks: onSave, onClose

### 5.3 AdminHaciendas.svelte

CRUD de haciendas con paginacion:
- Carga `GET /api/haciendas?page=1&page_size=100` al montar
- Tabla: ID, Codigo, Nombre, Creado, Actualizado, Acciones
- CRUD completo con modales
- Soft-delete via DELETE

### 5.4 HaciendaFormModal.svelte

Modal reutilizable para crear/editar hacienda:
- Campos: codigo (max 8 chars), nombre (max 255 chars)

### 5.5 AdminSuertes.svelte

CRUD de suertes filtrable por hacienda:
- Dropdown de seleccion de hacienda arriba
- Tabla filtrada al seleccionar
- CRUD completo con modales

### 5.6 SuerteFormModal.svelte

Modal reutilizable para crear/editar suerte:
- Create: hacienda_id (select, readonly), codigo_suerte (max 4 chars)
- Edit: codigo_suerte

## 6. Estado actual del codigo

Problemas conocidos del closure de feature 14:
- CRUD Usuarios: falta paginacion (solo AdminHaciendas y AdminSuertes la tienen)
- Verificar manejo de errores HTTP 409 en todos los CRUDs
- Verificar que soft-delete funciona correctamente

## 7. Persistencia

Esta feature NO modifica la base de datos.

## 8. github_labels

```
frontend, svelte, admin, users, haciendas, suertes, crud
```
