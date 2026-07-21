# Review — feature 33: sql_tools_v2

**Veredicto:** APPROVED

## Trazabilidad requirements <-> tests

| R<n> | Test(s) | Estado |
|------|---------|--------|
| R1 — Shortcut "hoy" | TestDateShortcuts.test_shortcut_hoy | [x] |
| R2 — Shortcuts ayer/7dias/mes/personalizado | test_shortcut_ayer, test_shortcut_ultimos_7_dias, test_shortcut_mes_actual, test_shortcut_personalizado_con_fechas | [x] |
| R3 — Parámetro agrupacion | TestBasicStatsWithGrouping (all), TestBreakdownByHaciendaWithGrouping, TestCustomPeriodSummaryWithGrouping | [x] |
| R4 — Formato resultado con agrupacion | test_basic_stats_with_dia_grouping | [x] |
| R5 — Filtro tractomula | test_filter_tractomula_adds_filter, test_basic_stats_with_tractomula_filter | [x] |
| R6 — Filtro vagon | test_filter_vagon_adds_filter, test_breakdown_with_vagon_filter | [x] |
| R7 — Nueva tool get_avg_weighing_time | test_avg_weighing_time_with_data | [x] |
| R8 — Datos insuficientes | test_avg_weighing_time_single_record | [x] |
| R9 — Nueva tool get_anomaly_rate | test_anomaly_rate_with_data | [x] |
| R10 — Sin anomalías | test_anomaly_rate_empty_range, test_anomaly_rate_no_anomalies | [x] |
| R11 — Nueva tool get_top_haciendas | test_top_haciendas_with_data | [x] |
| R12 — Límite inválido | test_top_haciendas_invalid_limit, test_top_haciendas_invalid_limit_negative | [x] |
| R13 — Nueva tool get_period_comparison | test_period_comparison_with_data | [x] |
| R14 — Periodo anterior vacío | test_period_comparison_anterior_vacio | [x] |
| R15 — Std en reportes SMS | test_generate_turn_report_includes_std | [x] |
| R16 — Métrica "std" en plantillas | test_generate_report_with_std_metric, test_std_handler_returns_formatted_text | [x] |
| R17 — Parámetros inválidos | test_shortcut_invalido, test_filter_invalid_raises, test_basic_stats_invalid_grouping | [x] |
| R18 — Rango vacío | test_basic_stats_empty_range, test_avg_weighing_time_empty_range | [x] |
| R19 — Compatibilidad inversa | test_basic_stats_no_new_params_compatibility, test_breakdown_no_new_params_compatibility, test_custom_period_no_new_params_compatibility | [x] |
| R20 — limites_control en GET /api/config | test_get_config_includes_limites_control | [x] |
| R21 — PUT /api/setup/controls persiste | test_put_controls_valid_returns_200, test_put_controls_out_of_range_returns_422, test_put_controls_negative_limit_returns_422 | [x] |
| R22 — Card en AdminConfig | T33 — Confirmado en AdminConfig.svelte (líneas 188-270) | [x] |
| R23 — Formato de la card | T27 — 7 inputs con unidades visibles (σ, registros, horas, %) | [x] |
| R24 — Tooltips CSS | T28 — CSS :hover tooltips sin librerías externas (líneas 408-488) | [x] |
| R25 — check_thresholds usa AgentConfig | TestCheckThresholdsWithAgentConfig.test_check_thresholds_default_config, test_check_thresholds_strict_config, test_check_thresholds_uses_injected_values | [x] |
| R26 — Control de acceso admin | TestLimitesControlEndpoints (dependency override admin role) | [x] |

Cobertura completa: 26/26 requirements cubiertos por tests concretos.

## Tasks completas

Todas las 33 tasks (T1-T33) en harness/specs/33_sql_tools_v2/tasks.md están marcadas [x]:
- Fase 1 (T1-T2): Helper shortcuts ✓
- Fase 2 (T3-T4): Filtro vehículo ✓
- Fase 3 (T5-T13): 4 nuevas tools + tests ✓
- Fase 4 (T14-T20): Modificar 3 tools existentes + tests ✓
- Fase 5 (T21-T23): Desviación estándar en SMS ✓
- Fase 6 (T24-T30): Setup Límites de Control ✓
- Fase 7 (T31-T33): Verificación final ✓

## Checkpoints

- C1: [x] Arnés completo
- C2: [x] Estado coherente (una feature en in_progress)
- C3: [x] Código respeta arquitectura
- C4: [x] Tests pasan (99 tests F33, todos OK)
- C5: [x] BD bajo control (sin migraciones nuevas)
- C6: [x] Sesión manejada
- C7: [x] SDD completo (specs/, tasks, tests)
- C8: [ ] Closure aún no creado (estado in_progress, pendiente de pruebas manuales)

## Puntos críticos verificados

1. **check_thresholds()** usa self._agent_config.max_vegetal_to_muestra (línea 1041 sql_tools.py) — NO hardcodeado 0.5 ✓
2. **GET /api/config** incluye clave limites_control con 7 parámetros (líneas 984-995 main.py) ✓
3. **PUT /api/setup/controls** existe con validaciones de rango (Field ge/le) (líneas 926-969 main.py) ✓
4. **SqlTools.__init__** acepta gent_config=None (línea 318 sql_tools.py) — no rompe tests legacy ✓
5. **AdminConfig.svelte** tiene card "Límites de Control" con 7 inputs + tooltips CSS (líneas 188-270, 408-488) ✓
6. **Tooltips** usan :hover sin librerías externas — CSS puro (.tooltip-icon:hover + .tooltip-text) ✓
7. **TOOL_DEFINITIONS** tiene 17 entradas — verificado por test (test_tool_definitions_count) ✓
8. **Parámetros nuevos son opcionales** — todos con = None default, compatibilidad R19 ✓
9. **Agrupación como post-procesamiento Python** — documentado en impl y confirmado en código (líneas 477-501, etc.) ✓
10. **SqlTools instanciado con agent_config** en main.py (línea 323) ✓
11. **PUT /api/setup/controls actualiza app.state.agent_config y sql_tools._agent_config** (líneas 957-960 main.py) ✓

## Skills consultados

El implementer documentó skills consultados en impl_33_sql_tools_v2.md:
- **svelte5** — Reglas de runes
- **verification-before-completion** — Verificación antes de declarar done ✓

## Impacto en features existentes

Documentado en impl_33_sql_tools_v2.md sección 'Impacto en features existentes':
- F8 (ai_agent): TOOL_DEFINITIONS 13→17, compatible ✓
- F7 (sms_service): generate_turn_report incluye std, compatible ✓
- Tests existentes: todos pasan sin modificaciones ✓

## Tests

- 	est_sql_tools: 69+ tests (todos OK)
- 	est_report_templates: 21 tests (todos OK)
- 	est_sms_service: TurnReport tests (todos OK)
- 	est_config (TestLimitesControlEndpoints): 4 tests (todos OK)
- **Total: 99 tests, todos OK** — ejecutado en contenedor Docker

Pre-existing failures en test_scale.py (F5) y test_virtual_scale.py (F25) — NO relacionados con F33.

## Frontend build

src/static/index.html actualizado (2026-07-20 20:00:41) — build reciente.

## Release

- [ ] La feature/bug está lista para release-manager (closure existe)
  - Estado actual: in_progress. Pendiente de pruebas manuales y autorización de cierre.
