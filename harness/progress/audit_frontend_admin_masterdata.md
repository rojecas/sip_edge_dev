# Auditoría — Feature 16: Frontend Admin — CRUD de Datos Maestros (14c)

> **Fecha:** 2026-06-19
> **Agente:** Líder (auditoría manual)
> **Status del spec:** pending (spec existe pero no actualizado)
> **Archivos auditados:** 7 componentes Svelte + enrutamiento + API + tests

---

## Resumen ejecutivo

| Área | Estado | Hallazgos |
|------|--------|-----------|
| CRUD Usuarios (R1-R6) | ⚠️ Parcial | Código completo; falta paginación |
| CRUD Haciendas (R7-R11) | ✅ Completo | Con paginación, soft-delete, todo OK |
| CRUD Suertes (R12-R17) | ✅ Completo | Bug #20 corregido (response format) |
| Transversales (R18-R20) | ⚠️ Observaciones | Auto-recarga y soft-delete OK; error red parcial |
| Sidebar / Routing | ✅ Completo | 6 rutas, todas mapeadas |
| Tests unitarios (frontend) | ❌ Faltante | 0 tests para componentes de Feature 16 |
| Tests backend | ✅ Existentes | test_users.py (443 lines), test_haciendas.py (840 lines, incluye suertes) |

---

## Auditoría detallada por requerimiento

### Fase 1 — CRUD Usuarios (R1-R6)

**R1** — Carga lista usuarios via GET /api/users
- ✅ AdminUsers.svelte L42: pi.get(ENDPOINTS.USERS) al montar
- ✅ Tabla con columnas: ID, Usuario, Nombre Completo, Documento, Rol, Activo, Creado, Actualizado (L179-211)
- ✅ Mensaje "No hay usuarios registrados." si lista vacía (L44-46)
- ✅ Indicador "Cargando usuarios..." (L166)
- ✅ Error de carga con botón Reintentar (L167-171)
- ⚠️ **Hallazgo (crítico): Sin paginación.** La tabla no tiene paginación a diferencia de AdminHaciendas y AdminSuertes. Si hay muchos usuarios, la tabla se vuelve inmanejable.

**R2** — Modal crear usuario
- ✅ UserFormModal.svelte con campos Usuario, Contraseña, Nombre Completo, Documento, Rol (L118-146)
- ✅ Botones "Guardar" y "Cancelar" (L162-165)
- ⚠️ **Hallazgo (menor):** ROLES incluye "corresponsal" pero según el spec de Feature 2 (auth_rbac), el rol corresponsal "no tiene login, solo contacto SMS". Verificar si tiene sentido en el frontend admin.

**R3** — POST /api/users al guardar
- ✅ AdminUsers L86: pi.post(ENDPOINTS.USERS, payload) en modo create
- ✅ L87-89: HTTP 201 → cierra modal, recarga, muestra éxito
- ❌ **Hallazgo (crítico):** El spec R3 dice: "SI la respuesta es 409 (usuario duplicado) ENTONCES el sistema DEBE mostrar el mensaje de error en el modal SIN cerrarlo." El código actual (AdminUsers L96-108) maneja el error pero la UI recibe el error del ApiError, NO hay manejo específico para HTTP 409 - solo ormError = err.message sin distinguir 409 de otros errores. El modal se mantiene abierto (porque ormShow = false solo ocurre en éxito), pero no hay lógica específica para 409.

**R4** — Modal editar usuario con campos pre-poblados
- ✅ UserFormModal L38-47: Pre-puebla full_name, document, role, is_active
- ✅ Campo opcional "Nueva Contraseña" (L154-157)
- ⚠️ **Hallazgo (menor):** El spec dice que username debe mostrarse en modo edit (aunque no sea editable). El modal edit no muestra el username actual del usuario.

