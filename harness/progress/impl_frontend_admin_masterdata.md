# Implementacion — Feature 16: Frontend Admin — CRUD de Datos Maestros

> **Fecha:** 2026-06-19
> **Agente:** Implementer
> **Status spec:** in_progress → implementacion completada
> **Tests frontend:** 121 tests, 9 archivos, TODOS verdes (npx vitest run)

---

## Resumen

Feature 16 implementa el CRUD completo de datos maestros (usuarios, haciendas, suertes) en el frontend Svelte 5. Se corrigieron 6 hallazgos de la auditoria previa y se implementaron tests unitarios completos para todos los componentes.

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `frontend/src/components/AdminUsers.svelte` | Paginacion (C1) + manejo HTTP 409 (C3) |
| `frontend/src/components/UserFormModal.svelte` | Mostrar username en modo edit (M4) |
| `frontend/src/components/AdminHaciendas.svelte` | Manejo HTTP 409 (M1) |
| `frontend/src/components/AdminSuertes.svelte` | Manejo HTTP 409 (M2) |

### Archivos nuevos (tests)

| Archivo | Cubre |
|---------|-------|
| `frontend/src/components/__tests__/AdminUsers.test.js` | R1, R3, R5, R6 |
| `frontend/src/components/__tests__/UserFormModal.test.js` | R2, R4 |
| `frontend/src/components/__tests__/AdminHaciendas.test.js` | R7, R9, R10, R11 |
| `frontend/src/components/__tests__/HaciendaFormModal.test.js` | R8 |
| `frontend/src/components/__tests__/AdminSuertes.test.js` | R12, R13, R15, R16, R17 |
| `frontend/src/components/__tests__/SuerteFormModal.test.js` | R14 |
| `frontend/src/components/__tests__/ConfirmModal.test.js` | Componente generico |

---

## Hallazgos corregidos

### C1 — Paginacion en AdminUsers.svelte (Critico)

**Problema:** La tabla de usuarios no tenia paginacion, a diferencia de AdminHaciendas y AdminSuertes.

**Solucion:**
- Se agrego import de `buildQuery` y `CONFIG`
- Se agregaron variables de estado: `currentPage`, `totalPages`, `totalItems`, `pageSize`
- `loadUsers()` ahora usa `GET /api/users?page=X&page_size=Y`
- Se agrego UI de paginacion identica a AdminHaciendas: botones Anterior/Siguiente + selector page size (10/20/50/100)
- Se agregaron las funciones `goToPage(page)` y `changePageSize(e)`
- Se agregaron estilos CSS `.pagination`, `.page-info`, `.btn-page`, `.page-size-select`

### C2 — Tests frontend (Critico)

**Problema:** No existian tests unitarios para ningun componente de Feature 16.

**Solucion:**
- Se crearon 7 archivos de test siguiendo el patron de `AdminBackup.test.js`
- Se usa `vi.mock("../../lib/api.js", ...)` para mockear el API
- Se usa `ApiError` importado del modulo mockeado para errores con `instanceof` correcto
- Tests cubren: carga de datos, renderizado de tablas, mensajes vacios/error, CRUD operaciones (POST/PUT/DELETE), manejo 409, paginacion, modales

### C3 — Manejo HTTP 409 en creacion de usuario (Critico)

**Problema:** El codigo no distingua HTTP 409 de otros errores en `handleFormSave`.

**Solucion:**
- En `AdminUsers.svelte` `handleFormSave`, se agrego caso `err.status === 409` que asigna `formError = err.message` y mantiene `formShow = true` (modal abierto)
- El codigo resultante:
  ```
  if (err.status === 409) {
    formError = err.message;
    // Modal stays open to let the user correct the duplicate
  } else if (err.status === 404) { ... }
  ```

### M1 — Manejo HTTP 409 en CRUD Haciendas (Moderado)

**Problema:** Sin manejo especifico para 409 en creacion de hacienda.

**Solucion:**
- En `AdminHaciendas.svelte` `handleFormSave`, se agrego caso `err.status === 409` que asigna `formError = err.message` y mantiene `formShow = true`

### M2 — Manejo HTTP 409 en CRUD Suertes (Moderado)

**Problema:** Sin manejo especifico para 409 en creacion de suerte.

**Solucion:**
- En `AdminSuertes.svelte` `handleFormSave`, se agrego caso `err.status === 409` que asigna `formError = err.message` y mantiene `formShow = true`

### M3 — Boton Reintentar inline en errores CRUD (Moderado)

**Evaluacion:** El comportamiento actual (mostrar error en banner + posibilidad de reintentar manualmente cerrando y re-abriendo el modal) es aceptable para errores de red en operaciones CRUD. NO se agrego reintento automatico en modales. Los errores de red se manejan a nivel de UI con mensaje de error en el modal.

