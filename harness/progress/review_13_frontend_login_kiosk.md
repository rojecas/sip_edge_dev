# Review — feature 13 (frontend_login_kiosk)

**Veredicto:** CHANGES_REQUESTED

## Resumen

Se reviso la implementacion completa de Feature 13 (Fase 9: T36-T43). Se encontraron:
- 1 CRITICAL regression re-introducida (KioskForm.svelte —  + '$derived(emergencyStore.isEmergencyMode)' + @)
- Cobertura de tests de frontend limitada para algunos R<n>
- Tests de backend y frontend (Feature 13) pasan

---

## 1. Trazabilidad requirements <-> tests

### R1-R42 (antes de Fase 9)
La mayoria de los requirements estan cubiertos por tests de backend o por verificacion de existencia de componentes. Los que NO tienen test concreto:
- R1 (modal login sin JWT), R2 (redirect por rol), R10 (boton logout visible), R11 (logout con confirmacion), R12 (inactividad), R14 (formulario campos), R15 (boton Leer REXT), R16 (boton Tara TARE), R18 (WS reconexion), R29 (Bearer token), R30 (Enter submit), R31 (username header), R33 (admin placeholder), R34 (logout limpia localStorage), R35 (WS tiempo real), R36 (FastAPI sirve SPA), R41 (JWT invalido), R42 (submit deshabilitado si vacio)

Muchos de estos estan *implementados* en componentes pero no tienen tests automatizados (solo verificacion manual o componente existe).

**Nota:** Hay precedente de revision previa (2026-06-18) que aprobo con esta misma cobertura. No es blocker absoluto pero queda documentado.

### R43 (POST /api/scale/command) — Cobertura completa
- tests/test_scale_api.py — 5 tests: REXT ok, TARE ok, unknown cmd 400, disconnect 503, timeout 503

### R44 (Auto-capture PRINT) — Cobertura
- frontend/src/components/__tests__/KioskForm.test.js — test "muestra notificacion temporal al recibir peso sin campo con foco"

### R45 (ScaleReader sin cambios) — Verificado
- ScaleReader.svelte no fue modificado. Usa  + '$scaleStore' + @ correctamente.

---

## 2. Tasks completas

- [x] T36 — src/scale_api.py creado
- [x] T37 — tests/test_scale_api.py (5 tests)
- [x] T38 — WeightField.svelte modificado (REXT/TARE via API)
- [x] T39 — ws.js exporta onScaleReading callback
- [x] T40 — KioskForm.svelte auto-capture PRINT
- [x] T41 — Tests para auto-capture PRINT
- [x] T42 — SCALE_COMMAND endpoint en constants.js
- [x] T43 — Build y verificacion

Todas las tasks de Fase 9 estan completas [x].

---

## 3. CRITICAL — Regression re-introducida en KioskForm.svelte

**Archivo:** frontend/src/components/KioskForm.svelte
**Linea 41:**  + "let isEmergencyMode = " + $derived(emergencyStore.isEmergencyMode); + "" + @
**Template (lineas 381-383):**  + "disabled={!isEmergencyMode}" + @

**Problema:** Esto es EXACTAMENTE el mismo bug que fue diagnosticado y corregido el 2026-06-18 como "Regression 2: CRITICAL". La correccion original (aprobada en review_frontend_login_kiosk.md) elimino esta linea y uso  + "$emergencyStore" + @ directamente en el template con  + "disabled={!}" + @.

**Razon por la que esta roto:**
- emergencyStore.isEmergencyMode es un getter que llama get(_isEmergencyMode) internamente
- () en Svelte 5 runes NO puede trackear get() de svelte/store como dependencia reactiva
- Cuando _isEmergencyMode.set(v) se ejecuta (via polling EmergencyBanner), isEmergencyMode NO se actualiza
- El disabled prop en WeightField queda congelado en su valor inicial

**Regresion introducida en:** Fase 9 (T38-T43 modifications to KioskForm.svelte agregaron el onScaleReading callback, pero la linea  + "let isEmergencyMode" + @ persistio o fue re-introducida).