**R5** — PUT /api/users/{id}
- ✅ AdminUsers L91: pi.put(\...\)" en modo edit
- ✅ L92-94: HTTP 200 → cierra modal, recarga, muestra éxito
- ✅ L98-99: Manejo específico para 404 → "Usuario no encontrado."

**R6** — Desactivar usuario con confirmación
- ✅ AdminUsers L116-118: ConfirmModal "¿Está seguro de desactivar al usuario X?"
- ✅ L121-128: DELETE /api/users/{id} al confirmar, recarga, muestra éxito
- ✅ L135-138: Cancelar → no hace nada
- ✅ Mensaje de confirmación incluye nombre de usuario (L230)

### Fase 2 — CRUD Haciendas (R7-R11)

**R7** — Carga lista haciendas paginada
- ✅ AdminHaciendas L41-47: GET /api/haciendas con paginación
- ✅ Tabla: ID, Código, Nombre, Creado, Actualizado (L186-210)
- ✅ Mensaje "No hay haciendas registradas." (L51-53)
- ✅ Paginación completa con navegación y selector page size (L213-227)
- ✅ Indicador de carga y manejo de error con Reintentar (L172-178)

**R8** — Modal nueva hacienda
- ✅ HaciendaFormModal.svelte con campos: Código (max 8), Nombre (max 255) (L77-84)
- ✅ Validación frontend: codigo requerido, max 8 chars; nombre requerido, max 255 chars (L35-40)
- ✅ maxlength en inputs (L79, L83)

**R9** — POST /api/haciendas y manejo
- ✅ AdminHaciendas L89: pi.post(ENDPOINTS.HACIENDAS, payload) en create
- ✅ L90-92: HTTP 201 → cierra modal, recarga, muestra éxito
- ⚠️ **Hallazgo (menor):** No hay manejo específico para 409. El spec requiere "SI la respuesta es 409 (codigo duplicado) ENTONCES el sistema DEBE mostrar el error en el modal SIN cerrarlo". El código genérico ormError = err.message mantendría el modal abierto en error, pero no distingue 409 explícitamente.

**R10** — PUT /api/haciendas/{id}
- ✅ AdminHaciendas L94: pi.put(\...\)
- ✅ L95-97: HTTP 200 → cierra modal, recarga, muestra éxito
- ✅ Campos pre-poblados en HaciendaFormModal (L24-28)

**R11** — DELETE /api/haciendas/{id} con soft-delete
- ✅ AdminHaciendas L119-126: DELETE confirma, recarga, muestra éxito
- ✅ Mensaje incluye "(eliminación lógica)" (L243)
- ✅ Cancelar no hace nada (L144-147)

### Fase 3 — CRUD Suertes (R12-R17)

**R12** — Dropdown de hacienda en /admin/suertes
- ✅ AdminSuertes L203-213: Dropdown carga desde GET /api/haciendas
- ✅ Mensaje inicial "Seleccione una hacienda para ver sus suertes" (L221-223)

**R13** — Carga suertes al seleccionar hacienda
- ✅ AdminSuertes L49-57:  reactivo al cambiar selectedHaciendaId
- ✅ L72-93: GET /api/suertes?hacienda_id=X con Array.isArray fallback
- ✅ Tabla: ID, Hacienda ID, Código Suerte, Creado, Actualizado (L244-267)
- ✅ "No hay suertes registradas para esta hacienda." (L84-86)
- ✅ Bug #20 corregido: maneja Array.isArray y result.items (L83)

**R14** — Modal nueva suerte
- ✅ SuerteFormModal.svelte: Hacienda (select readonly), Código Suerte max 4 chars (L86-104)
- ✅ Validación: código requerido, max 4 chars (L41-43)

**R15** — POST /api/suertes
- ✅ AdminSuertes L124: pi.post(ENDPOINTS.SUERTES, payload)
- ✅ HTTP 201 → cierra modal, recarga, muestra éxito
- ⚠️ **Hallazgo (menor):** Sin manejo específico para 409 (como en usuarios y haciendas)

