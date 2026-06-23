# Plan bug — user_phone_not_exposed

## Sintoma

**Issue 1 — Phone no expuesto:**
- No hay campo "Teléfono" en /admin/usuarios (create/edit modal)
- POST /api/users response no incluye phone
- GET /api/users response no incluye phone
- GET /api/emergency/admins no retorna phone
- El SMS de emergencia no se envía cuando supervisor.phone=None

**Issue 2 — Document ambiguo:**
- El campo `document` se interpreta como documento de identidad pero es realmente el código interno de empresa (employee_code)
- La tabla en /admin/usuarios muestra "Documento" (sugiere identidad legal)
- API usa `document` en vez de `employee_code`
- BD columna se llama `document`, debe migrarse a `employee_code`

## Causa raiz

1. **Phone not exposed:** La columna `phone` existe en la BD (migración `2026_06_16_000002_add_phone_to_users.sql`) y en el modelo SQLAlchemy (`User.phone` en `src/models.py`), pero nunca fue incluida en:
   - Los schemas Pydantic `UserCreate`, `UserUpdate`, `UserResponse` (src/users.py)
   - La función `_user_to_response()` (src/users.py)
   - El endpoint `GET /api/emergency/admins` (src/emergency_mode.py)
   - El frontend (`UserFormModal.svelte`, `AdminUsers.svelte`)

2. **Document → employee_code:** El campo está nombrado `document` en toda la pila (BD, modelo ORM, schemas Pydantic, frontend) desde su creación en la feature 3 (user_management), pero semánticamente es el código de empleado/ficha de la empresa, no un documento de identidad. Debe renombrarse en toda la pila con una migración de BD.

## Archivos implicados

| Archivo | Cambio |
|---------|--------|
| `src/models.py` | Renombrar `User.document` → `User.employee_code` |
| `src/users.py` | Agregar `phone` a schemas UserCreate/UserUpdate/UserResponse y _user_to_response(); renombrar `document` → `employee_code` |
| `src/emergency_mode.py` | Agregar `phone` a GET /api/emergency/admins response; renombrar `document` → `employee_code` |
| `database/migrations/2026_06_23_000001_rename_document_to_employee_code.sql` | Migración: ALTER TABLE users CHANGE COLUMN document employee_code + ADD COLUMN phone (si no existe) |
| `frontend/src/components/UserFormModal.svelte` | Agregar input "Teléfono"; renombrar "Documento" → "Código Empresa" y campos de `document` → `employee_code` |
| `frontend/src/components/AdminUsers.svelte` | Agregar columna "Teléfono"; renombrar "Documento" → "Código Empresa" |
| `tests/test_users.py` | Actualizar referencias de `document` → `employee_code` |
| `tests/test_database.py` | Actualizar referencia `fetched.document` → `fetched.employee_code` |
| `database/seeds/seed_all.py` | Actualizar referencias de `document` → `employee_code` |
| `database/seeds/seed_extra.py` | Actualizar referencias de `document` → `employee_code` |
| `frontend/src/components/__tests__/UserFormModal.test.js` | Actualizar payload esperado: `document` → `employee_code` |
| `frontend/src/components/__tests__/AdminUsers.test.js` | Actualizar mock data y assertions: `document` → `employee_code` |

## Fix propuesto

### Backend
1. **src/models.py:** Renombrar la columna `document` a `employee_code`
2. **src/users.py:**
   - Agregar `phone: str | None = None` a `UserCreate`, `UserUpdate`, `UserResponse`
   - Renombrar `document` → `employee_code` en los tres schemas
   - Actualizar `_user_to_response()` para incluir `phone` y `employee_code`
   - Actualizar `create_user()` y `update_user()` para usar `employee_code`
3. **src/emergency_mode.py:** Agregar `"phone": u.phone` y cambiar `"document"` → `"employee_code"` en GET /api/emergency/admins

### Base de datos
4. **Migración SQL:** Crear `2026_06_23_000001_rename_document_to_employee_code.sql` con:
   ```sql
   ALTER TABLE users CHANGE COLUMN document employee_code VARCHAR(32) NOT NULL DEFAULT '';
   ```

### Frontend
5. **UserFormModal.svelte:**
   - Renombrar campo `form.document` → `form.employee_code`
   - Cambiar label "Documento" → "Código Empresa"
   - Cambiar placeholder "Documento (opcional)" → "Código de empleado (opcional)"
   - Agregar campo "Teléfono" con `form.phone`
   - Actualizar payloads create/edit para incluir `phone` y `employee_code`
6. **AdminUsers.svelte:**
   - Renombrar columna "Documento" → "Código Empresa"
   - Cambiar `u.document` → `u.employee_code`
   - Agregar columna "Teléfono" con `u.phone`

### Tests
7. **test_users.py:** Actualizar todos los payloads y assertions que usen `document` → `employee_code`
8. **test_database.py:** Actualizar `fetched.document` → `fetched.employee_code`
9. **UserFormModal.test.js:** Actualizar payload esperado `document` → `employee_code`
10. **AdminUsers.test.js:** Actualizar mock data y assertions

### Seeds
11. **seed_all.py:** Actualizar `document=` → `employee_code=`
12. **seed_extra.py:** Actualizar `document=` → `employee_code=`

## Plan de verificacion

- [ ] Regression test en `test_users.py` cubre que:
  - POST /api/users con `employee_code` y `phone` funciona y retorna ambos campos
  - PUT /api/users con `phone` actualiza correctamente
  - GET /api/users retorna `phone` y `employee_code`
  - GET /api/users lista incluye `phone` en response
- [ ] `./init.ps1` verde
- [ ] Tests existentes no rotos
- [ ] Frontend tests de vitest pasan
