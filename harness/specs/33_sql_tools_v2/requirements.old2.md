# Feature 33 — sql_tools_v2: Herramientas Estadísticas v2

> Extiende el catálogo de herramientas SQL con 4 nuevas métricas, modifica 3 herramientas
> existentes agregando parámetros de agrupación y filtro por vehículo, e incluye shortcuts
> de fecha y desviación estándar en resúmenes SMS.

---

## R1 — Shortcut "hoy"
CUANDO el usuario especifica `"periodo": "hoy"` en una herramienta que acepte shortcuts de
fecha, el sistema DEBE convertir internamente ese shortcut al rango `[fecha_actual, fecha_actual]`
(es decir, desde las 00:00:00 hasta las 23:59:59 del día actual).

## R2 — Shortcuts "ayer", "últimos 7 días", "mes actual" y "personalizado"
CUANDO el usuario especifica uno de los siguientes shortcuts:
- `"ayer"` → rango del día anterior
- `"ultimos_7_dias"` → rango desde hace 7 días hasta hoy, ambos inclusive
- `"mes_actual"` → rango desde el primer día del mes actual hasta hoy, ambos inclusive
- `"personalizado"` → requiere los parámetros `fecha_inicio` y `fecha_fin` explícitos
ENTONCES el sistema DEBE resolver el rango de fechas correspondiente antes de ejecutar la
consulta SQL.

## R3 — Parámetro de agrupación en herramientas existentes
DONDE una herramienta existente soporte rangos de fecha (`get_basic_stats`,
`get_breakdown_by_hacienda`, `get_custom_period_summary`), el sistema DEBE aceptar un
parámetro opcional `agrupacion` con los valores: `"dia"`, `"semana"`, `"mes"`, `"turno"`.

## R4 — Formato del resultado con agrupación
CUANDO se especifica `agrupacion`, el sistema DEBE retornar los resultados organizados en una
lista de grupos, donde cada grupo contiene un identificador del período (ej. la fecha ISO para
"dia", el número de semana ISO + año para "semana", el mes y año para "mes", o el nombre del
turno para "turno") más las métricas correspondientes.

## R5 — Filtro por vehículo tractomula
DONDE una herramienta consulte la tabla `weighings`, el sistema DEBE aceptar un parámetro
opcional `tipo_vehiculo` con valor `"tractomula"`, y filtrar los registros donde la columna
`tractomula` NO esté vacía.

## R6 — Filtro por vehículo vagon
DONDE una herramienta consulte la tabla `weighings`, el sistema DEBE aceptar un parámetro
opcional `tipo_vehiculo` con valor `"vagon"`, y filtrar los registros donde la columna `vagon`
NO esté vacía.

## R7 — Nueva tool: get_avg_weighing_time — camino feliz
CUANDO se invoca `get_avg_weighing_time` con `fecha_inicio` y `fecha_fin` válidos, el sistema
DEBE calcular el tiempo promedio entre pesajes consecutivos dentro del rango, utilizando la
diferencia entre la hora de cada pesaje y el anterior, y retornar `{ "avg_time_minutes": <float>,
"count": <int>, "fecha_inicio": <str>, "fecha_fin": <str> }`.

## R8 — Nueva tool: get_avg_weighing_time — datos insuficientes
SI el rango de fechas contiene menos de 2 pesajes, `get_avg_weighing_time` DEBE retornar
`{ "avg_time_minutes": 0.0, "count": <int>, "mensaje": "Datos insuficientes" }`.

## R9 — Nueva tool: get_anomaly_rate — camino feliz
CUANDO se invoca `get_anomaly_rate` con `fecha_inicio` y `fecha_fin` válidos, el sistema DEBE
calcular la tasa de anomalías como el porcentaje de registros en `AnomalyLog` contra el total de
pesajes en el rango, y retornar `{ "total_weighings": <int>, "total_anomalies": <int>,
"anomaly_rate_pct": <float>, "fecha_inicio": <str>, "fecha_fin": <str> }`.

## R10 — Nueva tool: get_anomaly_rate — sin anomalías
SI el rango de fechas contiene pesajes pero no hay anomalías registradas, el sistema DEBE
retornar `anomaly_rate_pct = 0.0`.

## R11 — Nueva tool: get_top_haciendas — camino feliz
CUANDO se invoca `get_top_haciendas` con `fecha_inicio`, `fecha_fin` y `limite` (entero > 0),
el sistema DEBE retornar un ranking descendente de hasta N haciendas por peso total, con
`{ "ranking": [ { "hacienda_id": <int>, "codigo": <str>, "nombre": <str>, "total_weight": <float>,
"count": <int> }, ... ], "fecha_inicio": <str>, "fecha_fin": <str> }`.

## R12 — Nueva tool: get_top_haciendas — límite inválido
SI `limite` es menor o igual a 0 ENTONCES el sistema DEBE lanzar `ToolExecutionError` con el
mensaje `"limite debe ser mayor a 0"`.

## R13 — Nueva tool: get_period_comparison — camino feliz
CUANDO se invoca `get_period_comparison` con `fecha_inicio`, `fecha_fin` y
`periodo_anterior_inicio`, `periodo_anterior_fin`, el sistema DEBE retornar la comparación
entre ambos períodos incluyendo delta absoluto y delta porcentual para: count, peso_total,
peso_promedio. Formato: `{ "periodo_actual": { "count": <int>, "peso_total": <float>,
"peso_promedio": <float> }, "periodo_anterior": { ... }, "delta": { "count": <int>,
"peso_total": <float>, "peso_promedio": <float> },
"delta_pct": { "count": <float>, "peso_total": <float>, "peso_promedio": <float> } }`.

## R14 — Nueva tool: get_period_comparison — período anterior vacío
SI el período anterior contiene 0 pesajes ENTONCES el sistema DEBE retornar `delta_pct` con
valor `null` para todas las métricas (división por cero evitada).

## R15 — Desviación estándar en reportes de turno SMS
MIENTRAS el sistema genera un reporte de turno en `sms_service.py` (`generate_turn_report`),
DEBE incluir la desviación estándar del peso total de los pesajes en el turno, además del
count y peso_total existentes.

## R16 — Mátrica "std" en plantillas de reporte programado
El sistema DEBE registrar un nuevo handler de métrica `"std"` en `report_templates.py` que
calcule la desviación estándar del peso total (`peso_muestra + peso_mineral + peso_vegetal_extrano`)
para el día actual y retorne un string como `"Desviacion estandar: X.XX kg"`.

## R17 — Parámetros inválidos en herramientas
SI una herramienta recibe parámetros inválidos (ej. `agrupacion` no reconocido,
`tipo_vehiculo` no reconocido, fecha en formato incorrecto), el sistema DEBE lanzar
`ToolExecutionError` con un mensaje descriptivo indicando los valores válidos.

## R18 — Rango de fecha vacío (sin datos)
SI una herramienta recibe un rango de fechas sin registros de pesaje, el sistema DEBE
retornar un resultado vacío o con valores en cero según la herramienta, sin lanzar excepción.

## R19 — Compatibilidad inversa de herramientas modificadas
DONDE se agreguen nuevos parámetros opcionales (`agrupacion`, `tipo_vehiculo`) a herramientas
existentes, el sistema DEBE mantener compatibilidad hacia atrás: invocar la herramienta sin
los nuevos parámetros DEBE producir el mismo resultado que antes de la modificación.
