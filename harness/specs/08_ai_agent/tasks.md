# Tasks — Sistema Inteligente de Reportería y Detección de Anomalías (TinyLLM)

> Feature 8 — ai_agent  
> Orden de implementación. Cada task debe marcarse `[x]` al completarse.

---

## Fase 1 — Configuración y modelo de datos

- [x] T1 — Añadir dataclass `AgentConfig` en `src/config.py` con todos los
  parámetros de configuración del agente (llm_url, llm_model, window_size,
  z_threshold, etc.). Extender `load_config()` para parsear sección `agent`.
  Extender `_atomic_write_sections()` para incluir la sección `agent`.
  Cubre: R11, R12, R20.

- [x] T2 — Añadir modelos SQLAlchemy `ReportTemplate` y `AnomalyLog` en
  `src/models.py` con los campos definidos en design.md.
  Cubre: R1, R19.

- [x] T3 — Crear migraciones SQL para producción:
  `database/migrations/2026_06_16_000004_create_report_templates.sql` y
  `database/migrations/2026_06_16_000005_create_anomaly_log.sql`.
  Cubre: R1, R19.

---

## Fase 2 — SQL Tools (catálogo de herramientas)

- [x] T4 — Crear `src/sql_tools.py` con la clase `SqlTools` y el catálogo
  `TOOL_DEFINITIONS` (12 tool definitions en formato OpenAI tool calling).
  Implementar constructor que recibe `db_session_factory`.
  Cubre: R18.

- [x] T5 — Implementar herramientas de estadísticas: `get_basic_stats()`,
  `get_percentiles()`, `get_moving_average()`, `get_trend()` con consultas SQL
  parametrizadas contra la tabla `weighings`.
  Cubre: R18.

- [x] T6 — Implementar herramientas de desglose: `get_breakdown_by_hacienda()`,
  `get_breakdown_by_operator()`, `get_material_composition()` con JOIN a
  tablas `haciendas` y `users`.
  Cubre: R18.

- [x] T7 — Implementar herramientas de resumen: `get_shift_summary()`,
  `get_daily_summary()`, `get_custom_period_summary()`.
  Cubre: R18.

- [x] T8 — Implementar herramientas de anomalías: `detect_anomalies()`,
  `check_thresholds()` que consultan `anomaly_log`.
  Cubre: R18.

- [x] T9 — Implementar método `execute_tool(tool_name, arguments) -> dict` como
  dispatcher central que valida el nombre de la tool y llama al método
  correspondiente. Lanzar `ToolExecutionError` si la tool no existe o los
  parámetros son inválidos.
  Cubre: R14, R15, R18.

---

## Fase 3 — Anomaly Detector (3 capas)

- [x] T10 — Crear `src/anomaly_detector.py` con la dataclass `AnomalyResult`
  y la clase `AnomalyDetector`. Implementar `_get_window()` que obtiene los
  últimos N registros de `weighings` o los de las últimas H horas (lo que
  ocurra primero), ordenados por `fecha` + `hora` descendente.
  Cubre: R6, R11.

- [x] T11 — Implementar `_detect_zscore()`: calcula media y desviación estándar
  del peso total (muestra + mineral + vegetal) de la ventana. Marca como
  anomalía todo registro con |Z| > `z_threshold`.
  Cubre: R7, R12.

- [x] T12 — Implementar `_detect_relational()`: calcula ratios
  vegetal/muestra y mineral/muestra para cada registro. Marca como anomalía
  si algún ratio excede los umbrales configurables.
  Cubre: R8, R12.

- [x] T13 — Implementar `_detect_temporal()`: calcula tasa de cambio entre
  pesajes consecutivos. Marca como anomalía cambios que superen
  `max_rate_change`. Detecta rachas de N+ anómalos consecutivos como anomalía
  sistémica.
  Cubre: R9, R12.