### M4 — Mostrar username en modo edit de usuario (Moderado)

**Problema:** El modal de edicion no mostraba el username del usuario.

**Solucion:**
- En `UserFormModal.svelte`, se agrego un bloque `info-field` en modo edit que muestra "Usuario: {username}" como texto informativo no editable
- CSS agregado para `.info-field`, `.info-label`, `.info-value`

---

## Trazabilidad R<n> → Test

| Requirement | Test(s) | Archivo |
|-------------|---------|---------|
| R1 | `AdminUsers — carga de usuarios` (6 tests) + `AdminUsers — paginacion` (3 tests) | AdminUsers.test.js |
| R2 | `UserFormModal — Create mode` (10 tests) | UserFormModal.test.js |
| R3 | `AdminUsers — crear usuario` (4 tests, incl. 201 y 409) | AdminUsers.test.js |
| R4 | `UserFormModal — Edit mode` (8 tests, incl. username display M4) | UserFormModal.test.js |
| R5 | `AdminUsers — editar usuario` (4 tests, incl. 200 y 404) | AdminUsers.test.js |
| R6 | `AdminUsers — desactivar usuario` (3 tests) | AdminUsers.test.js |
| R7 | `AdminHaciendas — carga` (4 tests) | AdminHaciendas.test.js |
| R8 | `HaciendaFormModal` (10 tests, incl. validaciones maxlength) | HaciendaFormModal.test.js |
| R9 | `AdminHaciendas — crear hacienda` (3 tests, incl. 201 y 409 M1) | AdminHaciendas.test.js |
| R10 | `AdminHaciendas — editar hacienda` (1 test) | AdminHaciendas.test.js |
| R11 | `AdminHaciendas — eliminar hacienda` (2 tests, incl. soft-delete mensaje) | AdminHaciendas.test.js |
| R12 | `AdminSuertes — dropdown y carga` (1 test) | AdminSuertes.test.js |
| R13 | `AdminSuertes — dropdown y carga` (5 tests, Array.isArray y {items}) | AdminSuertes.test.js |
| R14 | `SuerteFormModal` (8 tests, incl. validaciones) | SuerteFormModal.test.js |
| R15 | `AdminSuertes — crear suerte` (2 tests, incl. 409 M2) | AdminSuertes.test.js |
| R16 | `AdminSuertes — editar suerte` (1 test, incl. PUT verificacion) | AdminSuertes.test.js |
| R17 | `AdminSuertes — eliminar suerte` (1 test) | AdminSuertes.test.js |
| R18 | Verificado en tests de AdminUsers (create L198, edit L263, deactivate L307), AdminHaciendas, AdminSuertes | Admin* test files |
| R19 | `AdminUsers — carga -> error con Reintentar` | AdminUsers.test.js |
| R20 | `AdminHaciendas — eliminar hacienda -> mensaje eliminacion logica` | AdminHaciendas.test.js |

---

## Impacto en features existentes

**Ninguno.** Feature 16 es frontend-only. Los archivos modificados son exclusivos de esta feature (componentes Svelte en `frontend/src/components/`). No se modificaron archivos de backend (`src/`) ni librerias compartidas que afecten otras features.

Las features dependientes (feature 17 — frontend_analytics, feature 18 — harvest_type) no se ven afectadas porque:
- Feature 17 depende de 16 (routing admin ya esta establecido)
- Feature 18 toca backend + frontend kiosco, no admin CRUD

---

## Verificacion

- `npx vitest run`: **121 tests, 9 archivos, TODOS verdes** ✅
- `npm run build`: **Build exitoso** (solo warnings a11y pre-existentes) ✅
- `./harness/init.ps1`: Secciones 1-5 [OK]; Seccion 6 (Docker tests) timed out (normal en Windows, requiere Docker corriendo) ⚠️

---

## Tasks completadas (tasks.md)

T1-T17 y T20 marcadas [x]. T18 (copiar dist a static) y T19 (init.ps1 completo) requieren entorno Docker.

---

## Convenciones Svelte 5 verificadas

- [x] `$state()` para estado reactivo en `.svelte`
- [x] `$props()` para props de componentes
- [x] `$effect()` en AdminSuertes para reactividad al cambiar `selectedHaciendaId`
- [x] `import { onMount } from "svelte"` explicito
- [x] NO uso de `$:` (Svelte 4 legacy)
- [x] NO uso de `new Component()` (Svelte 4)
- [x] `api.js` usa `writable` de `svelte/store` (`.js` simple)
- [x] Templates usan `$authStore` con prefijo `$`
- [x] API responses: `Array.isArray(result) ? result : result.items` en AdminSuertes
