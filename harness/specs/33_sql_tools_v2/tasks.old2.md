# Tasks — Feature 33: sql_tools_v2

> Orden sugerido: helpers primero, luego nuevas tools, luego modificación de existentes,
> luego SMS/std, luego tests.

---

## Fase 1 — Helper de shortcuts de fecha

- [ ] T1 — Implementar `_resolve_date_shortcut()` como método `@staticmethod` en `SqlTools`.
      Soportar `"hoy"`, `"ayer"`, `"ultimos_7_dias"`, `"mes_actual"`, `"personalizado"`.
      Lanzar `ToolExecutionError` si `periodo="personalizado"` pero faltan fechas.
      Cubre: R1, R2, R17.

- [ ] T2 — Agregar tests unitarios para `_resolve_date_shortcut`:
      - Test para cada shortcut: hoy, ayer, ultimos_7_dias, mes_actual.
      - Test para personalizado con fechas explícitas.
      - Test para personalizado sin fechas → ToolExecutionError.
      - Test para periodo inválido → ToolExecutionError.
      Cubre: R1, R2, R17.

## Fase 2 — Filtro por vehículo (helper reutilizable)

- [ ] T3 — Implementar método `_apply_vehicle_filter(query, tipo_vehiculo)` que agregue
      filtro WHERE según el valor: `"tractomula"` → `Weighing.tractomula != ""`,
      `"vagon"` → `Weighing.vagon != ""`. Lanzar `ToolExecutionError` si valor no reconocido.
      Cubre: R5, R6, R17.

- [ ] T4 — Agregar tests para `_apply_vehicle_filter`:
      - Test con `tipo_vehiculo="tractomula"`.
      - Test con `tipo_vehiculo="vagon"`.
      - Test con tipo_vehiculo inválido → ToolExecutionError.
      - Test con `tipo_vehiculo=None` (sin filtro).
      Cubre: R5, R6, R17.

## Fase 3 — Nuevas tools (4)

- [ ] T5 — Implementar `get_avg_weighing_time()` en `SqlTools`.
      Calcular diferencia promedio entre pesajes consecutivos ordenados por `(fecha, hora)`.
      Retornar tiempo promedio en minutos. Si count < 2, retornar "Datos insuficientes".
      Cubre: R7, R8, R18.

- [ ] T6 — Implementar `get_anomaly_rate()` en `SqlTools`.
      Contar total de pesajes en rango, contar anomalías en `AnomalyLog`, calcular porcentaje.
      Si count=0, retornar 0 anomalías.
      Cubre: R9, R10, R18.

- [ ] T7 — Implementar `get_top_haciendas()` en `SqlTools`.
      JOIN con `Hacienda`, agrupar, ordenar por peso total DESC, limitar a `limite` registros.
      Validar `limite > 0` (lanzar ToolExecutionError si no).
      Cubre: R11, R12, R18.

- [ ] T8 — Implementar `get_period_comparison()` en `SqlTools`.
      Ejecutar mismas agregaciones para dos períodos, calcular delta y delta%.
      Manejar división por cero (delta_pct = null cuando periodo_anterior tenga count=0).
      Cubre: R13, R14, R18.

- [ ] T9 — Registrar las 4 nuevas tools en `TOOL_DEFINITIONS` con sus schemas JSON.
      Agregar entradas al `tool_map` en `execute_tool()`.
      Cubre: R7, R9, R11, R13, R19.

- [ ] T10 — Agregar tests unitarios para `get_avg_weighing_time`:
      - Test camino feliz con 3+ pesajes.
      - Test con 1 solo pesaje → "Datos insuficientes".
      - Test con rango vacío → count=0, avg=0.
      Cubre: R7, R8, R18.

- [ ] T11 — Agregar tests unitarios para `get_anomaly_rate`:
      - Test con anomalías en el rango.
      - Test sin anomalías → 0.0%.
      - Test con rango vacío.
      Cubre: R9, R10, R18.

