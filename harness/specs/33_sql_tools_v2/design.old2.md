# Design — Feature 33: sql_tools_v2

## Archivos a modificar

| Archivo | Acción |
|---------|--------|
| `src/sql_tools.py` | Modificar: agregar 4 nuevas tools + modificar 3 existentes + helper shortcuts |
| `src/report_templates.py` | Modificar: agregar handler de métrica `"std"` |
| `src/sms_service.py` | Modificar: incluir desviación estándar en `generate_turn_report()` |
| `tests/test_sql_tools.py` | Crear: tests para nuevas tools + parámetros adicionales |
| `tests/test_report_templates.py` | Modificar: test para handler `"std"` |
| `tests/test_sms_service.py` | Modificar: test para std en turn report |

## Firmas nuevas

### Helper reutilizable

```python
@staticmethod
def _resolve_date_shortcut(
    periodo: str | None = None,
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
) -> tuple[str, str]:
    """Resuelve shortcuts de fecha a rangos (fecha_inicio, fecha_fin).

    Valores de periodo: 'hoy', 'ayer', 'ultimos_7_dias', 'mes_actual', 'personalizado'.
    Si periodo='personalizado', requiere fecha_inicio y fecha_fin explícitos.
    Si periodo es None, usa fecha_inicio/fecha_fin directamente.
    Lanza ToolExecutionError si faltan parámetros.
    """
```

### 4 nuevas tools en SqlTools

```python
def get_avg_weighing_time(
    self,
    fecha_inicio: str,
    fecha_fin: str,
    tipo_vehiculo: str | None = None,
    periodo: str | None = None,
) -> dict:
    """Tiempo promedio (minutos) entre pesajes consecutivos en el rango.

    Si periodo no es None, _resolve_date_shortcut() sobreescribe fecha_inicio/fecha_fin.
    """

def get_anomaly_rate(
    self,
    fecha_inicio: str,
    fecha_fin: str,
    tipo_vehiculo: str | None = None,
    periodo: str | None = None,
) -> dict:
    """Porcentaje de anomalías vs total de pesajes en el rango.

    Si periodo no es None, _resolve_date_shortcut() sobreescribe fecha_inicio/fecha_fin.
    """

def get_top_haciendas(
    self,
    fecha_inicio: str,
    fecha_fin: str,
    limite: int = 10,
    tipo_vehiculo: str | None = None,
    periodo: str | None = None,
) -> dict:
    """Ranking top N haciendas por peso total.

    Si periodo no es None, _resolve_date_shortcut() sobreescribe fecha_inicio/fecha_fin.
    """

def get_period_comparison(
    self,
    fecha_inicio: str,
    fecha_fin: str,
    periodo_anterior_inicio: str,
    periodo_anterior_fin: str,
    tipo_vehiculo: str | None = None,
    periodo: str | None = None,
) -> dict:
    """Comparación (delta + delta%) entre dos períodos.

    Si periodo no es None, _resolve_date_shortcut() sobreescribe fecha_inicio/fecha_fin.
    """
```

### 3 tools existentes modificadas (nuevos parámetros opcionales)

```python
# get_basic_stats — nuevos parámetros opcionales:
#   agrupacion: str | None = None  # "dia", "semana", "mes", "turno"
#   tipo_vehiculo: str | None = None
#   periodo: str | None = None  # shortcut de fecha (hoy, ayer, ultimos_7_dias, mes_actual, personalizado)

# get_breakdown_by_hacienda — nuevos parámetros opcionales:
#   agrupacion: str | None = None
#   tipo_vehiculo: str | None = None
#   periodo: str | None = None

# get_custom_period_summary — nuevos parámetros opcionales:
#   agrupacion: str | None = None
#   tipo_vehiculo: str | None = None
#   periodo: str | None = None
```

### TOOL_DEFINITIONS entries nuevas

Se agregan 4 nuevas entradas al diccionario `TOOL_DEFINITIONS` y se modifican las descripciones/parámetros de las 3 existentes. El total pasa de 13 a 17 herramientas.

### tool_map en execute_tool

Se agregan 4 nuevas entradas al `tool_map`.

## Contrato API (tool signatures)

