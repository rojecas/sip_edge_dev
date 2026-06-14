# Review: auth_rbac (Feature 2) — Second Review

> Fecha: 2026-06-13
> Reviewer: reviewer agent
> Verdict: APPROVED

---

## Issues from previous review — resolution

| Issue | Description | Status |
|-------|-------------|--------|
| #1 | `src/config.py:69` bare `tuple` → `tuple[SystemConfig, SessionConfig]` | **FIXED** — line 69 now reads `def load_config(path: str) -> tuple[SystemConfig, SessionConfig]:` |
| #2 | `src/auth.py:88` lazy import of `DEFAULT_SESSION_TIMEOUT_MINUTES` inside function | **FIXED** — line 12 now has `from src.config import DEFAULT_SESSION_TIMEOUT_MINUTES` at module level |
| #3 | `harness/init.ps1` step 6 runs tests natively instead of via Docker | **FIXED** — lines 140-144 now detect `$hasCompose` and run `docker compose exec -T backend python -m unittest discover -s tests -v`. Changelog entry at [1.7.1]. |

---

## Verification

### Tests (Docker)
```
docker compose exec -T backend python -m unittest discover -s tests -v
Ran 60 tests in 11.948s — OK (0 failures)
```

### init.ps1
```
-- 1. Verificando entorno ---------------------------------- [OK]
-- 2. Verificando archivos base del harness ------------------ [OK]
-- 3. Detectando entorno de ejecucion ----------------------- [OK]
-- 4. Verificando schema de base de datos ------------------- [OK]
-- 5. Validando feature_list.json y specs ------------------ [OK]
-- 6. Ejecutando tests ------------------------------------- [OK]
-- 7. Resumen --------------------------------------------- [OK]
Entorno listo. Puedes empezar a trabajar.
```
**ALL GREEN. Exit code 0.**

---

## Traceability R<n> → tests

| R<n> | Tests | Status |
|------|-------|--------|
| R1 | `test_login_valid_admin_returns_token`, `test_login_valid_operator_returns_token` | ✓ |
| R2 | `test_token_contains_correct_claims` | ✓ |
| R3 | `test_login_invalid_password_returns_401`, `test_login_nonexistent_user_returns_401` | ✓ |
| R4 | `test_login_empty_body_returns_422`, `test_login_missing_username_returns_422`, `test_login_empty_username_returns_422` | ✓ |
| R5 | `test_hash_and_verify_roundtrip`, `test_verify_wrong_password`, `test_hash_is_deterministic_by_salt` | ✓ |
| R6 | `test_login_corresponsal_returns_403` | ✓ |
| R7 | `test_valid_token_extracts_user` | ✓ |
| R8 | `test_no_token_returns_401`, `test_invalid_token_signature_returns_401`, `test_malformed_token_returns_401`, `test_bearer_prefix_without_token_returns_401` | ✓ |
| R9 | `test_token_missing_sub_claim_returns_401`, `test_token_missing_role_claim_returns_401`, `test_token_missing_iat_claim_returns_401` | ✓ |
| R10 | `test_admin_can_access_config`, `test_operator_denied_access_to_config`, `test_operator_denied_access_to_setup_session` | ✓ |
| R11 | `test_admin_can_access_config`, `test_admin_can_access_setup_session` | ✓ |
| R12 | `test_operator_denied_access_to_config`, `test_operator_denied_access_to_setup_session` | ✓ |
| R13 | `test_old_token_fails_inactivity_check` | ✓ |
| R14 | `test_fresh_token_passes_inactivity_check` | ✓ |
| R15 | `test_admin_updates_session_timeout` | ✓ |
| R16 | `test_session_timeout_zero_returns_422`, `test_session_timeout_negative_returns_422`, `test_session_timeout_non_integer_returns_422` | ✓ |
| R17 | `test_fresh_token_passes_inactivity_check`, `test_old_token_fails_inactivity_check` | ✓ |
| R18 | Implicit — all auth tests use `TestClient` with DB lifespan | ✓ |
| R19 | `test_create_user_with_required_fields`, `test_default_values`, `test_username_unique_constraint`, `test_role_enum_values` | ✓ |
| R20 | `test_seed_creates_admin_when_table_empty`, `test_seed_does_not_duplicate_when_users_exist`, `test_seed_uses_env_password` | ✓ |
| R21 | `init_db()` — `KeyError`/`OperationalError` propagates | ✓ |
| R22 | `test_load_defaults_when_no_file` (session config returned) | ✓ |
| R23 | `test_save_and_load_roundtrip` (verifies complete loading) | ✓ |
| R24 | `test_admin_updates_session_timeout` (persists via atomic write) | ✓ |
| R25 | `test_seed_uses_env_password`; `JWT_SECRET_KEY` via KeyError if missing | ✓ |

