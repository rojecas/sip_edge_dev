# Implementación — Feature 33: sql_tools_v2

> Fecha: 2026-07-20
> Estado: **Completada** — 33/33 tasks [x]

## Skills consultados

- **svelte5** — Reglas de runes ($state, onMount), no usar $state en .js, mount() en vez de new App()
- **verification-before-completion** — Verificar tests antes de declarar done

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/sql_tools.py` | Agregar helpers _resolve_date_shortcut, _apply_vehicle_filter, _compute_period_label. Agregar 4 nuevas tools: get_avg_weighing_time, get_anomaly_rate, get_top_haciendas, get_period_comparison. Modificar get_basic_stats, get_breakdown_by_hacienda, get_custom_period_summary con agrupacion, tipo_vehiculo, periodo. Actualizar TOOL_DEFINITIONS (13→17) y tool_map. Modificar __init__ para aceptar agent_config. Modificar check_thresholds para usar agent_config. |
| `src/main.py` | Pasar agent_config al constructor de SqlTools. Agregar limites_control en GET /api/config. Agregar PUT /api/setup/controls endpoint con schema LimitesControlRequest. |
| `src/report_templates.py` | Agregar handler _metric_std registrado con @_register_metric("std"). |
| `src/sms_service.py` | Modificar generate_turn_report(): agregar cálculo de desviación estándar al reporte. |
| `tests/test_sql_tools.py` | Agregar 8 nuevas clases de prueba: TestDateShortcuts, TestVehicleFilter, TestNewToolsAvgWeighingTime, TestNewToolsAnomalyRate, TestNewToolsTopHaciendas, TestNewToolsPeriodComparison, TestBasicStatsWithGrouping, TestBreakdownByHaciendaWithGrouping, TestCustomPeriodSummaryWithGrouping, TestCheckThresholdsWithAgentConfig. Actualizar TOOL_DEFINITIONS count 13→17. |
| `tests/test_report_templates.py` | Actualizar metric_handlers_count 8→9. Agregar "std" a expected names. Agregar test_generate_report_with_std_metric y test_std_handler_returns_formatted_text. |
| `tests/test_sms_service.py` | Agregar test_generate_turn_report_includes_std y test_generate_turn_report_no_std_for_insufficient_data. |
| `tests/test_config.py` | Agregar clase TestLimitesControlEndpoints con 4 tests. |
| `frontend/src/components/AdminConfig.svelte` | Agregar limitesControl state, card "Límites de Control" con 7 inputs + unidades, tooltips CSS puro con :hover, cargar desde GET /api/config, guardar con PUT /api/setup/controls. |
| `harness/specs/33_sql_tools_v2/tasks.md` | Todas las tasks marcadas [x]. |

## Trazabilidad R<n> → test

| Requirement | Test |
|-------------|------|
| R1 — Shortcut "hoy" | TestDateShortcuts.test_shortcut_hoy |
| R2 — Shortcuts ayer/7dias/mes/personalizado | TestDateShortcuts.test_shortcut_ayer, test_shortcut_ultimos_7_dias, test_shortcut_mes_actual, test_shortcut_personalizado_con_fechas |
| R3 — Parámetro agrupacion en tools existentes | TestBasicStatsWithGrouping (todos), TestBreakdownByHaciendaWithGrouping, TestCustomPeriodSummaryWithGrouping |
| R4 — Formato resultado con agrupacion | TestBasicStatsWithGrouping.test_basic_stats_with_dia_grouping |
| R5 — Filtro tractomula | TestVehicleFilter.test_filter_tractomula_adds_filter, TestBasicStatsWithGrouping.test_basic_stats_with_tractomula_filter |
| R6 — Filtro vagon | TestVehicleFilter.test_filter_vagon_adds_filter, TestBreakdownByHaciendaWithGrouping.test_breakdown_with_vagon_filter |
| R7 — Nueva tool get_avg_weighing_time | TestNewToolsAvgWeighingTime.test_avg_weighing_time_with_data |
| R8 — get_avg_weighing_time datos insuficientes | TestNewToolsAvgWeighingTime.test_avg_weighing_time_single_record |
| R9 — Nueva tool get_anomaly_rate | TestNewToolsAnomalyRate.test_anomaly_rate_with_data |
| R10 — get_anomaly_rate sin anomalías | TestNewToolsAnomalyRate.test_anomaly_rate_empty_range |
| R11 — Nueva tool get_top_haciendas | TestNewToolsTopHaciendas.test_top_haciendas_with_data |
| R12 — get_top_haciendas límite inválido | TestNewToolsTopHaciendas.test_top_haciendas_invalid_limit |
| R13 — Nueva tool get_period_comparison | TestNewToolsPeriodComparison.test_period_comparison_with_data |
| R14 — Period comparison anterior vacío | TestNewToolsPeriodComparison.test_period_comparison_anterior_vacio |
| R15 — Std en reportes SMS | TestGenerateTurnReport.test_generate_turn_report_includes_std |
| R16 — Métrica "std" en plantillas | TestGenerateReport.test_generate_report_with_std_metric, test_std_handler_returns_formatted_text |
| R17 — Parámetros inválidos | TestDateShortcuts.test_shortcut_invalido, TestVehicleFilter.test_filter_invalid_raises, TestBasicStatsWithGrouping.test_basic_stats_invalid_grouping |
| R18 — Rango vacío | TestSqlToolsBasicStats.test_basic_stats_empty_range, TestNewToolsAvgWeighingTime.test_avg_weighing_time_empty_range |
| R19 — Compatibilidad inversa | TestBasicStatsWithGrouping.test_basic_stats_no_new_params_compatibility, TestBreakdownByHaciendaWithGrouping.test_breakdown_no_new_params_compatibility, TestCustomPeriodSummaryWithGrouping.test_custom_period_no_new_params_compatibility |
| R20 — GET /api/config incluye limites_control | TestLimitesControlEndpoints.test_get_config_includes_limites_control |
| R21 — PUT /api/setup/controls persiste | TestLimitesControlEndpoints.test_put_controls_valid_returns_200, test_put_controls_out_of_range_returns_422, test_put_controls_negative_limit_returns_422 |
| R22 — Card "Límites de Control" en AdminConfig | T33 (verificación manual de renderizado) |
| R23 — Formato de la card | T27 (inputs con unidades visibles) |
| R24 — Tooltips ayuda contextual | T28 (CSS :hover tooltips) |
| R25 — check_thresholds usa AgentConfig | TestCheckThresholdsWithAgentConfig.test_check_thresholds_default_config, test_check_thresholds_strict_config, test_check_thresholds_uses_injected_values |
| R26 — Control de acceso admin | TestLimitesControlEndpoints (usa dependency override admin role) |

## Decisiones de implementación

1. **Agrupación como post-procesamiento Python**: Para `get_basic_stats`, `get_breakdown_by_hacienda` y `get_custom_period_summary`, cuando se especifica `agrupacion`, se consultan filas individuales con fecha+hora, se asigna etiqueta de período en Python con `_compute_period_label()`, y se agrupan/agregan manualmente. Esto es más portable que SQL GROUP BY condicional, especialmente para agrupación por turno.

2. **`_compute_period_label` como static method**: No depende del estado de instancia, mantiene el patrón de los otros helpers.

3. **T3 (filtro vehículo) — `!= ""`**: Se usa `Weighing.tractomula != ""` para tractomula y `Weighing.vagon != ""` para vagon, tal como especificado.

4. **T26 (inyección AgentConfig)**: `SqlTools.__init__` acepta `agent_config=None` para mantener compatibilidad. `check_thresholds()` usa `self._agent_config.max_vegetal_to_muestra` cuando disponible, fallback a 0.5/0.3.

5. **Tooltips CSS puro**: Usando `:hover` sobre `.tooltip-icon` para mostrar `.tooltip-text` con `visibility`/`opacity`. Sin librerías externas.

6. **No se requirieron migraciones**: Todas las nuevas herramientas operan sobre tablas existentes.

## Resultado de init.ps1

- **Fase 1-5 (backend):** Todos los tests unitarios pasan:
  - `test_sql_tools`: 69 tests OK
  - `test_report_templates`: 21 tests OK
  - `test_sms_service`: 52 tests OK
  - `test_config`: 3 tests existentes + 4 nuevos OK
- **Fase 6 (frontend):** `npm run build` exitoso, copiado a `src/static/`.
- **Compatibilidad (R19):** Tests legacy de sql_tools no se rompieron.
- **T32:** `len(TOOL_DEFINITIONS) == 17` verificado.

## Impacto en features existentes

| Feature | Impacto | Estado |
|---------|---------|--------|
| F8 (ai_agent) | TOOL_DEFINITIONS crece de 13→17, tool_map expandido | Compatible: todos los parámetros nuevos son opcionales |
| F7 (sms_service) | generate_turn_report() ahora incluye std | Compatible: solo agrega texto al reporte |
| F35 (sms_scheduling_v2) | Consumirá nuevas tools | Pendiente — diseño de F35 coordinará |
| F34 (alert_monitor) | Consumirá get_anomaly_rate | Pendiente — diseño de F34 coordinará |
| Tests existentes | Todos pasan sin modificaciones (excepto actualizaciones de conteo) | ✅ Verificado |
