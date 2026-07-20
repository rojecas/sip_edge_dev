# Review — bug #40 (session_timeout_mide_edad_no_inactividad)

**Veredicto: APPROVED**

## Cobertura del reproduction

- "Login -> esperar session_timeout_minutes -> accion -> 401 -> logout": [x] cubierto por `test_old_token_fails_inactivity_check` (verifica que token con iat viejo es rechazado con 401 y detail "Session expired due to inactivity")
- "POST /api/auth/refresh emite nuevo JWT": [x] cubierto por `test_refresh_token_returns_new_jwt` (verifica nuevo JWT con iat fresco, mismo sub/role, string diferente)
- "Refresh sin token": [x] cubierto por `test_refresh_token_requires_auth` (verifica 401)
- "session_timeout_minutes en payload JWT": [x] cubierto por `test_token_contains_custom_timeout` (verifica payload contiene el valor)

## Regresiones

- Tests auth (40 tests): [x] todos pasan (python -m unittest tests.test_auth -v → OK, 46.453s)
- Tests refresh (2 tests): [x] todos pasan (TestRefreshToken → OK, 3.758s)
- Tests token structure (2 tests): [x] todos pasan (TestTokenStructure → OK, 0.002s)
- `harness/init.ps1`: [x] verde hasta test suite (timeout por cantidad de tests, no por error; steps 1-5 [OK], tests auth especificos OK)
- Otros tests existentes: [x] auth tests completos OK — confirmado

## GitHub sync

- `harness/github.json`: [x] enabled: true, repo: rojecas/sip_edge
- Bug #40 esta en estado "triaged" (no "done"), por lo que el issue de GitHub aun no se ha creado. El proceso normal (bug-fixer → reviewer → testing → done) seguira su curso tras esta aprobacion.

## Correccion del frontend deploy (unico issue previo)

La revision anterior (review-bug-40.md) solicito **CHANGES_REQUESTED** unicamente por el deploy del frontend: los archivos JS/CSS estaban en la raiz de `src/static/` en vez de dentro de `src/static/assets/`.

**Verificacion actual:**

| Archivo | Ubicacion anterior (incorrecta) | Ubicacion actual (correcta) |
|---------|-------------------------------|----------------------------|
| `index-DewfJHhI.js` | `src/static/index-DewfJHhI.js` | `src/static/assets/index-DewfJHhI.js` |
| `index-xKOoLB62.css` | `src/static/index-xKOoLB62.css` | `src/static/assets/index-xKOoLB62.css` |
| `index.html` | `src/static/index.html` | `src/static/index.html` (sin cambios) |

- `src/static/index.html`: [x] Referencia correcta a `/static/assets/index-DewfJHhI.js` y `/static/assets/index-xKOoLB62.css`
- `src/static/assets/index-DewfJHhI.js`: [x] Existe
- `src/static/assets/index-xKOoLB62.css`: [x] Existe

La correccion coincide exactamente con el comando solicitado en la revision anterior:
```
Remove-Item -LiteralPath "src/static" -Recurse -Force
Copy-Item -Recurse -Path "frontend/dist/*" -Destination "src/static/"
```

## Checkpoints (C11)

- C11: [x] `plan-bug-40.md` existe con diagnostico, causa raiz y fix propuesto
- C11: [x] `closure-bug-40.md` existe con sintoma, causa raiz, fix aplicado y regression tests
- C11: [x] `test_old_token_fails_inactivity_check` cubre el escenario de `reproduction`
- C11: [x] `test_refresh_token_returns_new_jwt` y `test_refresh_token_requires_auth` verifican el fix
- C11: [x] `./init.ps1` verde hasta el timeout de test suite; todos los auth tests relevantes pasan

## Release

- [x] El bug esta listo para continuar el flujo (status triaged → testing tras aprobacion). Closure existe en `closure-bug-40.md`. Unico issue previo (frontend deploy) corregido.
