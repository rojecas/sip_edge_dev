# Feature 33 — sql_tools_v2: Herramientas Estadísticas v2

> Extiende el catálogo de herramientas SQL con 4 nuevas métricas, modifica 3 herramientas
> existentes agregando parámetros de agrupación y filtro por vehículo, incluye shortcuts
> de fecha, desviación estándar en SMS, y expone los límites de control en el panel de
> configuración (Admin > Setup).

---

## R1 — Shortcut "hoy"
CUANDO el usuario especifica `"periodo": "hoy"` en una herramienta que acepte shortcuts de
fecha, el sistema DEBE convertir internamente ese shortcut al rango `[fecha_actual, fecha_actual]`.

## R2 — Shortcuts "ayer", "últimos 7 días", "mes actual" y "personalizado"
CUANDO el usuario especifica `"ayer"`, `"ultimos_7_dias"`, `"mes_actual"` o `"personalizado"`,
el sistema DEBE resolver el rango de fechas correspondiente antes de ejecutar la consulta SQL.

## R3 — Parámetro de agrupación en herramientas existentes
DONDE una herramienta existente soporte rangos de fecha (`get_basic_stats`,
`get_breakdown_by_hacienda`, `get_custom_period_summary`), el sistema DEBE aceptar un
parámetro opcional `agrupacion` con los valores: `"dia"`, `"semana"`, `"mes"`, `"turno"`.

## R4 — Formato del resultado con agrupación
CUANDO se especifica `agrupacion`, el sistema DEBE retornar los resultados organizados en una
lista de grupos con identificador del período más las métricas correspondientes.

## R5 — Filtro por vehículo tractomula
DONDE una herramienta consulte `weighings`, el sistema DEBE aceptar un parámetro opcional
`tipo_vehiculo="tractomula"` y filtrar registros con `tractomula` no vacía.

## R6 — Filtro por vehículo vagon
DONDE una herramienta consulte `weighings`, el sistema DEBE aceptar un parámetro opcional
`tipo_vehiculo="vagon"` y filtrar registros con `vagon` no vacío.

## R7 — Nueva tool: get_avg_weighing_time
CUANDO se invoca `get_avg_weighing_time` con fechas válidas, el sistema DEBE retornar el
tiempo promedio entre pesajes consecutivos en minutos.

## R8 — Nueva tool: get_avg_weighing_time — datos insuficientes
SI el rango contiene menos de 2 pesajes, el sistema DEBE retornar `avg_time_minutes: 0.0`
con mensaje "Datos insuficientes".

## R9 — Nueva tool: get_anomaly_rate
CUANDO se invoca `get_anomaly_rate` con fechas válidas, el sistema DEBE retornar el
porcentaje de anomalías vs total de pesajes en el rango.

## R10 — Nueva tool: get_anomaly_rate — sin anomalías
SI no hay anomalías registradas, el sistema DEBE retornar `anomaly_rate_pct = 0.0`.

## R11 — Nueva tool: get_top_haciendas
CUANDO se invoca `get_top_haciendas` con fechas y `limite > 0`, el sistema DEBE retornar
ranking descendente de N haciendas por peso total.

## R12 — Nueva tool: get_top_haciendas — límite inválido
SI `limite <= 0`, el sistema DEBE lanzar `ToolExecutionError`.

## R13 — Nueva tool: get_period_comparison
CUANDO se invoca `get_period_comparison` con período actual y anterior, el sistema DEBE
retornar delta absoluto y porcentual para count, peso_total y peso_promedio.

## R14 — Nueva tool: get_period_comparison — período anterior vacío
SI el período anterior tiene 0 pesajes, el sistema DEBE retornar `delta_pct: null`.

## R15 — Desviación estándar en reportes de turno SMS
MIENTRAS el sistema genera un reporte de turno en `sms_service.py`, DEBE incluir la
desviación estándar del peso total.

## R16 — Métrica "std" en plantillas de reporte programado
El sistema DEBE registrar un handler `"std"` en `report_templates.py` que calcule la
desviación estándar del día actual.

## R17 — Parámetros inválidos en herramientas
SI una herramienta recibe parámetros inválidos, el sistema DEBE lanzar `ToolExecutionError`
con mensaje descriptivo.

## R18 — Rango de fecha vacío
SI un rango no tiene registros, el sistema DEBE retornar resultado vacío o con ceros, sin
lanzar excepción.

## R19 — Compatibilidad inversa de herramientas modificadas
DONDE se agreguen parámetros opcionales a herramientas existentes, el sistema DEBE mantener
compatibilidad: invocar sin los nuevos parámetros DEBE producir el mismo resultado que antes.

## R20 — Exposición de límites de control en GET /api/config
CUANDO un administrador consulta `GET /api/config`, el sistema DEBE incluir en la respuesta
una sección `"limites_control"` con los 7 parámetros: `z_threshold`, `window_size`,
`window_hours`, `max_vegetal_to_muestra`, `max_mineral_to_muestra`, `max_rate_change`,
`max_consecutive_anomalies`, con sus valores actuales desde `AgentConfig`.

## R21 — Persistencia de límites de control vía PUT /api/setup/controls
CUANDO un administrador envía `PUT /api/setup/controls` con el cuerpo conteniendo los 7
parámetros, el sistema DEBE:
- Validar rangos: `z_threshold` entre 1.0 y 10.0, `window_size` entre 30 y 500,
  `window_hours` entre 1 y 48, los ratios entre 0.01 y 1.0, `max_consecutive_anomalies`
  entre 1 y 20.
- Persistirlos en `config.yaml` (sección `agent`).
- Actualizar `app.state.agent_config` para que los cambios apliquen sin reinicio.
- Retornar el objeto `AgentConfig` completo actualizado.

## R22 — Card "Límites de Control" en AdminConfig
MIENTRAS el administrador visualiza la página de Configuración del Sistema, el sistema DEBE
mostrar una card con el título "Límites de Control" conteniendo 7 campos editables (uno por
parámetro), con el mismo estilo visual que las cards del dashboard principal.

## R23 — Formato de la card
La card DEBE mostrar cada parámetro con: etiqueta legible en español, input numérico con
unidad visible (σ, registros, horas, %), valor actual cargado desde `GET /api/config`, y
botón Guardar independiente o integrado con el guardado global de configuración.

## R24 — Tooltips de ayuda contextual
MIENTRAS el puntero del mouse se posa sobre la etiqueta o el ícono de ayuda de cada
parámetro, el sistema DEBE mostrar una burbuja (tooltip) con una explicación en español del
significado del parámetro y cómo afecta al sistema.

## R25 — check_thresholds() debe leer umbrales desde AgentConfig
El método `check_thresholds()` en `src/sql_tools.py` DEBE leer los umbrales
`max_vegetal_to_muestra` y `max_mineral_to_muestra` desde el `AgentConfig` inyectado, en
lugar de usar los valores hardcodeados `0.5` y `0.3`.

## R26 — Control de acceso a límites de control
El endpoint `PUT /api/setup/controls` DEBE requerir autenticación con rol `admin`
(dependencia `require_role("admin")`). GET /api/config ya tiene esta restricción.