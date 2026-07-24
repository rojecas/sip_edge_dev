# Review — feature 44 (rs232_resend) — v2

**Veredicto:** APPROVED

## Hallazgos del review anterior — Re-verificación

| # | Hallazgo | Estado | Evidencia |
|---|----------|--------|-----------|
| 1 | Falta test para R4 (Tara/Leer sale de resendMode) | ✅ CORREGIDO | `KioskForm.test.js:365-455` — test `modo reenvio se desactiva al presionar Tara o Leer`. Llena formulario, confirma, presiona Tara, verifica botón vuelve a "Confirmar Medidas". |
| 2 | Mock emergencyStore falla (10/10 KioskForm tests rojos) | ✅ CORREGIDO | `KioskForm.test.js:61-70` — `subscribe` ahora llama callback con `false` y retorna `() => {}`. Los 11 tests de KioskForm pasan. |
| 3 | Migración sin `AFTER enviado_pc` | ✅ CORREGIDO | `database/migrations/2026_07_23_000001_add_resend_count_to_weighings.py:14` — incluye `AFTER enviado_pc`. |
| 4 | Feature 44 no registrada en feature_list.json | ✅ YA EXISTE | `feature_list.json:927-949` — entrada completa con `id:44`, `status:in_progress`, `github_issue`. |
| 5 | Test R1 débil (no hacía clic en Confirmar) | ✅ CORREGIDO | `KioskForm.test.js:263-340` — ahora llena campos, hace clic efectivo en "Confirmar Medidas", verifica botón cambia a "Reenviar Datos". |

## Trazabilidad requirements <-> tests

| R | Estado | Cobertura |
|---|--------|-----------|
| R1 | ✅ | `boton Reenviar Datos aparece tras confirmar pesaje` (KioskForm.test.js) — clic en Confirmar + verifica "Reenviar Datos" |
| R2 | ✅ | `test_resend_endpoint_returns_200` (backend) + `boton Reenviar Datos aparece tras confirmar pesaje` (frontend) |
| R3 | ✅ | `test_resend_multiple_times_allowed` (backend) — 3 llamadas seguidas, todas 200 |
| R4 | ✅ | `modo reenvio se desactiva al presionar Tara o Leer` (KioskForm.test.js) — simula Tara tras confirmar, verifica retorno a "Confirmar Medidas" |
| R5 | ✅ | 6 tests backend cubren todas sub-responsabilidades (200, 404 not found, 404 operator ajeno, no anomalías, enviado_pc, estructura) |
| R6 | ✅ | `test_resend_count_defaults_to_zero_on_create` (backend) + migración + modelo |
| R7 | ✅ | `test_resend_endpoint_increments_resend_count` (backend) |
| R8 | ✅ | `admin ve boton reenvio cuando enviado_pc=false` (HistoryTable.test.js) |
| R9 | ✅ | `operador no ve boton reenvio` (HistoryTable.test.js) |

## Tasks completas

- [x] T1 — Migración con `AFTER enviado_pc`
- [x] T2 — Columna `resend_count` en modelo
- [x] T3 — Campo `resend_count` en schema
- [x] T4 — Endpoint `POST /api/weighings/{id}/resend`
- [x] T5 — Constante en constants.js
- [x] T6 — KioskForm.svelte (resendMode, handleResend, exitResendMode, botón condicional)
- [x] T7 — HistoryTable.svelte (columna Acción + botón 🔄 admin-only)
- [x] T8 — 8 tests backend (todos OK)
- [x] T9 — 3 tests frontend KioskForm + 1 test R4 adicional (todos OK)
- [x] T10 — 2 tests frontend HistoryTable (todos OK)

## Checkpoints

### C1 — El arnés está completo
- [x] Existen los 4 archivos base
- [x] Existen los 3 docs
- [ ] `./init.ps1` timeout en step 6 (misma limitación de entorno Docker; tests individuales corren verde)

### C2 — El estado es coherente
- [x] Solo F44 en `in_progress`
- [x] `current.md` describe la sesión activa correctamente
- [x] F44 correctamente registrada en feature_list.json

### C3 — Código respeta arquitectura
- [x] Sin dependencias externas nuevas
- [x] Sin `print()` ni TODOs sin contexto
- [x] Respeta capas (CLI → modelo → persistencia)
- [x] Respeta SOLID (endpoint único, responsabilidad única)

### C4 — Verificación real
- [x] Backend tests: 49/49 pasan (todos los resend tests OK)
- [x] Frontend tests F44: 6/6 pasan (KioskForm 4 + HistoryTable 2)
- [x] 19 fallos pre-existentes no relacionados con F44 (AdminBackup, AdminConfig, AdminHaciendas, AdminUsers, UserFormModal — mismos fallos heredados, no introducidos por F44)

### C7 — Spec Driven Development
- [x] Carpeta `specs/44_rs232_resend/` con 3 archivos
- [x] `requirements.md` usa EARS estricto
- [x] `tasks.md` completa con todos `[x]`
- [x] Cada R1-R9 cubierto por al menos un test concreto

### C8 — Documentación histórica
- [ ] No existe closure (feature en `in_progress`, no procede)
- [x] Feature registrada con estado correcto

### C10 — GitHub sync
- [x] `github.json` existe con `enabled: true`
- [x] F44 tiene `github_issue: "https://github.com/rojecas/sip_edge/issues/27"`
- [x] Issue #27 existe y está OPEN (correcto para `in_progress`)

## Documentación requerida por protocolo

### Skills consultados
- [x] `svelte5` documentado en `impl_44_rs232_resend_fixes.md:7` y `impl_44_rs232_resend.md:5`

### Impacto en features existentes
- [x] Documentado en ambos impl files — ninguno, solo migración, schema y tests

## Resultado de tests

```
# Backend (Docker):
Ran 49 tests in 66.174s
OK

# Frontend KioskForm (F44):
✓ muestra boton Confirmar Medidas al cargar
✓ boton Reenviar Datos aparece tras confirmar pesaje
✓ limpia modo reenvio al presionar Limpiar todo
✓ modo reenvio se desactiva al presionar Tara o Leer

# Frontend HistoryTable (F44):
✓ muestra boton de reenvio para admin cuando enviado_pc es false
✓ no muestra boton de reenvio para operador

# Total frontend: 180 passed, 19 failed (pre-existentes)
# Total backend: 49 passed, 0 failed
```

## Conclusión

Los 5 hallazgos del review anterior fueron corregidos satisfactoriamente. Todos los tests de F44 (backend + frontend) pasan. La trazabilidad R1-R9 es completa y verificable. La documentación requerida (skills consultados, impacto en features existentes) está presente. GitHub sync operativo (issue #27 existe y está abierto). No se detectaron regresiones en features existentes.

**APPROVED** — La feature está lista para transicionar a `testing`.
