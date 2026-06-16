# Requirements — Sistema Inteligente de Reportería y Detección de Anomalías (TinyLLM)

> Feature 8 — ai_agent  
> EARS notation: Ubicuo, Evento, Estado, Opcional, No deseado

---

## R1 — Creación de plantilla de reporte

CUANDO el administrador envía una solicitud POST a `/api/reports/templates` con
un cuerpo JSON que incluye `name` (string), `schedule` (lista de horarios
"HH:MM"), `recipients` (lista de teléfonos) y `metrics` (lista de strings con
las métricas a incluir), el sistema DEBE crear una nueva plantilla de reporte
programado y persistirla en la tabla `report_templates`.

Cubre: RF-008a

---

## R2 — Modificación de plantilla de reporte

CUANDO el administrador envía una solicitud PUT a `/api/reports/templates/{id}`
con uno o más campos modificados (`name`, `schedule`, `recipients`, `metrics`),
el sistema DEBE actualizar la plantilla existente y persistir los cambios en la
tabla `report_templates`.

Cubre: RF-008a

---

## R3 — Eliminación de plantilla de reporte

CUANDO el administrador envía una solicitud DELETE a
`/api/reports/templates/{id}`, el sistema DEBE eliminar la plantilla de la tabla
`report_templates` y cesar la generación de reportes programados para esa
plantilla.

Cubre: RF-008a

---

## R4 — Métricas seleccionables en plantilla

Las métricas seleccionables para una plantilla DEBEN incluir al menos: `count`
(cantidad de pesajes), `avg` (peso promedio), `min_max` (peso mínimo y máximo),
`breakdown_by_hacienda` (desglose por hacienda), `breakdown_by_operator`
(desglose por operador), `composition` (proporción muestra/mineral/vegetal),
`anomaly_count` (conteo de anomalías en el período) y `trend` (tendencia lineal
del peso total).

Cubre: RF-008a

---

## R5 — Generación de reporte programado con métricas seleccionadas

CUANDO el planificador de reportes verifica la hora actual y coincide con un
horario configurado en alguna plantilla activa, el sistema DEBE generar un
reporte que incluya EXCLUSIVAMENTE las métricas seleccionadas en dicha
plantilla, ejecutando consultas SQL directas (sin invocar el LLM), y enviar el
reporte por SMS a todos los destinatarios configurados en `recipients`.

Cubre: RF-008b

---

## R6 — Detección de anomalías tras cada pesaje confirmado

CUANDO se completa exitosamente un registro de pesaje
(POST `/api/weighings` retorna status 201), el sistema DEBE ejecutar el
`AnomalyDetector` para evaluar el nuevo registro contra el histórico de pesajes
de la ventana configurada.

Cubre: RF-008c

---

## R7 — Capa Z-Score con ventana móvil

CUANDO el `AnomalyDetector` ejecuta la capa Z-Score, DEBE calcular el puntaje Z
del peso total (muestra + mineral + vegetal) de cada registro en la ventana
móvil, utilizando los últimos N registros o las últimas H horas (lo que ocurra
primero), y marcar como anomalía todo registro con |Z| > umbral configurable.

Cubre: RF-008c

---

## R8 — Capa relacional (ratios entre materiales)

CUANDO el `AnomalyDetector` ejecuta la capa relacional, DEBE calcular los
ratios `vegetal/muestra` y `mineral/muestra` para cada registro en la ventana,
y marcar como anomalía todo registro donde algún ratio exceda los umbrales
configurables (`max_vegetal_to_muestra`, `max_mineral_to_muestra`).

Cubre: RF-008c

---

## R9 — Capa temporal (tasa de cambio y rachas)

CUANDO el `AnomalyDetector` ejecuta la capa temporal, DEBE:
- Calcular la tasa de cambio porcentual de peso total entre pesajes consecutivos
- Marcar como anomalía todo cambio que supere el umbral `max_rate_change`
- Si se detectan `max_consecutive_anomalies` o más registros anómalos
  consecutivos, marcar el conjunto como anomalía sistémica.

Cubre: RF-008c

---

## R10 — Invocación del LLM ante anomalía detectada

SI alguna de las tres capas (Z-Score, relacional o temporal) detecta al menos
una anomalía, ENTONCES el sistema DEBE invocar el LLM local
(Qwen 2.5 1.5B en llama-server) pasándole el contexto estadístico real de la
ventana (últimos N registros, estadísticas descriptivas, lista de anomalías
detectadas por capa), generar un reporte narrativo y enviarlo por SMS a la
lista de corresponsales configurada.

Cubre: RF-008d

---

## R11 — Configuración de ventana Z-Score

La ventana del Z-Score DEBE ser configurable mediante los parámetros
`window_size` (número de registros, default 120) y `window_hours` (horas
máximas hacia atrás, default 4), aplicándose el límite que se alcance primero.

Cubre: RF-008c

---

## R12 — Umbrales configurables por capa

Los umbrales de detección DEBEN ser configurables:
- Capa Z-Score: `z_threshold` (default 3.0)
- Capa relacional: `max_vegetal_to_muestra` (default 0.5),
  `max_mineral_to_muestra` (default 0.3)