### `get_avg_weighing_time`
```json
{
    "name": "get_avg_weighing_time",
    "description": "Calcula el tiempo promedio entre pesajes consecutivos en un rango de fechas.",
    "parameters": {
        "properties": {
            "fecha_inicio": {"type": "string", "description": "Fecha inicio en formato YYYY-MM-DD"},
            "fecha_fin": {"type": "string", "description": "Fecha fin en formato YYYY-MM-DD"},
            "tipo_vehiculo": {"type": "string", "description": "tractomula o vagon (opcional)"},
            "periodo": {"type": "string", "description": "Shortcut: hoy, ayer, ultimos_7_dias, mes_actual, personalizado (opcional)"}
        },
        "required": ["fecha_inicio", "fecha_fin"]
    }
}
```
**Respuesta:** `{ "avg_time_minutes": float, "count": int, "fecha_inicio": str, "fecha_fin": str }`

### `get_anomaly_rate`
```json
{
    "name": "get_anomaly_rate",
    "description": "Calcula la tasa de anomalías (% de pesajes marcados como anómalos vs total).",
    "parameters": {
        "properties": {
            "fecha_inicio": {"type": "string", "description": "Fecha inicio en formato YYYY-MM-DD"},
            "fecha_fin": {"type": "string", "description": "Fecha fin en formato YYYY-MM-DD"},
            "tipo_vehiculo": {"type": "string", "description": "tractomula o vagon (opcional)"},
            "periodo": {"type": "string", "description": "Shortcut (opcional)"}
        },
        "required": ["fecha_inicio", "fecha_fin"]
    }
}
```
**Respuesta:** `{ "total_weighings": int, "total_anomalies": int, "anomaly_rate_pct": float, "fecha_inicio": str, "fecha_fin": str }`

### `get_top_haciendas`
```json
{
    "name": "get_top_haciendas",
    "description": "Ranking descendente de haciendas por peso total en un rango de fechas.",
    "parameters": {
        "properties": {
            "fecha_inicio": {"type": "string", "description": "Fecha inicio en formato YYYY-MM-DD"},
            "fecha_fin": {"type": "string", "description": "Fecha fin en formato YYYY-MM-DD"},
            "limite": {"type": "integer", "description": "Número máximo de haciendas (default 10)"},
            "tipo_vehiculo": {"type": "string", "description": "tractomula o vagon (opcional)"},
            "periodo": {"type": "string", "description": "Shortcut (opcional)"}
        },
        "required": ["fecha_inicio", "fecha_fin"]
    }
}
```
**Respuesta:** `{ "ranking": [ {"hacienda_id": int, "codigo": str, "nombre": str, "total_weight": float, "count": int} ], "fecha_inicio": str, "fecha_fin": str }`

### `get_period_comparison`
```json
{
    "name": "get_period_comparison",
    "description": "Compara dos períodos: delta absoluto y delta porcentual para count, peso_total, peso_promedio.",
    "parameters": {
        "properties": {
            "fecha_inicio": {"type": "string", "description": "Inicio período actual YYYY-MM-DD"},
            "fecha_fin": {"type": "string", "description": "Fin período actual YYYY-MM-DD"},
            "periodo_anterior_inicio": {"type": "string", "description": "Inicio período anterior YYYY-MM-DD"},
            "periodo_anterior_fin": {"type": "string", "description": "Fin período anterior YYYY-MM-DD"},
            "tipo_vehiculo": {"type": "string", "description": "tractomula o vagon (opcional)"}
        },
        "required": ["fecha_inicio", "fecha_fin", "periodo_anterior_inicio", "periodo_anterior_fin"]
    }
}
```
**Respuesta:** `{ "periodo_actual": {...}, "periodo_anterior": {...}, "delta": {...}, "delta_pct": {...} }`

### `get_basic_stats` (modificada)
Nuevos parámetros opcionales: `agrupacion` (string: "dia"/"semana"/"mes"/"turno"), `tipo_vehiculo` (string: "tractomula"/"vagon"), `periodo` (string: shortcut).

**Respuesta (sin agrupación):** igual que antes `{ "count": int, "avg": float, "min": float, "max": float, "std": float }`

