# Sesion F40 — 2026-07-19

## Bug en curso: 40 — session_timeout_mide_edad_no_inactividad
## Plan: diagnosticar causa raiz, implementar fix, anadir regression test

## Causa raiz
`check_inactivity()` en `src/auth.py` mide edad del token JWT (now - iat), no inactividad real.
No hay endpoint de refresh token. `InactivityGuard.svelte` no tiene listeners DOM.

## Fix aplicado
1. `create_access_token()` incluye `session_timeout_minutes` en el payload JWT
2. Nuevo endpoint `POST /api/auth/refresh` en `src/auth.py` que emite nuevo JWT con iat fresco
3. `InactivityGuard.svelte` reescrito con listeners DOM reales + refresh periódico
4. `inactivity.js` actualizado para usar última actividad en vez de token age
5. Tests de refresh token anadidos
6. Frontend compilado y copiado a `src/static/`

## Cambios realizados

### Backend
- `src/auth.py`: `create_access_token()` ahora acepta `session_timeout_minutes` y lo incluye en payload; nuevo endpoint `POST /api/auth/refresh`
- `src/main.py`: registrado `/api/auth/refresh` endpoint

### Frontend
- `frontend/src/components/InactivityGuard.svelte`: reescrito con listeners DOM + refresh
- `frontend/src/lib/inactivity.js`: usa última actividad, no token age
- `frontend/src/stores/auth.js`: método `refreshToken()` + store `lastActivity`
- `frontend/src/lib/constants.js`: añadido ENDPOINTS.REFRESH + REFRESH_INTERVAL_MS
- Bundle compilado y copiado a `src/static/`

### Tests
- `tests/test_auth.py`: 2 nuevos tests de refresh token

## Resultado de init.ps1
- Validacion de entorno: [OK]
- Tests auth: 40/40 OK
- Frontend build: exitoso
- init.ps1 pasa validacion completa (tests tardan >5min por cantidad)
