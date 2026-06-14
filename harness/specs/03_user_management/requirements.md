# Requirements — Gestión de Usuarios (CRUD)

> Feature 3 — RF-021: Interfaz gráfica Admin para Crear/Leer/Actualizar/Desactivar
> usuarios (Nombre, Documento, Rol, Estado). Desactivación lógica sin eliminación física.

---

## R1 — Listar usuarios (GET /api/users)

CUANDO el Admin autenticado hace GET a `/api/users`, el sistema DEBE
devolver una lista JSON de todos los usuarios activos e inactivos, excluyendo
el campo `password_hash` de cada registro.

## R2 — Obtener usuario único (GET /api/users/{id})

CUANDO el Admin autenticado hace GET a `/api/users/{id}`, el sistema DEBE
devolver el usuario correspondiente sin el campo `password_hash`.
SI el `id` no existe ENTONCES el sistema DEBE responder 404.

## R3 — Crear usuario (POST /api/users)

CUANDO el Admin autenticado hace POST a `/api/users` con un body JSON válido
(`username`, `password`, `full_name`, `document`, `role`), el sistema DEBE:
- Verificar que `username` no exista. SI existe ENTONCES 409.
- Verificar que `role` sea uno de: `admin`, `operator`, `corresponsal`.
  SI no ENTONCES 422.
- Verificar que `full_name` no esté vacío. SI está vacío ENTONCES 422.
- Hashear `password` con bcrypt antes de almacenar.
- Crear el registro con `is_active=True` por defecto.
- Devolver 201 con el usuario creado (sin `password_hash`).

## R4 — Actualizar usuario (PUT /api/users/{id})

CUANDO el Admin autenticado hace PUT a `/api/users/{id}` con un body JSON
que puede incluir `full_name`, `document`, `role`, `is_active`
y opcionalmente `new_password`, el sistema DEBE:
- Actualizar solo los campos enviados (merge parcial).
- SI `new_password` está presente, hashearlo con bcrypt y actualizar
  `password_hash`.
- SI `role` cambia, validar que sea uno de los valores permitidos. SI no, 422.
- SI el `id` no existe ENTONCES 404.
- Devolver el usuario actualizado (sin `password_hash`).

## R5 — Desactivar usuario (DELETE /api/users/{id})

CUANDO el Admin autenticado hace DELETE a `/api/users/{id}`, el sistema DEBE:
- Establecer `is_active = False` en la base de datos.
- NO eliminar el registro físicamente.
- SI el `id` no existe ENTONCES 404.
- SI el usuario ya está inactivo, la operación DEBE ejecutarse sin error
  (idempotente).
- Devolver el usuario actualizado con `is_active=False` (sin `password_hash`).

## R6 — Control de acceso: solo Admin

MIENTRAS el usuario autenticado tenga rol distinto de `admin`,
el sistema DEBE rechazar cualquier endpoint de `/api/users/*` con 403
"Insuficient permissions".

## R7 — Control de acceso: sin token

SI no hay token JWT en la cabecera `Authorization` ENTONCES el sistema DEBE
rechazar cualquier endpoint de `/api/users/*` con 401 "Not authenticated".

## R8 — Validación de campos en creación

SI el body de `POST /api/users` contiene campos inválidos (username vacío,
password vacío, role inválido, nombres faltantes) ENTONCES el sistema DEBE
responder 422 con detalle del error.