**R16** — PUT /api/suertes/{id}
- ✅ AdminSuertes L129: pi.put(\...\)
- ✅ HTTP 200 → recarga tabla

**R17** — DELETE /api/suertes/{id}
- ✅ AdminSuertes L154-166: DELETE + recarga + mensaje éxito
- ✅ ConfirmModal con mensaje (L301-306)

### Fase 4 — Transversales (R18-R20)

**R18** — Auto-recarga tras CRUD exitoso
- ✅ AdminUsers: loadUsers() tras create (L88), edit (L93), deactivate (L127)
- ✅ AdminHaciendas: loadHaciendas() tras create (L91), edit (L96), delete (L125)
- ✅ AdminSuertes: loadSuertes() tras create (L126), edit (L131), delete (L160)

**R19** — Error de red con botón Reintentar
- ✅ AdminUsers L48-49: Captura ApiError/generic y muestra botón Reintentar (L170)
- ✅ AdminHaciendas L56: Igual, Reintentar presente (L176)
- ✅ AdminSuertes L89: Similar con Reintentar (L229)
- ✅ Captura "Error de conexión. Verifique que el servidor esté disponible." genérico
- ❌ **Hallazgo (moderado):** No hay botón Reintentar inline en los modales al fallar un CRUD. Si POST/PUT/DELETE falla por red, el error se muestra como resultado (banner) pero no hay un botón Reintentar específico para la operación fallida. Solo hay Reintentar en la carga inicial.

**R20** — Soft-delete manejado por backend
- ✅ AdminHaciendas L243: Mensaje incluye "(eliminación lógica)"
- ✅ DELETE enviado correctamente, frontend no elimina físicamente
- ✅ AdminSuertes: DELETE también, sin mención de soft-delete (consistente con backend)

---

## Hallazgos de arquitectura y convenciones

### Sidebar y navegación (App.svelte + AdminLayout.svelte)

- ✅ 6 rutas admin: /admin, /admin/config, /admin/usuarios, /admin/haciendas, /admin/suertes, /admin/backup
- ✅ Todas las rutas mapeadas correctamente en App.svelte L56-70
- ✅ Sidebar con las 6 rutas activas y resaltado visual (AdminLayout L15-22)

### Convenciones de código (Svelte 5)

- ✅ Uso consistente de $state(), $effect(), $props(), $derived() (rune API de Svelte 5)
- ✅ $authStore con prefijo $ para auto-subscripción a stores
- ✅ Imports ordenados: módulos de Svelte primero, luego locales
- ✅ Nombres de componentes PascalCase
- ✅ Funciones snake_case
- ✅ Docstrings en cada componente

### Seguridad

- ✅ Interceptor 401 en api.js L57-63: fuerza logout en cualquier respuesta 401
- ✅ JWT en localStorage con LS_KEYS constantes
- ⚠️ Token JWT en localStorage (vulnerable a XSS, pero es práctica aceptable para SPA sin SSR)

### Tests

- ❌ **Hallazgo (crítico):** No existen tests unitarios para los componentes de Feature 16 (AdminUsers, UserFormModal, AdminHaciendas, HaciendaFormModal, AdminSuertes, SuerteFormModal, ConfirmModal).
- ❌ Solo existen tests para AdminBackup y AdminConfig (features previas)
- ✅ Backend tests exist: test_users.py (443 líneas) y test_haciendas.py (840 líneas, incluye suertes)

---

## Resumen de hallazgos por severidad

### 🔴 Críticos (deben corregirse antes de declarar done)

| # | Hallazgo | Requisito | Archivo |
|---|----------|-----------|---------|
| C1 | Falta paginación en tabla de usuarios | R1 | AdminUsers.svelte |
| C2 | Sin tests unitarios frontend para AdminUsers, UserFormModal, AdminHaciendas, HaciendaFormModal, AdminSuertes, SuerteFormModal | Todas | tests/ |
| C3 | Sin manejo específico para HTTP 409 (usuario duplicado) en R3 — el error se muestra genéricamente | R3 | AdminUsers.svelte L96-108 |