- [x] T14 — Implementar `run(weighing)` que ejecuta las 3 capas en secuencia
  y retorna la lista completa de `AnomalyResult`. Implementar
  `detect_on_demand(window_size, z_threshold)` para ejecución bajo demanda.
  Cubre: R6, R7, R8, R9.

---

## Fase 4 — LLM Client

- [x] T15 — Crear `src/llm_client.py` con la clase `LlamaClient`:
  - Constructor recibe `base_url`, `model`, `timeout`, `dev_mode`.
  - Método `chat_completion(messages, tools)` que hace POST a
    `/v1/chat/completions` con formato OpenAI API.
  - En dev_mode, retorna respuesta simulada (predecible).
  - Lanzar `LlamaConnectionError` si falla conexión.
  - Método `close()` para cerrar sesión HTTP.
  Cubre: R14, R21, R22.

---

## Fase 5 — Report Templates Service

- [x] T16 — Crear `src/report_templates.py` con la clase
  `ReportTemplateService`: métodos `create()`, `update()`, `delete()`,
  `get_all()`, `get_active_by_schedule(time)`. Lanzar
  `TemplateNotFoundError` si no existe.
  Cubre: R1, R2, R3.

- [x] T17 — Implementar `generate_report(template, db) -> str` que construye
  el texto del reporte con SOLO las métricas seleccionadas en `template.metrics`,
  ejecutando consultas SQL directas (sin LLM). El texto debe ser formateado
  para SMS (máximo 160 caracteres por mensaje, concatenado si es necesario).
  Cubre: R4, R5.

---

## Fase 6 — Agent Orchestrator

- [x] T18 — Crear `src/agent_orchestrator.py` con la clase `AgentOrchestrator`:
  - Constructor recibe `LlamaClient`, `SqlTools`, `SMSService`,
    `db_session_factory`.
  - Implementar `handle_anomaly(anomalies, context)`: construye prompt con
    contexto estadístico real, invoca LLM sin tools (solo narrativa), recibe
    texto, lo envía por SMS a corresponsales.
  - Si LLM falla, registrar error y continuar (no interrumpir pesaje).
  Cubre: R10, R19, R21.

- [x] T19 — Implementar `handle_sms_query(sender_phone, text)`:
  - Construye mensajes del sistema + consulta + definiciones de tools.
  - Invoca `LlamaClient.chat_completion()` con tools.
  - Si hay `tool_calls`, ejecutar `SqlTools.execute_tool()` para cada una.
  - Pasar resultados reales al LLM para segunda vuelta.
  - El LLM parafrasea y el texto final se envía por SMS al remitente.
  - Si datos vacíos, responder "No hay datos disponibles para el período".
  Cubre: R13, R14, R15, R16, R17, R23.

---

## Fase 7 — Endpoints API e integración en main.py

- [x] T20 — Modificar lifespan en `src/main.py`:
  - Desempaquetar `AgentConfig` del tuple de `load_config()`.
  - Crear instancias de `LlamaClient`, `SqlTools`, `AnomalyDetector`,
    `ReportTemplateService`, `AgentOrchestrator`.
  - Almacenar en `app.state`.
  - En cleanup, cerrar `LlamaClient`.
  Cubre: R6, R10, R13.

- [x] T21 — Registrar endpoint de consulta directa
  `POST /api/agent/query` (admin) que recibe `{ "query": "..." }` y retorna
  la respuesta del agente. Crear router `agent_router`.
  Cubre: R13, R14, R15, R16.

- [x] T22 — Registrar endpoints CRUD de plantillas:
  `GET /api/reports/templates`, `POST /api/reports/templates`,
  `PUT /api/reports/templates/{id}`, `DELETE /api/reports/templates/{id}`.
  Cubre: R1, R2, R3.

- [x] T23 — Registrar endpoints de anomalías:
  `GET /api/anomalies?window=120&threshold=3.0` (detección bajo demanda),
  `GET /api/anomalies/history?limit=50` (historial). Admin auth.
  Cubre: R7, R19.

