# Tasks — auth_rbac

> Pasos discretos en orden de implementacion. Cada task referencia los R<n> que cubre.

---

## Fase 1: Base de datos

- [x] T1 — Crear `src/database.py`: construir `DATABASE_URL` desde variables de entorno,
  crear `engine` (SQLAlchemy) con driver `mysql+pymysql`, `SessionLocal`
  (sessionmaker), y dependencia `get_db`. Cubre: R18, R21.

- [x] T2 — Crear `src/models.py`: definir `Base` (DeclarativeBase) y clase `User`
  con todas las columnas de la tabla `users` (id, username, password_hash,
  full_name, document, role, is_active, created_at, updated_at). Cubre: R19.

## Fase 2: Autenticacion JWT

- [x] T3 — Crear `src/auth.py`: implementar `hash_password()` (passlib bcrypt),
  `verify_password()`, `create_access_token()` (python-jose HS256, payload con
  sub/role/iat), `decode_access_token()`. Leer `JWT_SECRET_KEY` de env var.
  Cubre: R2, R5, R25.

- [x] T4 — Anadir dependencias FastAPI en `src/auth.py`: `get_current_user`
  (extrae token con HTTPBearer, decodifica, devuelve `{user_id, role, iat}`),
  `require_role(role)` (factory que comprueba rol), `check_inactivity`
  (comprueba `now - iat > timeout` usando `app.state.session`). Cubre: R7, R8,
  R9, R10, R11, R12, R13, R17.

## Fase 3: Configuracion de sesion

- [x] T5 — Anadir `SessionConfig` dataclass en `src/config.py` (frozen=True, campo
  `session_timeout_minutes: int`), constante `DEFAULT_SESSION_TIMEOUT_MINUTES = 15`.
  Cubre: R22.

- [x] T6 — Modificar `load_config` en `src/config.py` para que retorne
  `tuple[SystemConfig, SessionConfig]`, leyendo la seccion `session` de
  config.yaml con fallback a default. Adaptar `save_config` para que sea
  `save_system_config` (solo seccion system). Anadir `save_session_config`
  para persistir solo la seccion `session` con atomicidad (temp file +
  `os.replace`), preservando el resto de secciones. Cubre: R14, R23, R24.

## Fase 4: Seed de admin

- [x] T7 — Crear `src/seed.py`: implementar `seed_admin_user(db)` que inserte el
  usuario admin por defecto si la tabla `users` esta vacia. Leer
  `ADMIN_DEFAULT_PASSWORD` de env var con fallback `"admin"`. Cubre: R20, R25.

## Fase 5: Endpoints

- [x] T8 — Modificar `src/main.py` lifespan: cargar ambos configs (`app.state.config`,
  `app.state.session`), ejecutar `Base.metadata.create_all()`, invocar
  `seed_admin_user()`. Cubre: R18, R19, R20.

- [x] T9 — Anadir `POST /api/auth/login` en `src/main.py`: validar body, buscar
  usuario en DB, rechazar corresponsal (403), verificar password, devolver JWT.
  Cubre: R1, R3, R4, R6.

- [x] T10 — Anadir `PUT /api/setup/session` en `src/main.py` (protegido con
  `check_inactivity` + `require_role("admin")`): validar `session_timeout_minutes`
  > 0, persistir, devolver nuevo valor. Cubre: R15, R16.

- [x] T11 — Proteger endpoints existentes (`GET/PUT /api/config`,
  `POST /api/config/test/{port}`) con dependencias `check_inactivity` +
  `require_role("admin")`. Cubre: R11.

## Fase 6: Tests

- [x] T12 — Crear `tests/test_database.py`: `TestUserModel` (creacion de instancia,
  valores default, campos obligatorios), `TestSeedAdmin` (crea admin cuando
  tabla vacia, no duplica si ya existe), `TestHashPassword` (bcrypt roundtrip).
  Cubre: R5, R19, R20.

- [x] T13 — Crear `tests/test_auth.py` con `TestLoginEndpoint`: login valido
  (200 + token + role), credenciales invalidas (401), campos faltantes (422),
  corresponsal rechazado (403). Cubre: R1, R3, R4, R6.

- [x] T14 — Anadir `TestAuthDependencies` en `tests/test_auth.py`: token valido
  extrae user_id/role, token invalido/malformado (401), token sin claims
  requeridos (401). Cubre: R7, R8, R9.

- [x] T15 — Anadir `TestRBAC` en `tests/test_auth.py`: admin accede a
  `/api/config` (200), operator accede a `/api/config` (403), operator accede
  a `/api/weighing/test` (200 si endpoint existe). Cubre: R10, R11, R12.

- [x] T16 — Anadir `TestInactivity` en `tests/test_auth.py`: token recien
  emitido pasa inactivity check, token con iat antiguo (simulado) devuelve 401
  "Session expired". Cubre: R13, R17.

- [x] T17 — Anadir `TestSessionEndpoint` en `tests/test_auth.py`: admin
  actualiza timeout → 200, valor negativo → 422, sin token → 401, operator
  → 403. Cubre: R15, R16.

- [x] T18 — Ejecutar `docker compose exec backend python -m unittest discover -s
  tests -v` y verificar que todos los tests pasan. Cubre: todos.