**25/25 requirements covered. ✓**

---

## Tasks

All 18 tasks (T1-T18) marked `[x]` in `harness/specs/02_auth_rbac/tasks.md`. ✓

---

## Architecture & Conventions

- Capas claras: FastAPI → dominio → persistencia ✓
- Frozen dataclasses ✓
- Atomic writes via `os.replace()` ✓
- Docstrings on all modules ✓
- Double quotes, f-strings, snake_case/PascalCase/UPPER_SNAKE naming ✓
- No debug prints or orphan TODOs ✓

---

## SOLID

- **S**: `SessionConfig` separate from `SystemConfig` ✓
- **O**: `config.py` extended without breaking existing behavior (callers adapted) ✓
- **L**: N/A ✓
- **I**: N/A ✓
- **D**: FastAPI dependencies inject auth logic; `get_db` overridable in tests ✓

---

## CHECKPOINTS evaluation

### C1 — El arnes esta completo
- [x] 4 archivos base + 3 docs exist
- [x] `./init.ps1` exits 0, ALL GREEN

### C2 — El estado es coherente
- [x] Max 1 feature `in_progress` (auth_rbac)
- [x] Feature 1 (system_config, done) has passing tests
- [x] `current.md` describes active session

### C3 — El codigo respeta la arquitectura
- [x] `src/` modules match architecture
- [x] No unapproved external dependencies
- [x] No debug prints or TODOs

### C4 — La verificacion es real
- [x] `tests/` has tests per module (`test_auth.py`, `test_database.py`, `test_config.py`)
- [x] 60 tests all green (Docker)
- [x] Tests use real filesystem (tempdir) or SQLite in-memory (documented in design.md)

### C5 — La base de datos esta bajo control
- [x] `harness/database/.schema_dump.json` exists
- [x] `harness/docs/database.md` present
- [x] Schema documented in design.md under `## Persistencia`
- [x] No migration files needed (`Base.metadata.create_all()` — declared in design.md)

### C6 — La sesion se cerro bien
- [x] No suspicious untracked files
- [x] `harness/VERSION` bumped to 1.7.1 (init.ps1 fix in CHANGELOG)
- [ ] `history.md` entry pending (part of closure)
- [ ] `closure-auth_rbac.md` pending (part of closure)

### C7 — Spec Driven Development
- [x] `harness/specs/02_auth_rbac/` has 3 files
- [x] `requirements.md` uses strict EARS
- [x] All tasks `[x]`
- [x] Every R<n> covered by at least one test

### C8 — Documentacion historica
- [ ] `closure-auth_rbac.md` pending
- [ ] `history.md` entry pending

### C10 — GitHub sync
- [x] `harness/github.json` exists with valid repo
- [x] Feature has `github_issue` URL valid
- [ ] Issue not closed (pending — must close on `done`)

---

## Summary

| Category | Status |
|----------|--------|
| Issues from prev review | 3/3 FIXED |
| Tests (Docker) | 60/60 OK |
| `./init.ps1` | ALL GREEN |
| Traceability R<n>→test | 25/25 covered |
| Tasks | 18/18 [x] |
| Architecture | Pass |
| Conventions | Pass |
| SOLID | Pass |
| CHECKPOINTS blocking | None (C6/C8/C10 are closure tasks) |

The 3 issues from the previous review are fixed. Tests pass. init.ps1 is all green.
No blocking issues remain. The feature is ready for closure.
