# Review — feature 44 (rs232_resend)

**Veredicto:** CHANGES_REQUESTED

## Trazabilidad requirements <-> tests

| R | Estado | Cobertura |
|---|--------|-----------|
| R1 | ⚠️ Débil | Backend: `test_resend_endpoint_returns_200`. Frontend: test mockea POST pero NO hace clic en Confirmar para verificar que botón cambia. |
| R2 | ✅ | `test_resend_endpoint_returns_200` (backend). Test frontend mockea pero no ejecuta flujo completo. |
| R3 | ✅ | `test_resend_multiple_times_allowed` (backend) |
| R4 | ❌ SIN COBERTURA | No existe `test_resend_mode_exits_on_tara_or_leer`. tasks.md T9 lista este test como requerido pero NO fue implementado. |
| R5 | ✅ | 6 tests backend cubren todas sub-responsabilidades |
| R6 | ✅ | `test_resend_count_defaults_to_zero_on_create` + migracion + modelo |
| R7 | ✅ | `test_resend_endpoint_increments_resend_count` |
| R8 | ✅ | HistoryTable test "admin ve boton reenvio cuando enviado_pc=false" |
| R9 | ✅ | HistoryTable test "operador no ve boton reenvio" |

## Tasks completas

- [x] T1 — Migracion ejecutada
- [x] T2 — Columna en modelo
- [x] T3 — Campo en schema
- [x] T4 — Endpoint /resend
- [x] T5 — Constante en constants.js
- [x] T6 — KioskForm.svelte
- [x] T7 — HistoryTable.svelte
- [x] T8 — 8 tests backend (OK)
- [ ] T9 — INCOMPLETO: Falta test_resend_mode_exits_on_tara_or_leer. 3 tests existentes fallan por mock issue.
- [x] T10 — 2 tests HistoryTable (OK)

## Checkpoints

### C1 — El arnes esta completo
- [x] Existen los 4 archivos base
- [x] Existen los 3 docs
- [ ] `./init.ps1` termino en TIMEOUT (no se pudo verificar verde)

### C2 — El estado es coherente
- [ ] Feature 44 NO esta registrada en feature_list.json (max ID es 40)
- [ ] Hay tests rojos en frontend (29 failures total)
- [x] progress/current.md describe la sesion activa

### C3 — El codigo respeta la arquitectura
- [x] Sin dependencias externas nuevas
- [x] Sin print() ni TODOs sin contexto
- [x] Respeta capas

### C4 — La verificacion es real
- [ ] Frontend tests con fallos (KioskForm: 10/10 fail; total 29/198 fail)
- [x] Backend tests OK (49/49 pass)

### C7 — Spec Driven Development
- [x] Carpeta specs/44_rs232_resend/ con 3 archivos
- [x] requirements.md usa EARS
- [x] tasks.md completa
- [ ] Cada R<n> cubierto por test: R4 NO tiene test directo

### C8 — Documentacion historica
- [ ] No existe closure-44_rs232_resend.md
- [ ] Feature no registrada en feature_list.json

### C10 — GitHub sync
- [ ] Feature no registrada -> no tiene github_issue

## Hallazgos

### 1. FALTA test para R4 (Tara/Leer sale de resendMode)
tasks.md T9 lista test_resend_mode_exits_on_tara_or_leer como requerido, pero NO fue implementado.
Archivo: frontend/src/components/__tests__/KioskForm.test.js
Evidence: Bloque describe "KioskForm - Feature 44: rs232_resend (R1, R2, R4)" solo tiene 3 tests, ninguno para Tara/Leer.

### 2. KioskForm tests fallan (10/10, incluyendo 3 de F44)
Todos los tests de KioskForm.test.js fallan con TypeError por falta de mock de emergencyStore.
Archivo: frontend/src/components/__tests__/KioskForm.test.js
Causa: disabled={!$emergencyStore} en WeightField no mockeado.

### 3. Feature 44 no registrada en feature_list.json
La feature 44 NO existe en harness/feature_list.json. El ID mas alto registrado es 40.
No se creo issue en GitHub, no se siguio flujo SDD correcto.

### 4. Migracion sin AFTER enviado_pc
design.md y tasks.md T1 especifican AFTER enviado_pc en ALTER TABLE, pero la migracion real no lo incluye.
Comparar con F37 (notas) que SI incluye AFTER tipo_cosecha.

### 5. Test R1 debil: no verifica cambio de boton
El test "boton Reenviar Datos aparece tras confirmar pesaje" mockea POST pero nunca hace clic en Confirmar.
Solo verifica que "Confirmar Medidas" existe en estado inicial.

## Cambios requeridos

1. Anadir test para R4: implementar test_resend_mode_exits_on_tara_or_leer que active resendMode, simule Tara/Leer, y verifique boton vuelve a Confirmar Medidas.

2. Mockear emergencyStore en KioskForm.test.js: agregar vi.mock("../../stores/emergency.js", ...) para que tests dejen de fallar.

3. Registrar Feature 44 en feature_list.json: agregar entrada con id=44, name=rs232_resend, status=in_progress, sdd=true, depends_on=[6, 11].

4. Corregir migracion: agregar AFTER enviado_pc en la migracion para mantener consistencia con spec.

5. Fortalezer test R1: hacer clic efectivo en Confirmar y verificar texto cambia a Reenviar Datos.
