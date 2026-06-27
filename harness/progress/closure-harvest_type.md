# Cierre — harvest_type (Feature 18)

## Resumen

Se implementó el campo 	ipo_cosecha en el registro de pesaje con 6 valores ENUM:
Manual - Incendio, Manual - Quemado, Manual - Verde, Mecanico - Incendio, Mecanico - Verde, No convencional - Verde. Default: Mecanico - Verde.

## Archivos creados

| Archivo | Propósito |
|---------|-----------|
| database/migrations/2026_06_25_000001_add_tipo_cosecha_to_weighings.sql | Migración ALTER TABLE |
| rontend/src/lib/constants.js | Constante HARVEST_TYPES |

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| src/models.py | Columna tipo_cosecha ENUM en Weighing |
| src/weighings.py | Schemas + validación + RS232 incluye tipo_cosecha |
| src/main.py | Query param tipo_cosecha en GET /api/anomalies |
| src/anomaly_detector.py | Filtro tipo_cosecha en detect_on_demand y _get_window |
| src/sql_tools.py | Filtro tipo_cosecha en 11 herramientas + tool_definitions |
| rontend/src/components/KioskForm.svelte | Select Tipo de Cosecha |
| rontend/src/components/HistoryTable.svelte | Columna Tipo Cosecha |
| 	ests/test_weighings.py | 4 tests nuevos |
| 	ests/test_anomaly_detector.py | 1 test nuevo |

## Trazabilidad

- R1-R3 (columna + valores + default): test_create_weighing_default_tipo_cosecha, test_create_weighing_explicit_tipo_cosecha, test_create_weighing_invalid_tipo_cosecha
- R4 (select kiosco): KioskForm.svelte + test frontend
- R5 (persistencia): test_create_weighing_explicit_tipo_cosecha
- R6-R8 (filtro anomalías): test_detect_on_demand_filter_tipo_cosecha
- R9 (historial): HistoryTable.svelte
- R10 (RS232): weighings.py incluye tipo_cosecha en frame_data
- R11 (migración): archivo SQL creado

## Verificación

- [x] 71 tests, 0 regresiones
- [x] Review aprobado
- [x] Feature registrada en tracker.json
- [x] feature_list.json status = done

## Release

- [x] Feature registrada como pendiente en tracker.json para próximo release
