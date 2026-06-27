# Spec — harvest_type (Feature 18)

## Resumen

Feature que agrega el campo `tipo_cosecha` (ENUM de 6 valores) a la tabla `weighings`, al formulario de pesaje del kiosco, al historial, y como filtro en el endpoint de anomalías.

## Archivos creados

- `harness/specs/18_harvest_type/requirements.md` — 11 requirements en EARS (R1-R11)
- `harness/specs/18_harvest_type/design.md` — Decisiones técnicas, persistencia, impacto en APIs, alternativas descartadas
- `harness/specs/18_harvest_type/tasks.md` — 23 tasks (T1-T23) organizadas en 8 fases

## Cobertura de Acceptance Criteria

| AC | Cobertura |
|----|-----------|
| AC1 (ENUM 6 valores) | R1, R2, R3 |
| AC2 (NOT NULL, default) | R1, R2, R6 |
| AC3 (select en kiosco) | R8 |
| AC4 (persistir en BD) | R4, R5, R6, R7, R9 |
| AC5 (filtro anomalies) | R10 |
| AC6 (columna historial) | R11 |

## Cambios en feature_list.json

Feature 18 `harvest_type`: `pending` → `spec_ready`