- [x] T24 — Extender el hook posterior a `POST /api/weighings` para ejecutar
  `AnomalyDetector.run(weighing)`. Si hay anomalías, invocar
  `AgentOrchestrator.handle_anomaly()`. Registrar en `anomaly_log`.
  Cubre: R6, R10, R19.

- [x] T25 — Registrar handler de consultas SMS en `IncomingSmsDispatcher`
  (después de los handlers de emergency_mode y password_reset) que llame a
  `AgentOrchestrator.handle_sms_query()`. El handler debe ser una función
  que retorna `True` si procesó el SMS.
  Cubre: R13.

- [x] T26 — Extender `SMSService._check_and_send_reports()` para consultar
  `ReportTemplateService.get_active_by_schedule(hora_actual)` y generar
  reportes para cada plantilla activa en ese horario, usando
  `generate_report()`. Enviar a los destinatarios de la plantilla.
  Cubre: R5.

---

## Fase 8 — CPU Pinning

- [x] T27 — Configurar o documentar el servicio systemd `llama-server` para
  que se ejecute con `taskset -c 0-2` y argumento `-t 3`. Crear o modificar
  `llama-server` service file en EdgeBox. Verificar que el backend no se
  ejecuta en cores 0-2.
  Cubre: R20.

---

## Fase 9 — Tests

- [x] T28 — Crear `tests/test_sql_tools.py` con:
  - `TestSqlToolsBasicStats` — verificar count, avg, min, max, std con datos
    de prueba (R18)
  - `TestSqlToolsBreakdown` — verificar desglose por hacienda y operador (R18)
  - `TestSqlToolsComposition` — verificar proporción de materiales (R18)
  - `TestSqlToolsInvalidTool` — verificar `ToolExecutionError` para tool
    inexistente (R14)
  - `TestSqlToolsExecuteTool` — verificar dispatcher `execute_tool()` (R15)
  Cubre: R14, R15, R18.

- [x] T29 — Crear `tests/test_anomaly_detector.py` con:
  - `TestZScoreLayer` — verificar cálculo Z-Score con datos controlados (R7)
  - `TestZScoreThreshold` — verificar que |Z| <= threshold no marca anomalía (R12)
  - `TestRelationalLayer` — verificar detección de ratios excedidos (R8)
  - `TestTemporalLayer` — verificar detección de cambios bruscos (R9)
  - `TestTemporalConsecutive` — verificar detección de rachas anómalas (R9)
  - `TestAnomalyDetectorRun` — verificar integración de 3 capas (R6)
  - `TestWindowConfig` — verificar límite por registros y por horas (R11)
  Cubre: R6, R7, R8, R9, R11, R12.

- [x] T30 — Crear `tests/test_llm_client.py` con:
  - `TestLlamaClientDevMode` — verificar que en dev mode no hace HTTP (R22)
  - `TestLlamaClientProdMode` — verificar POST a la URL correcta (mock
    httpx.Client) (R14)
  - `TestLlamaClientConnectionError` — verificar `LlamaConnectionError`
    al fallar conexión (R21)
  Cubre: R14, R21, R22.

- [x] T31 — Crear `tests/test_agent_orchestrator.py` con:
  - `TestHandleAnomaly` — verificar que llama al LLM y envía SMS (mockear
    LlamaClient y SMSService) (R10)
  - `TestHandleSmsQuery` — verificar ciclo completo: SMS → LLM → tool_calls
    → ejecución → respuesta SMS (R13, R14, R15, R16)
  - `TestSmsQueryEmptyData` — verificar respuesta "sin datos" cuando no hay
    registros (R23)
  - `TestHandleAnomalyLlmFailure` — verificar que fallo del LLM no
    interrumple (R21)
  Cubre: R10, R13, R14, R15, R16, R21, R23.

---

## Fase 10 — Verificación final

- [x] T32 — Ejecutar `./init.ps1` y verificar que todos los bloques pasan
  en [OK]. Corregir cualquier fallo de lint, import o dependencia.
  Cubre: Verificación general del harness.
