# Cierre — auth_rbac

- **Feature:** auth_rbac (id: 2)
- **Fecha:** 2026-06-13
- **Status final:** done

## Archivos creados/modificados

| Archivo | Accion |
|---------|--------|
| `src/database.py` | CREADO — SQLAlchemy engine, session, Base, init_db |
| `src/models.py` | CREADO — User model ORM (tabla users completa) |
| `src/auth.py` | CREADO — JWT, password hashing, get_current_user, require_role, check_inactivity |
| `src/seed.py` | CREADO — Seed admin inicial si tabla vacia |
| `src/config.py` | MODIFICADO — SessionConfig dataclass, load_config extendido a tuple |
| `src/main.py` | MODIFICADO — POST /api/auth/login, GET /api/auth/me, GET/PUT /api/setup/session, endpoints protegidos |
| `tests/test_auth.py` | CREADO — 30 tests (login, JWT, RBAC, inactivity) |
| `tests/test_database.py` | CREADO — 9 tests (modelo, seed, hashing) |
| `harness/init.ps1` | MODIFICADO — Step 6 usa Docker para tests cuando compose detectado |

## Decisiones tecnicas

1. **MariaDB** (no SQLite) — ya corriendo en compose.yml, SQLAlchemy + PyMySQL
2. **JWT HS256** con `python-jose`, secret via env var `JWT_SECRET_KEY`
3. **bcrypt** via `passlib[bcrypt]` para hashing
4. **Tabla users completa** (cubre features 2+3): username, password_hash, full_name, document, role, is_active
5. **Seed admin** automático si tabla vacía, password desde `ADMIN_DEFAULT_PASSWORD` (fallback: "admin")
6. **Timeout de inactividad** configurable via `PUT /api/setup/session` (solo admin), default 15 min
7. **Corresponsal** no puede hacer login (403)
8. **SessionConfig** en config.yaml sección `session`, atomic writes preservan otras secciones

## Verificacion

- `docker compose exec backend python -m unittest discover -s tests -v` → 60 tests OK
- `./init.ps1` → [OK] todos los bloques
- Reviewer APPROVED → `harness/progress/review_auth_rbac.md` (segunda revision)
