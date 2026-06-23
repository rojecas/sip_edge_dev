# Cierre — user_phone_not_exposed

## Resumen
Bug 22 corregido: se expuso el campo `phone` en toda la pila (API CRUD de usuarios, endpoint de emergencia, frontend admin) y se renombró `document` → `employee_code` en toda la pila (modelo, schemas, API, frontend, seeds, tests) con migración de base de datos.

## Sintoma
**Phone no expuesto:** el campo `phone` existía en la BD y en el modelo ORM pero no era visible ni editable en la API CRUD de usuarios, en el endpoint de emergencia ni en el frontend admin, bloqueando las funcionalidades de emergencia SMS (F9) y reset de password por SMS (F12).

**Document ambiguo:** el campo `document` se etiquetaba como "Documento" (sugiriendo documento de identidad) cuando en realidad es el código interno de empresa/empleado, causando confusión en la interfaz.

## Causa raiz
- **Phone:** omisión durante la implementación de features 9 y 12: se agregó la columna y el modelo ORM pero nunca se expuso en los schemas Pydantic, la función `_user_to_response()`, el endpoint de emergencia, ni el frontend.
- **Document → employee_code:** el nombre original `document` fue insuficientemente descriptivo desde la feature 3 (user_management). El campo almacena códigos de empleado/ficha, no documentos de identidad.

## Fix aplicado
1. **src/models.py:** Renombrado `User.document` → `User.employee_code`
2. **src/seed.py:** Actualizado `document=` → `employee_code=` en seed_admin_user
3. **src/users.py:** Agregado `phone` a `UserCreate`, `UserUpdate`, `UserResponse`; renombrado `document` → `employee_code` en los tres schemas y en `_user_to_response()`, `create_user()`, `update_user()`
4. **src/emergency_mode.py:** Agregado `"phone"` y renombrado `"document"` → `"employee_code"` en GET /api/emergency/admins
5. **database/migrations/2026_06_23_000001_rename_document_to_employee_code.sql:** Migración SQL: `ALTER TABLE users CHANGE COLUMN document employee_code VARCHAR(32) NOT NULL DEFAULT ''`
6. **frontend/UserFormModal.svelte:** Agregado campo "Teléfono"; renombrado "Documento" → "Código Empresa" con placeholder "Código de empleado"
7. **frontend/AdminUsers.svelte:** Agregada columna "Teléfono"; renombrada cabecera "Documento" → "Código Empresa"
8. **tests/test_users.py:** Tests actualizados con `employee_code` y `phone`
9. **tests/test_database.py:** Actualizado `fetched.document` → `fetched.employee_code`
10. **database/seeds/seed_all.py:** Actualizados campos `document=` → `employee_code=`, agregado `phone` al admin
11. **database/seeds/seed_extra.py:** Actualizado `document=` → `employee_code=`
12. **frontend/test UserFormModal.test.js:** Actualizados mocks y payloads esperados
13. **frontend/test AdminUsers.test.js:** Actualizados mocks con `employee_code` y `phone`

## Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `src/models.py` | Renombrado `document` → `employee_code` |
| `src/seed.py` | Actualizado constructor de User |
| `src/users.py` | Phone expuesto + document → employee_code en schemas y lógica |
| `src/emergency_mode.py` | Phone + employee_code en GET /api/emergency/admins |
| `database/migrations/2026_06_23_000001_rename_document_to_employee_code.sql` | Migración BD |
| `frontend/src/components/UserFormModal.svelte` | Input Teléfono + renombrar campos |
| `frontend/src/components/AdminUsers.svelte` | Columna Teléfono + renombrar cabecera |
| `tests/test_users.py` | Tests actualizados con nuevos campos |
| `tests/test_database.py` | Actualizado `fetched.document` → `fetched.employee_code` |
| `database/seeds/seed_all.py` | Seeds actualizados |
| `database/seeds/seed_extra.py` | Seeds actualizados |
| `frontend/src/components/__tests__/UserFormModal.test.js` | Mocks actualizados |
| `frontend/src/components/__tests__/AdminUsers.test.js` | Mocks actualizados |

## Verificación
- [x] `./harness/init.ps1` — validación de schema OK (sección 4)
- [x] `test_users.py` — 28 tests OK (todos pasan)
- [x] `test_database.py` — 10 tests OK (todos pasan)
- [x] `test_emergency_mode.py` — 55 tests OK (todos pasan)
- [x] Frontend vitest UserFormModal.test.js — 17 tests OK
- [x] Frontend vitest AdminUsers.test.js — tests de funcionalidad CRUD OK (4 tests de paginación pre-existentes fallan por feature 21 aún pendiente)
- [x] Regression tests cubren:
  - POST /api/users con `employee_code` y `phone` funciona y retorna ambos campos
  - PUT /api/users con `employee_code` y `phone` actualiza correctamente
  - GET /api/users lista incluye `employee_code` y `phone` en response
  - GET /api/users/{id} incluye `employee_code` y `phone`

## Lecciones / pitfalls
- Al renombrar una columna del modelo ORM, hay que buscar TODAS las referencias en el código, incluyendo `src/seed.py` que es un archivo pequeño pero crítico para el primer arranque.
- Los tests de frontend `AdminUsers.test.js` tenían pruebas de paginación pre-escritas para la feature 21 que nunca fue implementada. Esos 4 tests fallan antes y después de mi cambio.
