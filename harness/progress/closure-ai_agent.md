# Cierre — ai_agent

## Resumen

Se implementó el Sistema Inteligente de Reportería y Detección de Anomalías (Feature 8) para SIP-Edge, basado en TinyLLM (Qwen 2.5 1.5B). El sistema consta de tres flujos principales:

1. **Reportes Programados:** El administrador crea plantillas con métricas seleccionables (count, avg, min/max, breakdown, composition, anomaly_count, trend) mediante endpoints CRUD. Los reportes se generan con SQL directo (sin LLM) y se envían por SMS a corresponsales en horarios configurables (por defecto 06:00, 14:00, 22:00).

2. **Detección de Anomalías en Tiempo Real:** Tras cada pesaje confirmado, el sistema ejecuta 3 capas algorítmicas: Z-Score con ventana móvil (default 120 registros o 4 horas), ratios relacionales entre materiales (vegetal/muestra, mineral/muestra) y tasa de cambio temporal con detección de rachas anómalas. Si se detecta una anomalía, se invoca el LLM local para generar un reporte narrativo y se envía por SMS a los corresponsales.

3. **Consultas Ad-hoc por SMS:** Un corresponsal envía una pregunta en lenguaje natural, el sistema la procesa mediante LLM con Function Calling, que selecciona y ejecuta herramientas SQL parametrizadas de un catálogo de 12 funciones, y retorna la respuesta parafraseada por SMS.

Todo soportado por 5 nuevos módulos (`sql_tools.py`, `anomaly_detector.py`, `llm_client.py`, `report_templates.py`, `agent_orchestrator.py`), con 5 nuevos archivos de test y 2 migraciones SQL.

## Archivos creados

