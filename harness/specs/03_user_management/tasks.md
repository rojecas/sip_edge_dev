# Tasks — Gestión de Usuarios (CRUD)

> Implementar en orden. Cada task referencia los requirements que cubre.

- [x] T1 — Crear `src/users.py` con:
  - Schemas Pydantic: `UserCreate`, `UserUpdate`, `UserResponse`.
  - Funciones internal API: `list_users`, `get_user`, `create_user`, `update_user`, `deactivate_user`.
  - `router = APIRouter(prefix="/api/users")` con 5 endpoints.
  - Cada endpoint protegido con `Depends(check_inactivity)` + `Depends(require_role("admin"))`.
  - Password hasheado con `hash_password()` de `src/auth.py`.
  - Excepciones 404 para ID inexistente, 409 para username duplicado.
  - Cubre: R1, R2, R3, R4, R5, R6, R7, R8.

- [x] T2 — Registrar el router en `src/main.py`:
  - `from src.users import router as users_router`
  - `app.include_router(users_router)`
  - Cubre: R1, R2, R3, R4, R5.

- [x] T3 — Crear `tests/test_users.py` con SQLite in-memory (mismo patrón que `test_auth.py`):
  - `test_list_users_as_admin` — GET /api/users devuelve lista. Cubre: R1.
  - `test_list_users_without_token` — 401. Cubre: R7.
  - `test_list_users_as_operator` — 403. Cubre: R6.
  - `test_get_user_by_id` — GET /api/users/{id} devuelve usuario. Cubre: R2.
  - `test_get_user_not_found` — 404. Cubre: R2.
  - `test_create_user_valid` — POST /api/users devuelve 201. Cubre: R3.
  - `test_create_user_duplicate_username` — 409. Cubre: R3.
  - `test_create_user_invalid_role` — 422. Cubre: R8.
  - `test_create_user_empty_name` — 422. Cubre: R8.
  - `test_update_user_fields` — PUT /api/users/{id} actualiza campos. Cubre: R4.
  - `test_update_user_password` — PUT con new_password hashea correctamente. Cubre: R4.
  - `test_update_user_not_found` — 404. Cubre: R4.
  - `test_deactivate_user` — DELETE /api/users/{id} pone is_active=False. Cubre: R5.
  - `test_deactivate_user_already_inactive` — idempotente, sigue siendo 200. Cubre: R5.
  - `test_deactivate_user_not_found` — 404. Cubre: R5.
  - `test_create_user_password_hashed` — Verificar que password_hash != password plano. Cubre: R3.

- [x] T4 — Verificar con `./init.ps1` que todo pasa y el entorno está sano.