- [ ] T12 — Agregar tests unitarios para `get_top_haciendas`:
      - Test camino feliz con 2+ haciendas.
      - Test con limite=5.
      - Test con limite <= 0 → ToolExecutionError.
      Cubre: R11, R12.

- [ ] T13 — Agregar tests unitarios para `get_period_comparison`:
      - Test con ambos períodos con datos.
      - Test con período anterior vacío → delta_pct null.
      - Test con período actual vacío.
      Cubre: R13, R14, R18.

## Fase 4 — Modificar 3 tools existentes

- [ ] T14 — Modificar `get_basic_stats()`:
      Agregar parámetros opcionales `agrupacion`, `tipo_vehiculo`, `periodo`.
      Integrar `_resolve_date_shortcut()` y `_apply_vehicle_filter()`.
      Implementar post-procesamiento de agrupación (retornar lista de grupos).
      Cubre: R1, R2, R3, R4, R5, R6, R17, R18, R19.

- [ ] T15 — Modificar `get_breakdown_by_hacienda()`:
      Agregar parámetros opcionales `agrupacion`, `tipo_vehiculo`, `periodo`.
      Integrar helpers de shortcut y filtro.
      Implementar agrupación por período + hacienda.
      Cubre: R1, R2, R3, R4, R5, R6, R17, R18, R19.

- [ ] T16 — Modificar `get_custom_period_summary()`:
      Agregar parámetros opcionales `agrupacion`, `tipo_vehiculo`, `periodo`.
      Integrar helpers de shortcut y filtro.
      Implementar agrupación por período.
      Cubre: R1, R2, R3, R4, R5, R6, R17, R18, R19.

- [ ] T17 — Actualizar los schemas en `TOOL_DEFINITIONS` para las 3 tools modificadas,
      agregando las nuevas propiedades opcionales en sus schemas JSON.
      Cubre: R3, R5, R19.

- [ ] T18 — Agregar tests para `get_basic_stats` con agrupación y filtro vehículo:
      - Test con agrupacion="dia".
      - Test con agrupacion="turno".
      - Test con tipo_vehiculo="tractomula".
      - Test con agrupacion inválida → ToolExecutionError.
      - Test sin nuevos parámetros (compatibilidad) → mismo resultado que antes.
      Cubre: R3, R4, R5, R6, R17, R19.

- [ ] T19 — Agregar tests para `get_breakdown_by_hacienda` con agrupación y filtro vehículo:
      - Test con agrupacion="semana".
      - Test con tipo_vehiculo="vagon".
      - Test de compatibilidad hacia atrás.
      Cubre: R3, R4, R5, R6, R19.

- [ ] T20 — Agregar tests para `get_custom_period_summary` con agrupación y filtro vehículo:
      - Test con agrupacion="mes".
      - Test con tipo_vehiculo="tractomula".
      - Test de compatibilidad hacia atrás.
      Cubre: R3, R4, R5, R6, R19.

## Fase 5 — Desviación estándar en SMS

- [ ] T21 — Modificar `generate_turn_report()` en `src/sms_service.py`:
      Agregar consulta de desviación estándar del peso total en el turno.
      Incluir en el string del reporte: `", desviacion estandar: X.XX kg"`.
      Cubre: R15.

- [ ] T22 — Agregar handler `_metric_std` en `src/report_templates.py`:
      Registrar con `@_register_metric("std")`.
      Calcular stddev de peso_total del día actual.
      Retornar `"Desviacion estandar: X.XX kg"`.
      Cubre: R16.

- [ ] T23 — Agregar tests para std en SMS:
      - Test que `generate_turn_report()` incluya "desviacion estandar" en el output.
      - Test del handler `_metric_std` en report_templates.
      Cubre: R15, R16.

## Fase 6 — Verificación final

- [ ] T24 — Ejecutar tests existentes de sql_tools y verificar que ningún test legacy
      se rompe (compatibilidad hacia atrás).
      Cubre: R19.

- [ ] T25 — Verificar que `TOOL_DEFINITIONS` tiene exactamente 17 entradas (13 legacy + 4 nuevas).
      Cubre: R7, R9, R11, R13.