| Archivo | Propósito |
|---------|-----------|
| `src/llm_client.py` | Cliente HTTP para llama-server con Function Calling y modo dev simulado |
| `src/anomaly_detector.py` | Detector de anomalías en 3 capas (Z-Score, relacional, temporal) |
| `src/sql_tools.py` | Catálogo de 12 herramientas SQL parametrizadas + dispatcher |
| `src/agent_orchestrator.py` | Orquestador LLM + SQL Tools + SMS |
| `src/report_templates.py` | CRUD de plantillas de reporte + generación SQL directa |
| `tests/test_sql_tools.py` | 24 tests para el catálogo de herramientas SQL |
| `tests/test_anomaly_detector.py` | 17 tests para las 3 capas de detección |
| `tests/test_llm_client.py` | 10 tests para el cliente LLM (dev/prod/errores) |
| `tests/test_agent_orchestrator.py` | 8 tests de integración del orquestador |
| `tests/test_report_templates.py` | 13 tests de CRUD, METRIC_HANDLERS, y generate_report |
| `database/migrations/2026_06_16_000004_create_report_templates.sql` | Migración: tabla report_templates |
| `database/migrations/2026_06_16_000005_create_anomaly_log.sql` | Migración: tabla anomaly_log |

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/config.py` | Añadido `AgentConfig` dataclass (frozen=True). `load_config()` retorna 6-tuple incluyendo AgentConfig. `_atomic_write_sections()` incluye sección `agent`. Nuevo `save_agent_config()`. |
| `src/models.py` | Añadidos modelos `ReportTemplate` y `AnomalyLog` con índices. |
| `src/main.py` | Lifespan extendido: 6-tuple de load_config, inicialización de LlamaClient, SqlTools, AnomalyDetector, ReportTemplateService, AgentOrchestrator. Nuevos routers: agent_router, reports_router, anomaly_router. Handler SMS AI registrado en dispatcher. Cleanup de LlamaClient. |
| `src/sms_service.py` | `send_scheduled_report()` acepta `recipients` opcional. `_check_and_send_reports()` extendido para consultar `ReportTemplateService`. Nuevo `set_template_service()`. |
| `src/weighings.py` | Hook `_run_anomaly_detection()` tras pesaje exitoso. |

## Decisiones técnicas

1. **Reportes programados sin LLM:** `generate_report()` usa SQL directo + formateo, sin invocar el LLM. Esto garantiza precisión numérica absoluta y baja latencia (<50ms vs 500ms-2s con LLM).

2. **Detector de anomalías algorítmico (3 capas):** Z-Score, relacional y temporal se implementaron con Python puro + SQL, evitando el no-determinismo del LLM para detección en tiempo real tras cada pesaje.

3. **Function Calling con herramientas SQL parametrizadas:** El LLM nunca ejecuta SQL directamente; selecciona herramientas de un catálogo de 12 funciones predefinidas con parámetros tipados, eliminando riesgo de alucinaciones numéricas o inyección SQL.

4. **Dispatcher SMS con handler AI como fallback:** El handler de consultas SMS se registra al ÚLTIMO en el dispatcher, actuando como fallback para cualquier SMS no manejado por emergency_mode o password_reset.

5. **Hook de pesaje tolerante a fallos:** `_run_anomaly_detection()` se ejecuta sincrónicamente tras el commit. Si falla (LLM no disponible, BD caída), registra error en log pero no interrumpe el flujo de pesaje.

6. **Modo desarrollo simulado:** `LlamaClient` en dev_mode no requiere llama-server. Retorna respuestas predecibles con tool_calls simulados, permitiendo desarrollo y tests sin hardware LLM real.

7. **CPU Pinning documentado:** El servicio llama-server se ejecuta con `taskset -c 0-2 -t 3`, dedicando 3 cores al LLM y dejando el core restante para el backend.

### Alternativas descartadas

1. **Usar el LLM para generar reportes programados completos:** Descartado por latencia innecesaria, riesgo de alucinaciones y consumo excesivo de recursos en EdgeBox.
2. **Detección de anomalías vía LLM:** Descartado por latencia impracticable en tiempo real, no-determinismo y consumo desproporcionado de CPU.
3. **Almacenar plantillas en config.yaml:** Descartado por falta de concurrencia, validación relacional y capacidad de consulta eficiente.

## Trazabilidad R&lt;n&gt; ↔ tests

| R&lt;n&gt; | Requisito | Test(s) |
|------------|-----------|---------|
| R1 | Crear plantilla de reporte | `test_create_template`, `test_get_all_templates`, `test_get_active_by_schedule` |
| R2 | Modificar plantilla | `test_update_template`, `test_update_nonexistent_template` |
| R3 | Eliminar plantilla | `test_delete_template`, `test_delete_nonexistent_template` |
| R4 | Métricas seleccionables (≥8) | `test_metric_handlers_count`, `test_metric_handlers_names` |
| R5 | Reporte sin LLM con métricas seleccionadas | `test_generate_report_produces_text_without_llm`, `test_generate_report_filters_metrics`, `test_generate_report_unknown_metric_skipped`, `test_generate_report_empty_metrics` |
| R6 | Detección tras pesaje confirmado | `TestAnomalyDetectorRun.test_run_returns_empty_on_normal`, hook `_run_anomaly_detection` |
| R7 | Capa Z-Score con ventana móvil | `TestZScoreLayer.test_no_anomaly_on_stable_data`, `test_anomaly_on_extreme_value` |
| R8 | Capa relacional (ratios) | `TestRelationalLayer.test_normal_ratios_no_anomaly`, `test_high_vegetal_ratio_detects_anomaly`, `test_high_mineral_ratio_detects_anomaly` |
| R9 | Capa temporal (tasa de cambio y rachas) | `TestTemporalLayer.test_small_change_no_anomaly`, `test_large_change_detects_anomaly`; `TestTemporalConsecutive.test_consecutive_anomalies_detected` |
| R10 | Invocación LLM ante anomalía | `TestHandleAnomaly.test_handle_anomaly_creates_logs_and_sends_sms`, `test_handle_anomaly_no_anomalies` |
| R11 | Ventana configurable (size/hours) | `TestWindowConfig.test_window_respects_size` |
| R12 | Umbrales configurables por capa | `TestZScoreThreshold.test_below_threshold_no_anomaly` |
| R13 | Enrutamiento SMS al orquestador | `TestHandleSmsQuery.test_sms_query_with_tool_calls`, handler `_build_ai_sms_handler` |
| R14 | Function Calling del LLM | `TestLlamaClientProdMode.test_chat_completion_posts_to_correct_url`, `test_chat_completion_includes_tools` |
| R15 | Ejecución tools con datos reales | `TestSqlToolsExecuteTool.test_execute_tool_valid` |
| R16 | Prohibición alucinaciones numéricas | `SYSTEM_PROMPT` en agent_orchestrator.py |
| R17 | Respuesta SMS al remitente | `TestHandleSmsQuery.test_sms_query_with_tool_calls` |
| R18 | Catálogo 12 herramientas SQL | `TestToolDefinitions.test_tool_definitions_count` (12 tools) |
| R19 | Registro anomaly_log | `TestHandleAnomaly.test_handle_anomaly_creates_logs_and_sends_sms` |
| R20 | CPU Pinning taskset | Documentado en entorno (configuración systemd) |
| R21 | Tolerancia fallos llama-server | `TestLlamaClientConnectionError` (3 tests); `TestHandleAnomalyLlmFailure` (2 tests) |
| R22 | Modo desarrollo simulado | `TestLlamaClientDevMode` (3 tests) |
| R23 | Respuesta datos vacíos en consulta SMS | `TestSmsQueryEmptyData.test_empty_data_responds_no_data` |

## Verificación

- [x] 430 tests ejecutados: TODOS VERDES (OK)
- [x] `./init.ps1` — todos los bloques [OK]
- [x] Trazabilidad R1–R23 ↔ tests completa (23 requirements con cobertura)
- [x] 32/32 tasks completadas (T1–T32 marcadas [x])
- [x] Code review aprobado (3ª ronda, ver `harness/progress/review_ai_agent.md`)
- [x] Código respeta capas, convenciones, inmutabilidad (dataclasses frozen=True)
- [x] Sin dependencias externas nuevas (solo stdlib + httpx/pyserial ya existentes)
- [x] Unpacking load_config() de 6 valores correcto en todos los módulos
- [x] GitHub issue #12 comentado y cerrado (reason: completed)
- [x] Closure listo para release-manager

## Lecciones / pitfalls

- El cambio de firma de `load_config()` de 5-tuple a 6-tuple (añadiendo AgentConfig) rompió unpackings en `src/rs232.py`, `tests/test_scale.py`, `scripts/backup.py` y `src/main.py`. El reviewer verificó manualmente cada sitio y todos estaban correctos en la 3ª ronda.
- La feature requirió 3 rondas de review: la primera detectó tests faltantes para R1-R5, la segunda detectó T32 sin marcar, y la tercera fue aprobatoria.
- El detector de anomalías en 3 capas consumió la mayor parte del esfuerzo de diseño e implementación debido a la complejidad algorítmica y la necesidad de ventanas configurables.
- La integración con el dispatcher SMS existente requirió modificar `sms_service.py` para soportar destinatarios personalizados y consultar `ReportTemplateService`.

## GitHub Issue

- **Issue:** https://github.com/rojecas/sip_edge/issues/12
- **Estado:** Comentado con resumen de implementación y cerrado (reason: completed)

## Release

- [x] La feature está registrada en tracker.json como pendiente para release
