# Plan: Bug #40 — session_timeout_mide_edad_no_inactividad

## Sintoma
El timeout de sesion mide la edad del token JWT (now - iat), no la inactividad real del usuario. Los operadores son expulsados en medio de una medición aunque estén activamente usando el sistema, porque el timer corre desde el login y nunca se resetea. No hay endpoint de refresh token, y el InactivityGuard no monitorea eventos DOM.

## Causa raiz
1. `check_inactivity()` en `src/auth.py` (linea 133): calcula `elapsed_minutes = (now - current_user["iat"]) / 60.0` — esto mide cuánto tiempo pasó desde que se emitió el token, no desde la última acción del usuario.
2. No existe endpoint `POST /api/auth/refresh` para emitir un nuevo JWT con `iat` fresco.
3. `create_access_token()` no incluye `session_timeout_minutes` en el payload JWT, por lo que el frontend no conoce el timeout configurado.
4. `InactivityGuard.svelte` solo ejecuta un timer que compara `iat` con hora actual, sin escuchar eventos DOM del usuario.
5. `inactivity.js` usa el `iat` del JWT en vez de mantener un marcador de última actividad.

## Archivos implicados
| Archivo | Cambio |
|---------|--------|
| `src/auth.py` | `create_access_token()` incluir `session_timeout_minutes` en payload; nuevo endpoint `POST /api/auth/refresh`; request/response models |
| `src/main.py` | Registrar `auth_router` con el refresh endpoint |
| `frontend/src/components/InactivityGuard.svelte` | Reescribir con listeners DOM reales + refresh periódico vía API |
| `frontend/src/lib/inactivity.js` | Cambiar lógica para usar timestamp de última actividad, no `iat` |
| `frontend/src/lib/constants.js` | Añadir `ENDPOINTS.REFRESH` y `REFRESH_INTERVAL_MS` |
| `frontend/src/stores/auth.js` | Añadir método `refreshToken()` y store `lastActivity` |
| `tests/test_auth.py` | Añadir `TestRefreshToken` con 2 tests |

## Fix propuesto

### Backend

1. **`create_access_token()`** — añadir parámetro `session_timeout_minutes: int = 30` e incluirlo en el payload JWT como `session_timeout_minutes`.

2. **Nuevo endpoint `POST /api/auth/refresh`** — requiere autenticación (`get_current_user`), lee el `session_timeout_minutes` de `app.state.session`, y emite un nuevo token con el mismo `sub` y `role` pero con `iat` fresco.

3. **Exportar router** desde `auth.py` para montarlo en `main.py`.

### Frontend

4. **`InactivityGuard.svelte`**:
   - Escuchar eventos `mousedown`, `keydown`, `touchstart` en `document`.
   - Mantener timestamp de última actividad.
   - Timer periódico (ej. cada 60s) que: si `now - lastActivity > timeout`, llama `authStore.logout()`.
   - Si el token está próximo a expirar (ej. >80% del timeout), hacer refresh via API.
   - El timeout se lee de `authStore.jwtPayload.session_timeout_minutes`.

5. **`inactivity.js`** — función `checkInactivity(lastActivity, timeoutMinutes)` que compara el timestamp de última actividad contra el timeout, ya no usa `iat`.

6. **`auth.js`** — nuevo método `refreshToken()` que llama `POST /api/auth/refresh` y actualiza el token en el store.

7. **`constants.js`** — añadir `ENDPOINTS.REFRESH = "/api/auth/refresh"` y `CONFIG.REFRESH_INTERVAL_MS = 120000` (2 min).

## Plan de verificacion
1. Ejecutar `python -m unittest tests.test_auth.TestRefreshToken -v` — ambos tests deben pasar.
2. Ejecutar `python -m unittest discover -s tests -v` — todos los tests existentes deben seguir pasando.
3. Compilar frontend con `npm run build` en `frontend/` y copiar a `src/static/`.
4. Ejecutar `./init.ps1` — debe terminar con todos los checks [OK].