- Capa temporal: `max_rate_change` (default 0.5, 50%),
  `max_consecutive_anomalies` (default 3)

Cubre: RF-008c

---

## R13 — Enrutamiento de consulta SMS al LLM

CUANDO el `IncomingSmsDispatcher` recibe un SMS entrante que no coincide con
ningún comando conocido de otros módulos registrados (emergency_mode,
password_reset), el sistema DEBE pasar el texto completo del SMS al
`AgentOrchestrator` para su procesamiento como consulta en lenguaje natural
sobre los datos de pesaje.

Cubre: RF-008e

---

## R14 — Function Calling del LLM

CUANDO el LLM recibe una consulta del agente orquestador, DEBE responder
exclusivamente con una o más llamadas a herramientas (`tool_calls`) del
catálogo SQL parametrizado, sin ejecutar SQL directamente ni generar valores
numéricos propios.

Cubre: RF-008f

---

## R15 — Ejecución de herramientas con datos reales

CUANDO el sistema recibe una `tool_call` del LLM, DEBE ejecutar la herramienta
SQL solicitada con los parámetros indicados y pasar el resultado real (números,
listas, agregaciones) de vuelta al LLM como respuesta a la llamada de la
herramienta.

Cubre: RF-008f

---

## R16 — Prohibición de alucinaciones numéricas

El LLM NO DEBE generar valores numéricos, totales, promedios ni ninguna métrica
cuantitativa en su respuesta final que no provenga directamente de la ejecución
de una herramienta SQL parametrizada en la misma conversación.

Cubre: RF-008f

---

## R17 — Respuesta SMS al remitente

CUANDO el LLM genera la respuesta final parafraseando los resultados de las
herramientas ejecutadas, el sistema DEBE enviar el texto de la respuesta por
SMS al número de teléfono del remitente que originó la consulta.

Cubre: RF-008e, RF-008f

---

## R18 — Catálogo de herramientas SQL parametrizadas

El catálogo de herramientas SQL DEBE incluir las siguientes 12 funciones
invocables por el LLM:
1. `get_basic_stats(fecha_inicio, fecha_fin, tipo_material)` → count, avg, min, max, std
2. `get_percentiles(fecha_inicio, fecha_fin, percentil)` → percentil específico
3. `get_moving_average(window_size, tipo_material)` → promedio móvil
4. `get_trend(fecha_inicio, fecha_fin, tipo_material)` → pendiente regresión lineal
5. `get_breakdown_by_hacienda(fecha_inicio, fecha_fin)` → agregado por hacienda
6. `get_breakdown_by_operator(fecha_inicio, fecha_fin)` → agregado por operador
7. `get_material_composition(fecha_inicio, fecha_fin)` → proporción muestra/mineral/vegetal
8. `get_shift_summary(fecha, turno)` → reporte completo de turno
9. `get_daily_summary(fecha)` → agregado diario
10. `get_custom_period_summary(fecha_inicio, fecha_fin)` → resumen período
11. `detect_anomalies(window_size, z_threshold)` → lista de anomalías detectadas
12. `check_thresholds(window_size)` → evaluación vs umbrales

Cubre: RF-008h

---

## R19 — Registro de anomalías en tabla anomaly_log

CUANDO se detecta una anomalía por cualquier capa, el sistema DEBE insertar un
registro en la tabla `anomaly_log` con: `record_id` del pesaje asociado,
`layer` (zscore/relacional/temporal), `z_score` o valor de la métrica,
`threshold` aplicado, `metric_value`, `llm_report` (texto narrativo si se
invocó el LLM), `sent_sms` (booleano) y `created_at`.

Cubre: RF-008d

---

## R20 — CPU Pinning del LLM con taskset

MIENTRAS el servicio `llama-server` esté en ejecución, DEBE estar limitado a
los cores 0-2 mediante `taskset -c 0-2` y configurado con `-t 3` (3 threads de
inferencia), garantizando que el backend que ejecuta en el core 3 no se vea
afectado por la carga del LLM.

Cubre: RF-008g

---

## R21 — Tolerancia a fallos de conexión con llama-server

CUANDO falla la comunicación HTTP con `llama-server` (timeout, conexión
rechazada, error 5xx), el sistema DEBE registrar el error en el log con nivel
ERROR, descartar la operación que requería el LLM y continuar la ejecución sin
interrumpir el servicio de pesaje ni los reportes programados.

Cubre: RF-008d

---

## R22 — Modo desarrollo con LLM simulado

CUANDO el sistema se inicia con `DEV_MODE=true`, el `LlamaClient` DEBE operar
en modo simulación: responder a las solicitudes de completions con respuestas
predefinidas o registrar las interacciones en el log, sin requerir conexión a
`llama-server` ni ejecución de `taskset`.

Cubre: RF-008g

---

## R23 — Respuesta ante datos vacíos en consulta SMS

CUANDO una consulta SMS del corresponsal dispara herramientas SQL que retornan
conjuntos vacíos (sin datos en el período consultado), el sistema DEBE
responder al remitente con un mensaje SMS informando que no hay datos
disponibles para el período o filtros solicitados.

Cubre: RF-008e, RF-008f