**Respuesta (con agrupación):** `{ "agrupacion": "dia", "grupos": [{"periodo": "2026-07-20", "count": int, "avg": float, "min": float, "max": float, "std": float}, ...] }`

### `get_breakdown_by_hacienda` (modificada)
Nuevos parámetros opcionales: `agrupacion`, `tipo_vehiculo`, `periodo`.

**Respuesta (sin agrupación):** igual que antes.

**Respuesta (con agrupación):** `{ "agrupacion": "mes", "grupos": [{"periodo": "2026-07", "haciendas": [...]}, ...] }`

### `get_custom_period_summary` (modificada)
Nuevos parámetros opcionales: `agrupacion`, `tipo_vehiculo`, `periodo`.

## Decisiones técnicas

1. **Helper `_resolve_date_shortcut` reutilizable**: Todos los shortcuts se resuelven en un único método estático en `SqlTools`. Esto evita duplicación y garantiza comportamiento consistente entre herramientas. El helper no depende del estado de la instancia.

2. **Parámetros opcionales con `None` default**: Los nuevos parámetros (`agrupacion`, `tipo_vehiculo`, `periodo`) son opcionales con valor por defecto `None`. Esto garantiza compatibilidad hacia atrás cuando el LLM invoca herramientas sin estos parámetros.

3. **Token bucket de `_weight_column` para filtro vehículo**: Se agrega un filtro `_apply_vehicle_filter(query, tipo_vehiculo)` aplicado al query antes de ejecutar, usando `Weighing.tractomula != ""` para tractomula y `Weighing.vagon != ""` para vagon.

4. **Validación en `ToolExecutionError`**: Los parámetros inválidos lanzan excepción nombrada `ToolExecutionError` con mensaje descriptivo, consistente con el patrón existente en `get_percentiles` y `get_moving_average`.

5. **Agrupación como post-procesamiento**: Para las herramientas modificadas, la agrupación se implementa como una capa de post-procesamiento sobre los resultados. El query SQL base retorna datos sin agrupar (con columna de período añadida), y luego se agrupan en Python. Esto evita tener que construir SQL dinámico complejo con `GROUP BY` condicional.

6. **Desviación estándar en SMS**: Se agrega el cálculo de `std` directamente en `generate_turn_report()` y como handler `_metric_std` en `report_templates.py`, usando `func.stddev_samp` de SQLAlchemy o cálculo manual en Python si no está disponible.

## Alternativas descartadas

1. **Invocar sql_tools desde report_templates**: Se descartó porque los handlers de métricas en `report_templates.py` actualmente usan SQL directo a través de SQLAlchemy, no la abstracción de `SqlTools`. Hacer que report_templates dependa de SqlTools crearía un acoplamiento innecesario y dificultaría el testing. En su lugar, `_metric_std` implementa su propio cálculo SQL directo, consistente con los demás handlers.

2. **Agrupación vía SQL puro con GROUP BY**: Se descartó porque la lógica de agrupación por "turno" (basada en la hora del día) es compleja de expresar en SQL puro y varía entre SQLite (dev) y MariaDB (prod). Post-procesar en Python es más portable y testeable.

3. **Un solo parámetro `periodo` que reemplace `fecha_inicio`/`fecha_fin`**: Se descartó porque rompe compatibilidad hacia atrás. En su lugar, `periodo` es un parámetro adicional que, si se especifica, sobreescribe `fecha_inicio`/`fecha_fin`. El LLM puede elegir usar shortcuts o fechas explícitas.

## Persistencia

No se requieren nuevas tablas, columnas ni migraciones. Todas las herramientas trabajan sobre las tablas existentes:
- `weighings` — para métricas de pesaje
- `anomaly_logs` — para tasa de anomalías
- `haciendas` — JOIN para top haciendas

## Impacto en APIs existentes

### Feature 8 — ai_agent (TOOL_DEFINITIONS consumido por LLM)

| Item | Cambio |
|------|--------|
| `TOOL_DEFINITIONS` en `sql_tools.py` | Se agregan 4 nuevas definiciones + se modifican 3 existentes (nuevos parámetros opcionales). El array crece de 13 a 17 entradas. |
| `agent_orchestrator.py` | No requiere cambios. El LLM recibe el catálogo aumentado y puede invocar las nuevas tools. `execute_tool()` sigue funcionando con el tool_map actualizado. |
| `main.py` | No requiere cambios. La línea `TOOL_DEFINITIONS` usada en el endpoint de chat carga automáticamente las nuevas definiciones. |

