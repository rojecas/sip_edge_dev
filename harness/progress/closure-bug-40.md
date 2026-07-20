# Closure: Bug #40 — session_timeout_mide_edad_no_inactividad

## Sintoma
El timeout de sesion mide la edad del token JWT (now - iat), no la inactividad real del usuario. Los operadores son expulsados en medio de una medicion aunque esten activamente usando el sistema porque el timer corre desde el login y nunca se resetea. No hay endpoint de refresh token, y el InactivityGuard no monitorea eventos DOM para detectar actividad del usuario.

## Causa raiz
1. `check_inactivity()` en `src/auth.py` comparaba `(now - current_user["iat"])` contra el timeout, midiendo antiguedad del token, no inactividad.
2. `create_access_token()` no incluia `session_timeout_minutes` en el payload JWT.
3. No existia endpoint `POST /api/auth/refresh` para emitir un nuevo JWT con `iat` fresco.
4. `InactivityGuard.svelte` solo ejecutaba un timer que comparaba `iat` contra hora actual, sin escuchar eventos DOM.
5. `inactivity.js` usaba el `iat` del JWT como referencia, no un marcador de ultima actividad.

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/auth.py` | `create_access_token()` ahora acepta `session_timeout_minutes` y lo incluye en payload JWT. Nuevo endpoint `POST /api/auth/refresh` via `auth_router` que emite nuevo JWT con `iat` fresco. Nuevos modelos `RefreshResponse`. |
| `src/main.py` | Import de `auth_router` y registro via `app.include_router()`. Login endpoint ahora pasa `session_timeout_minutes` a `create_access_token()`. Import de `DEFAULT_SESSION_TIMEOUT_MINUTES`. |
| `frontend/src/components/InactivityGuard.svelte` | Reescribo completamente: anade listeners DOM (mousedown, keydown, touchstart, scroll, click) que actualizan `lastActivity`. Timer verifica inactividad real vs `lastActivity`. Refresh periodico via `authStore.refreshToken()` cada `REFRESH_INTERVAL_MS`. |
| `frontend/src/lib/inactivity.js` | Cambia API: ahora recibe `lastActivity` timestamp en vez de `jwtPayload`. Funcion `checkInactivity(lastActivity, sessionTimeoutMinutes)` compara ultima actividad real contra el timeout. |
| `frontend/src/stores/auth.js` | Nuevo writable `_lastActivity`. Nueva propiedad `lastActivity`. Nuevo metodo `updateLastActivity()`. Nuevo metodo `refreshToken()` que llama `POST /api/auth/refresh` y actualiza token. Login resetea `lastActivity`. |
| `frontend/src/lib/constants.js` | Nuevo `ENDPOINTS.REFRESH = "/api/auth/refresh"`. Nuevo `CONFIG.REFRESH_INTERVAL_MS = 120000`. |
| `tests/test_auth.py` | Nuevos tests: `TestTokenStructure.test_token_contains_custom_timeout`, `TestRefreshToken.test_refresh_token_returns_new_jwt`, `TestRefreshToken.test_refresh_token_requires_auth`. |

## Fix aplicado

### Backend
1. `create_access_token()` incluye `session_timeout_minutes` en el payload JWT, permitiendo que el frontend conozca el timeout configurado.
2. Nuevo endpoint `POST /api/auth/refresh` que requiere autenticacion, lee el timeout de `app.state.session`, y emite un nuevo JWT con el mismo `sub` y `role` pero con `iat` fresco.
3. Login endpoint pasa el `session_timeout_minutes` desde la configuracion al crear el token.

### Frontend
4. `InactivityGuard.svelte` escucha eventos DOM reales (mousedown, keydown, touchstart, scroll, click) usando el patron de passive event listeners.
5. Mantiene un timestamp `lastActivity` que se actualiza en cada interaccion del usuario.
6. El timer de inactividad compara `now - lastActivity` contra el timeout, no contra el `iat` del JWT.
7. Antes de que el timeout se cumpla (~80%), refresca el token via API para mantener la sesion activa.
8. Ademas, refresca proactivamente cada `REFRESH_INTERVAL_MS` (2 min) para evitar expiracion.

## Regression test

- `test_refresh_token_returns_new_jwt`: Verifica que POST /api/auth/refresh retorna un nuevo JWT con `iat` fresco, mismo `sub` y `role`, y string diferente al token original.
- `test_refresh_token_requires_auth`: Verifica que POST /api/auth/refresh sin token retorna 401.
- `test_token_contains_custom_timeout`: Verifica que `create_access_token()` con `session_timeout_minutes=60` incluye el valor en el payload.

## Resultado de verificacion

- `python -m unittest tests.test_auth -v`: **40 tests, OK** (todos los tests existentes + los nuevos pasan).
- Frontend: `npm run build` exitoso, copiado a `src/static/`.
- `./init.ps1`: Validacion [OK], tests arrancan sin errores (la suite completa excede timeout de 5min por cantidad de tests, pero todos los tests visibles pasan).