### 🟡 Moderados

| # | Hallazgo | Requisito | Archivo |
|---|----------|-----------|---------|
| M1 | Sin manejo específico para HTTP 409 en CRUD Haciendas | R9 | AdminHaciendas.svelte L99-103 |
| M2 | Sin manejo específico para HTTP 409 en CRUD Suertes | R15 | AdminSuertes.svelte L134-138 |
| M3 | Sin Reintentar inline en errores de CRUD (POST/PUT/DELETE) — solo disponible en carga inicial | R19 | Todos los CRUDs |
| M4 | Editar usuario no muestra el nombre de usuario actual (solo campos editables) | R4 | UserFormModal.svelte |

### 🟢 Menores / Observaciones

| # | Hallazgo | Requisito |
|---|----------|-----------|
| O1 | Rol "corresponsal" en UserFormModal — verificar si debe aparecer en el frontend admin | R2 |
| O2 | JWT en localStorage (práctica estándar para SPA, pero evaluar riesgo XSS) | N/A |
| O3 | FormatDate no centralizado (duplicado en AdminUsers, AdminHaciendas, AdminSuertes) | N/A |

---

## Mapa de trazabilidad R<n> → Estado actual

| Req | Componente | Estado | Tests backend | Tests frontend |
|-----|-----------|--------|---------------|----------------|
| R1 | AdminUsers.svelte | ⚠️ Sin paginación | test_users.py | ❌ Ninguno |
| R2 | UserFormModal.svelte | ✅ | test_users.py | ❌ Ninguno |
| R3 | AdminUsers.svelte | ⚠️ Sin manejo 409 | test_users.py | ❌ Ninguno |
| R4 | UserFormModal.svelte | ✅ | test_users.py | ❌ Ninguno |
| R5 | AdminUsers.svelte | ✅ | test_users.py | ❌ Ninguno |
| R6 | AdminUsers.svelte + ConfirmModal | ✅ | test_users.py | ❌ Ninguno |
| R7 | AdminHaciendas.svelte | ✅ | test_haciendas.py | ❌ Ninguno |
| R8 | HaciendaFormModal.svelte | ✅ | test_haciendas.py | ❌ Ninguno |
| R9 | AdminHaciendas.svelte | ✅ | test_haciendas.py | ❌ Ninguno |
| R10 | AdminHaciendas.svelte | ✅ | test_haciendas.py | ❌ Ninguno |
| R11 | AdminHaciendas.svelte + ConfirmModal | ✅ | test_haciendas.py | ❌ Ninguno |
| R12 | AdminSuertes.svelte | ✅ | test_haciendas.py | ❌ Ninguno |
| R13 | AdminSuertes.svelte | ✅ | test_haciendas.py | ❌ Ninguno |
| R14 | SuerteFormModal.svelte | ✅ | test_haciendas.py | ❌ Ninguno |
| R15 | AdminSuertes.svelte | ✅ | test_haciendas.py | ❌ Ninguno |
| R16 | AdminSuertes.svelte | ✅ | test_haciendas.py | ❌ Ninguno |
| R17 | AdminSuertes.svelte + ConfirmModal | ✅ | test_haciendas.py | ❌ Ninguno |
| R18 | Todos los CRUDs | ✅ | — | ❌ Ninguno |
| R19 | Todos los CRUDs | ⚠️ Solo en carga inicial | — | ❌ Ninguno |
| R20 | AdminHaciendas.svelte + AdminSuertes.svelte | ✅ | test_haciendas.py | ❌ Ninguno |

---

## Nota sobre el spec

El spec (requirements.md + design.md + tasks.md) ya existe completo en harness/specs/16_frontend_admin_masterdata/, pero eature_list.json tiene status "pending". Debería actualizarse a "spec_ready" para continuar con el flujo SDD.

