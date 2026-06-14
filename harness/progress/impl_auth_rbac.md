# Implementacion: auth_rbac (Feature 2)

> Fecha: 2026-06-13
> Spec: `harness/specs/02_auth_rbac/`
> Estado: Tareas completadas. Esperando reviewer.

---

## Archivos creados

| Archivo | Proposito |
|---------|-----------|
| `src/database.py` | Conexion SQLAlchemy a MariaDB (`engine`, `SessionLocal`, `get_db`) |
| `src/models.py` | Modelo ORM `User` (tabla `users` completa) |
| `src/auth.py` | Funciones JWT, password hashing, dependencias FastAPI de auth |
| `src/seed.py` | `seed_admin_user()` — crea admin inicial si tabla vacia |
| `tests/test_database.py` | Tests de modelos, seed admin, password hashing |
| `tests/test_auth.py` | Tests de login, JWT, RBAC, inactividad, sesion |

## Archivos modificados

| Archivo | Cambios |
|---------|---------|
| `src/config.py` | Anadido `SessionConfig` dataclass, `load_config` retorna `tuple`, `save_system_config` + `save_session_config` atomicos |
| `src/main.py` | Lifespan con DB init + seed, `POST /api/auth/login`, `PUT /api/setup/session`, proteccion de endpoints existentes con auth |
| `compose.yml` | Anadidas variables `JWT_SECRET_KEY` y `ADMIN_DEFAULT_PASSWORD` |
| `tests/test_config.py` | Adaptados a nuevo `load_config` (retorna tuple) y override de auth dependencies |

---

## Trazabilidad (R<n> → tests)

| Requirement | Test(s) |
|-------------|---------|
| R1 (login valido) | `test_login_valid_admin_returns_token`, `test_login_valid_operator_returns_token` |
| R2 (JWT claims sub/role/iat + HS256) | `test_token_contains_correct_claims` |
| R3 (credenciales invalidas → 401) | `test_login_invalid_password_returns_401`, `test_login_nonexistent_user_returns_401` |
| R4 (body invalido → 422) | `test_login_empty_body_returns_422`, `test_login_missing_username_returns_422`, `test_login_empty_username_returns_422` |
| R5 (bcrypt hash, no plain text) | `test_hash_and_verify_roundtrip`, `test_verify_wrong_password`, `test_hash_is_deterministic_by_salt` |
| R6 (corresponsal → 403) | `test_login_corresponsal_returns_403` |
| R7 (get_current_user extrae token) | `test_valid_token_extracts_user` |
| R8 (sin token / invalido → 401) | `test_no_token_returns_401`, `test_invalid_token_signature_returns_401`, `test_malformed_token_returns_401`, `test_bearer_prefix_without_token_returns_401` |
| R9 (token sin claims → 401) | `test_token_missing_sub_claim_returns_401`, `test_token_missing_role_claim_returns_401`, `test_token_missing_iat_claim_returns_401` |
| R10 (require_role) | `test_admin_can_access_config`, `test_operator_denied_access_to_config`, `test_operator_denied_access_to_setup_session` |
| R11 (admin acceso total) | `test_admin_can_access_config`, `test_admin_can_access_setup_session` |
| R12 (operator restringido) | `test_operator_denied_access_to_config`, `test_operator_denied_access_to_setup_session` |
| R13 (inactividad → 401) | `test_old_token_fails_inactivity_check` |
| R14 (leer session_timeout de config) | `test_fresh_token_passes_inactivity_check` (usa default 15) |
| R15 (PUT /api/setup/session) | `test_admin_updates_session_timeout` |
| R16 (valor invalido → 422) | `test_session_timeout_zero_returns_422`, `test_session_timeout_negative_returns_422`, `test_session_timeout_non_integer_returns_422` |
| R17 (check_inactivity dependency) | `test_fresh_token_passes_inactivity_check`, `test_old_token_fails_inactivity_check` |
| R18 (conexion MariaDB + SQLAlchemy) | `src/database.py` init_db + lifespan (verificado con test_client en todos los tests de auth) |
| R19 (tabla users creada) | `test_create_user_with_required_fields`, `test_default_values`, `test_username_unique_constraint`, `test_role_enum_values` |
| R20 (seed admin inicial) | `test_seed_creates_admin_when_table_empty`, `test_seed_does_not_duplicate_when_users_exist`, `test_seed_uses_env_password` |
| R21 (DB falla → excepcion) | Implementado en `init_db()` — `KeyError`/`OperationalError` propaga |
| R22 (SessionConfig dataclass) | `test_load_defaults_when_no_file` (verifica retorno de session config) |
| R23 (load_config devuelve ambos) | `test_save_and_load_roundtrip` (verifica carga completa) |
| R24 (save_session_config atomico) | `test_admin_updates_session_timeout` (persiste y verifica) |
| R25 (JWT_SECRET_KEY + ADMIN_DEFAULT_PASSWORD de env) | `test_seed_uses_env_password` (ADMIN_DEFAULT_PASSWORD), `JWT_SECRET_KEY` leido en `src/auth.py` (KeyError si falta) |

---

## Decisiones tecnicas notables

1. **`check_same_thread: False` + `StaticPool` para tests con SQLite**: Necesario porque FastAPI ejecuta endpoints en thread pool. Sin `StaticPool`, cada conexion SQLite `:memory:` ve una BD separada.

2. **`HTTPBearer(auto_error=False)`**: Necesario para devolver 401 en lugar del default 403 cuando falta el header `Authorization`.

3. **`BigInteger().with_variant(Integer, "sqlite")`**: `BigInteger` con `autoincrement=True` en SQLite requiere tipo `Integer` para funcionar correctamente con RETURNING.

4. **`save_config` mantenido como wrapper backward-compatible**: `tests/test_config.py` lo usa directamente. Internamente delega en `save_system_config`.

5. **`load_config` rompe compatibilidad**: Cambia de `SystemConfig` a `tuple[SystemConfig, SessionConfig]`. Los callers (`lifespan`, `test_config.py`) fueron actualizados.

---

## Verificacion

```bash
# Dentro del contenedor Docker:
docker compose exec backend python -m unittest discover -s tests -v
# Resultado: Ran 60 tests in ~12s — OK (0 failures)
```

---