### Feature 7 — sms_service (reportes de turno)

| Item | Cambio |
|------|--------|
| `generate_turn_report()` en `sms_service.py` | Se agrega cálculo de desviación estándar al reporte de turno. No rompe compatibilidad (solo se agrega texto al reporte). |
| Formato de SMS emitido | Cambia de `"Reporte de turno [HH:MM - HH:MM]: N pesajes realizados, peso total: X.XX kg"` a `"Reporte de turno [HH:MM - HH:MM]: N pesajes realizados, peso total: X.XX kg, desviacion estandar: Y.YY kg"`. |

### Feature 35 — sms_scheduling_v2 (en pending, depende de F33)

Feature 35 consumirá las nuevas herramientas estadísticas para sus reportes. El diseño de F33 ya contempla las nuevas tools que F35 necesita.

### Feature 7 (legacy) — report_templates (handlers de métricas)

| Item | Cambio |
|------|--------|
| `METRIC_HANDLERS` en `report_templates.py` | Se agrega handler `"std"`. No hay cambios en handlers existentes. |

## Análisis de impacto en features existentes

### Búsqueda de consumidores

Se rastrearon todos los llamantes de los métodos de `SqlTools` y referencias a `TOOL_DEFINITIONS`:

| # | Archivo | Referencia | Impacto |
|---|---------|-----------|---------|
| 1 | `src/agent_orchestrator.py` | `from src.sql_tools import SqlTools, TOOL_DEFINITIONS` | Bajo — solo recibe catálogo más grande; `execute_tool()` por nombre no cambia |
| 2 | `src/main.py` | `from src.sql_tools import SqlTools` + `TOOL_DEFINITIONS` | Bajo — `SqlTools()` constructor sin cambios; catálogo más grande |
| 3 | `src/llm_client.py` | Referencia textual a `"get_basic_stats"` y `"get_shift_summary"` | Ninguno — strings literales no se modifican |
| 4 | `src/report_templates.py` | Sin dependencia directa de `sql_tools` | Medio — se agrega nuevo handler `"std"` |
| 5 | `src/sms_service.py` | `generate_turn_report()` usa SQL directo | Medio — se agrega std al reporte |
| 6 | `tests/test_sql_tools.py` | Tests de 13 tools existentes | Alto — se requieren tests nuevos; tests existentes deben seguir pasando |
| 7 | `tests/test_agent_orchestrator.py` | `mock_sql_tools = mock.MagicMock()` | Bajo — mocks no se ven afectados |
| 8 | `tests/test_ai_multi_turn_integration.py` | `mock_sql_tools = mock.MagicMock()` | Bajo — mocks no se ven afectados |

### Features afectadas

| Feature | Tipo | Impacto | Mitigación |
|---------|------|---------|-----------|
| **F8** ai_agent | Dependencia directa | Bajo: TOOL_DEFINITIONS crece, tool_map se expande | Sin cambios de interfaz; llamadas existentes siguen funcionando |
| **F7** sms_service | Dependencia indirecta (F8->F7) | Medio: generate_turn_report() cambia formato de salida | Solo se agrega campo, no se elimina nada |
| **F35** sms_scheduling_v2 | Dependiente de F33 (pending) | Planeado: consumirá nuevas tools | Se coordinará en diseño de F35 |
| **F34** alert_monitor | Dependiente de F33 (pending) | Planeado: consumirá get_anomaly_rate | Se coordinará en diseño de F34 |

### Compatibilidad hacia atrás

Todos los cambios en tools existentes agregan parámetros **opcionales** con valor por defecto `None`. Cero cambios de firma obligatoria. El `execute_tool()` existente pasa `**arguments` a las funciones, por lo que los argumentos nuevos simplemente no se pasan si no están en el dict.

Los tests existentes en `test_sql_tools.py` deben seguir pasando sin modificaciones.

## github_labels

`sdd`, `estadisticas`, `tools`, `sql`, `feature-33`