**R afectados:** R24 (campos editables en modo emergencia), R25 (campos NO editables en modo normal)

**Fix requerido:**
1. Eliminar linea 41:  + "let isEmergencyMode = (emergencyStore.isEmergencyMode);" + @
2. Cambiar  + "disabled={!isEmergencyMode}" + @ a  + "disabled={!}" + @ en las 3 instancias de WeightField (lineas 381-383)
3. En handleConfirm() (linea 249), isEmergencyMode ya se usa dentro de callback — reemplazar con get(emergencyStore) o usar variable local

---

## 4. Escalabilidad del store scaleStore

**Archivo:** frontend/src/lib/ws.js

- scaleStore es un derived() de svelte/store — tiene subscribe, funciona correctamente
- onScaleReading(callback) exportado
- _onScaleReading invocado en onmessage tras actualizar store
- Sin / en archivo .js (cumple skill svelte5)

---

## 5. src/scale_api.py — revision

- Docstring de modulo
- Modelo Pydantic ScaleCommandRequest con command: str y value: str | None
- Dependencia get_scale_service() obtiene de app.state
- Manejo de errores: ScaleProtocolError 400, ScaleConnectionError/ScaleTimeoutError 503
- Integrado en src/main.py via app.include_router(scale_router)

---

## 6. Pruebas

### Backend (test_scale_api.py): 5/5 pasan

### Frontend (KioskForm + WeightField): 7/7 pasan

### init.ps1
- Secciones 1-5: todos [OK]
- Seccion 6 (tests): timeout (Docker)

### Pre-existing failures NOT related to F13:
- test_emergency_mode.py TestFullPipelineV2 — 3 tests FAIL (get_user_role_by_phone missing in SmsPersistenceService)
- AdminUsers.test.js, UserFormModal.test.js — 22 failures pre-existing

---

## 7. Skills consultados

- [x] skill svelte5 respetado — stores .js usan writable/derived, templates .svelte usan 
- [x] get() solo usado en callbacks (emergencyStore en handleConfirm)
- [x] onMount/onDestroy importados de "svelte"

**EXCEPCION:** La linea 41 (emergencyStore.isEmergencyMode) VIOLA el skill svelte5 — get() dentro de  no es reactivo.

---

## 8. Cambios requeridos (antes de aprobar)

### CRITICAL
1. **KioskForm.svelte:** Eliminar linea 41 ( + "let isEmergencyMode = (emergencyStore.isEmergencyMode)" + @). Cambiar  + "disabled={!isEmergencyMode}" + @ a  + "disabled={!}" + @ en las 3 instancias de WeightField. En handleConfirm() (linea 249), reemplazar isEmergencyMode con get(emergencyStore).

---

## 9. Checkpoints

- C1: [x] harness completo
- C2: [x] estado coherente
- C3: [x] respeta arquitectura
- C4: [x] tests existen y pasan
- C7: [x] SDD spec + tasks
- C11: [ ] No aplica (feature)

## 10. Release

- [ ] Requiere closure.md tras aprobacion

---

## Re-review after regression fix (2026-07-09)

**Veredicto:** APPROVED

### Verificaciones

| Check | Estado | Detalle |
|-------|--------|---------|
| Linea `$derived(emergencyStore.isEmergencyMode)` eliminada | ✅ | No existe en el archivo. Linea 41 original eliminada. |
| Template usa `disabled={!$emergencyStore}` (3 instancias) | ✅ | Lineas 379, 380, 381: correcto `disabled={!$emergencyStore}` |
| `handleConfirm()` usa `get(emergencyStore)` | ✅ | Linea 247: `manual_entry: get(emergencyStore),` |
| `import { get } from "svelte/store"` presente | ✅ | Linea 8 |
| `npm run build` — 0 errores | ✅ | `✓ built in 1.79s` — 0 errors |

### Resolucion

El fix aplicado coincide exactamente con lo requerido en la revision previa (seccion 3). La regresion CRITICA (R24/R25) queda corregida.

**La feature esta lista para cierre.**