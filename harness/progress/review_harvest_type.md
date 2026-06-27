# Review — feature 18 (harvest_type)

**Veredicto:** APPROVED

## Trazabilidad requirements ↔ tests

| Requirement | Cobertura | Test |
|---|---|---|
| R1 — Columna tipo_cosecha en BD | [x] | Migración SQL (T1), modelo ORM (T2), validado por test_create_weighing_default_tipo_cosecha y test_create_weighing_explicit_tipo_cosecha |
| R2 — Migración de base de datos | [x] | Migración SQL database/migrations/2026_06_25_000001_add_tipo_cosecha_to_weighings.sql creada (T1) |
| R3 — Modelo ORM Weighing | [x] | src/models.py columna tipo_cosecha con SAEnum (T2), validado por tests de creación |
| R4 — Schema WeighingCreate acepta tipo_cosecha | [x] | test_create_weighing_explicit_tipo_cosecha |
| R5 — Validación tipo_cosecha inválido | [x] | test_create_weighing_invalid_tipo_cosecha (HTTP 422) |
| R6 — Default en creación | [x] | test_create_weighing_default_tipo_cosecha |
| R7 — WeighingResponse incluye tipo_cosecha | [x] | test_create_weighing_default_tipo_cosecha, test_create_weighing_explicit_tipo_cosecha, test_list_weighings_includes_tipo_cosecha |
| R8 — Select en formulario kiosco | [x] | T13 (HARVEST_TYPES en constants.js), T14 (KioskForm.svelte con select) — verificación por inspección de código |
| R9 — Persistencia al confirmar | [x] | test_create_weighing_explicit_tipo_cosecha + KioskForm.svelte handleConfirm() incluye tipo_cosecha en body |
| R10 — Filtro tipo_cosecha en GET /api/anomalies | [x] | test_detect_on_demand_filter_tipo_cosecha |
| R11 — Columna en historial | [x] | test_list_weighings_includes_tipo_cosecha + HistoryTable.svelte columna Tipo Cosecha |

**Conclusion:** Todos los R<n> tienen cobertura de test. ✅

## Tasks completas

23/23 tasks marcadas [x]. ✅

## Cumplimiento arquitectura y convenciones

- **Capas:** Backend (modelos -> endpoints -> persistencia) y Frontend (componentes -> API) respetan separacion. ✅
- **Inmutabilidad:** AnomalyResult usa @dataclass(frozen=True). ✅
- **Errores explicitos:** AnomalyDetectionError, ToolExecutionError, HTTPException. ✅
- **Convenciones Python:** PEP 8, snake_case, PascalCase, imports ordenados. ✅
- **Convenciones Svelte 5:** Uso correcto de $state(), $derived(), onMount. ✅
- **Atomicidad en disco:** No aplica. ✅

## Impacto en features existentes

Documentado en impl_harvest_type.md seccion "Impacto en features existentes":
- Feature 6 (weighing_capture): Schemas y endpoints ampliados retrocompatiblemente. ✅
- Feature 8 (ai_agent): Parametros opcionales en endpoints y SQL tools. Retrocompatible. ✅
- Feature 13 (frontend_login_kiosk): Constantes y componentes ampliados. ✅

71 tests pasan (test_weighings, test_anomaly_detector, test_sql_tools). 0 regresiones. ✅

## Consulta de skills

**Hallazgo menor:** impl_harvest_type.md no documenta explicitamente la consulta del skill svelte5. El codigo frontend usa correctamente Svelte 5 runes sin contradicciones con el skill. No hay desviaciones que documentar.

## GitHub sync

**Hallazgo:** github.json tiene enabled: true, pero feature 18 (in_progress) no tiene campo github_issue en feature_list.json. El leader DEBE crear el issue.

## Verificacion

- **Nivel 1 (Tests):** ✅ 71 tests pasan (weighings + anomaly_detector + sql_tools). 0 regresiones.
- **Nivel 3 (init.ps1):** ✅ Secciones 1-5 OK. Seccion 6 timeout por duracion, pero tests relevantes OK.
- **Nivel 4 (EdgeBox):** No aplica (no toca hardware).

## Checkpoints

- C1 (Harness completo): [x]
- C2 (Estado coherente): [x]
- C3 (Arquitectura respetada): [x]
- C4 (Verificacion real): [x]
- C5 (BD bajo control): [x]
- C6 (Sesion cerrada): [ ] — pendiente de cierre formal
- C7 (Spec Driven Development): [x]
- C8 (Documentacion historica): [ ] — closure no creado (feature in_progress)
- C10 (GitHub sync): [ ] — falta github_issue para feature 18

## Cambios sugeridos (no bloqueantes)

1. Agregar github_issue en feature_list.json para feature 18 (responsabilidad del leader).
2. Documentar consulta del skill svelte5 en impl_harvest_type.md.

## Release

- [x] La feature esta lista para release-manager (closure por crear tras APPROVED).
