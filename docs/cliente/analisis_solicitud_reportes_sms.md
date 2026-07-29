# Análisis de Solicitud 01 - Nuevas Reatures: Reportes y Alertas SMS

> **Fecha:** 2026-07-14
> **Restricción crítica:** SIP-Edge en campo solo tiene acceso SMS (modem 4G Quectel EC25).
> **No hay acceso Ethernet ni dashboard web disponible para los corresponsales.**
> Toda entrega de información es vía SMS (texto plano, ~160 chars por mensaje, concatenables).

---

## 1. Aclaraciones sobre la solicitud
Los siguientes terminos los interpretamos de acuerdo al flujo establecido, sin embargo esperamos que pueda confirmar o aclarar si se trata del termino entendido o en caso contrario; explicar de forma un poco mas explicita a que refiere el termino utilizado.

| Término del cliente | Realidad en SIP-Edge |
|---------------------|---------------------|
| **Proveedor** | Es la **Hacienda**. Ya existe como entidad (tabla `haciendas`, tool `get_breakdown_by_hacienda`). |
| **Destino** | Toda la caña va a la misma fábrica. No aplica filtro por destino. |
| **Producto** | Equivale a `tipo_cosecha` (Cosechadora / Cosecha manual). Ya existe como columna en `weighings`. |
| **Vehículo** | Ya existe como `tractomula` y `vagon` en `weighings`. No expuesto como filtro en tools actuales. |

---

## 2. Features implementables (SMS)

### Feature propuesta: `sms_analytics_v2` — Reportes SMS enriquecidos + Alertas automáticas

**Depende de:** F7 (`sms_service`), F8 (`ai_agent`), F27 (`sms_persistence`) — todas `done`.

#### 2.1 — Filtros y agrupación nuevos

| Qué piden | Cómo se implementa | Nueva tool / cambio |
|-----------|-------------------|---------------------|
| Rangos de fecha: Hoy, Ayer, Últimos 7 días, Mes actual, Personalizado | Shortcuts de fecha en tools. El LLM resuelve "hoy" → `date.today()`. Nueva tool `resolve_date_range` que traduce shortcuts a fechas YYYY-MM-DD. | Nueva tool + actualizar `TOOL_DEFINITIONS` |
| Agrupar por Día, Semana, Mes, Turno | Nuevo parámetro `agrupacion` en tools existentes. Turno ya existe en `get_shift_summary`. | Nuevo parámetro en `get_basic_stats`, `get_trend`, `get_material_composition` |
| Filtro por vehículo (tractomula/vagon) | Nuevo parámetro opcional `vehiculo` en tools de consulta. | Nuevo parámetro en tools existentes |

#### 2.2 — Métricas de operación nuevas

| Métrica | Estado actual | Qué se necesita |
|---------|--------------|-----------------|
| **Desviación estándar** | ✅ Ya existe en `get_basic_stats` (campo `std`) | Nada. Solo asegurar que el LLM la incluya en el resumen. |
| **Tiempo promedio por pesaje** | ❌ No existe | Nueva tool `get_avg_weighing_time`: calcula delta entre `created_at` de pesajes consecutivos en un rango de fechas. |
| **Tasa de rechazo/reproceso** | ❌ No existe | Nueva tool `get_anomaly_rate`: `COUNT(anomaly_log) / COUNT(weighings)` en rango de fechas. |
| **Top 5 haciendas con más peso** | ❌ No existe como ranking | Nueva tool `get_top_haciendas`: `GROUP BY hacienda_id ORDER BY SUM(peso_total) DESC LIMIT N`. |
| **Comparativo vs período anterior** | ❌ No existe | Nueva tool `get_period_comparison`: corre mismo query en período actual y período anterior, retorna Δ absoluto y Δ%. |
| **OEE de báscula** | ❌ No existe infraestructura | **No implementable** (ver sección 3). |

**Total tools nuevas:** 4 (`get_avg_weighing_time`, `get_anomaly_rate`, `get_top_haciendas`, `get_period_comparison`)
**Tools modificadas:** 3 (agregar `agrupacion` y `vehiculo` como parámetros opcionales)

#### 2.3 — Alertas estadísticas automáticas

| Alerta | Cómo se implementa |
|--------|-------------------|
| **Anomalía > X%**: operador fuera del promedio | El engine de anomalías ya existe (`detect_anomalies` en `anomaly_detector.py`). Nueva condición: si `z_score > umbral_personalizable`, disparar SMS al admin. |
| **Caída de producción**: >20% menos pesajes vs promedio | Nuevo monitor en el loop del scheduler. Compara `COUNT(weighings)` de hoy (hasta ahora) vs promedio móvil de últimos 7 días. Si cae >20%, envía alerta SMS. |
| **Outliers**: fuera de 3 desviaciones estándar | Ya cubierto por `detect_anomalies` (Z-Score). Ajustar el umbral a 3σ. |
| **Inactividad**: 2h sin pesajes en horario laboral | Nuevo monitor de heartbeat. Si `MAX(weighings.created_at)` > 2h atrás y estamos en horario laboral (L-V 6am-10pm, S 6am-2pm), envía alerta SMS. |

**Infraestructura nueva necesaria:**
- `AlertMonitor`: clase que corre en el scheduler de `sms_service`, evalúa 4 condiciones cada N minutos.
- Tabla `alert_log` (o columna `alert_type` en `sms_messages`): registro de alertas enviadas para evitar duplicados.
- Configuración en `config.yaml`:
  ```yaml
  alerts:
    anomaly_threshold_pct: 15.0
    production_drop_pct: 20.0
    inactivity_minutes: 120
    outlier_stddev: 3.0
    check_interval_minutes: 30
    active_hours_weekday: [6, 22]
    active_hours_saturday: [6, 14]
  ```

#### 2.4 — Formato de entrega SMS

| Qué piden | Viabilidad SMS |
|-----------|---------------|
| **Resumen ejecutivo** (3 bullets) | ✅ **Perfecto para SMS.** El LLM ya genera resúmenes narrativos. Nueva instrucción de sistema: *"Responde SIEMPRE con 3 bullets: Total pesajes, anomalías detectadas, cambio vs período anterior."* |
| **Gráfico PNG** | ❌ Imposible por SMS (ver sección 3) |
| **Excel/CSV** | ❌ Imposible por SMS (ver sección 3) |
| **PDF** | ❌ Imposible por SMS (ver sección 3) |
| **Tabla formateada** | ❌ SMS no permite formato rico (ver sección 3) |

#### 2.5 — Configuración adicional

| Qué piden | Implementación |
|-----------|---------------|
| **Zona horaria** GMT-5 Bogotá | ✅ Agregar `timezone: "America/Bogota"` en `config.yaml`. Todos los schedulers usan `pytz` para convertir. |
| **Días activos** (L-V, L-S) | ✅ Agregar `active_days: [1,2,3,4,5]` en `config.yaml`. El scheduler omite envíos en días inactivos. |
| **Idioma/Formato números** | ✅ Ya en español. Agregar `number_format: es_CO` para separadores de miles (`.`) y decimales (`,`). |
| **Plantillas pre-hechas** | ✅ Nueva tabla `report_templates` (ya existe en F17) o extender la existente con `template_type`: `gerencia`, `operaciones`, `calidad`. Cada plantilla define métricas y umbrales propios. |

#### 2.6 — Flujos SMS programados

| Horario | Reporte | Implementación |
|---------|---------|---------------|
| **6:00 am** — "Resumen Ayer" | Cantidad, promedio, top haciendas, anomalías | Nueva entrada en el scheduler de `sms_service`. Invoca `get_daily_summary(fecha=ayer)` + `get_breakdown_by_hacienda` + `detect_anomalies`. Formato: 3-bullet SMS. |
| **Cada 4 horas** — "Alerta Operación" | Solo si hay anomalías o caída | El `AlertMonitor` (sección 2.3) evalúa condiciones. Si alguna se dispara, envía SMS. Si no hay novedades, **no envía nada** (modo solo-excepción). |
| **Lunes 7:00 am** — "Resumen Semanal" | Tendencia, comparativo, desviación | Nueva entrada en el scheduler. Invoca `get_trend(semana)` + `get_period_comparison(vs_semana_anterior)` + `get_basic_stats`. |

---

## 3. Items NO implementables

| Solicitud del cliente | Motivo técnico |
|-----------------------|---------------|
| **Gráficos PNG** (tendencia, barras, torta) | SMS es transporte de texto. No soporta imágenes, binarios ni MMS. No hay acceso ethernet para servir las imágenes por otro canal. |
| **Adjuntar Excel/CSV** | SMS no transporta archivos. No hay canal alternativo (sin ethernet, sin email). |
| **Adjuntar PDF** | Misma restricción: SMS no transporta binarios. |
| **Tablas formateadas** | SMS es texto plano. Se puede usar formato ASCII rudimentario (guiones y pipes), pero no tablas ricas con alineación, colores ni celdas. |
| **Dashboard web** | Los corresponsales no tienen acceso ethernet ni navegador en campo. El dashboard admin existe (`/admin/reportes`) pero solo es accesible al admin *in situ*. |
| **Filtro por Destino** | Toda la caña va a la misma fábrica. Agregar este filtro no aporta valor porque siempre devolvería el mismo resultado. |
| **Filtro por Proveedor** | Ya está cubierto por el filtro de **Hacienda** (tabla `haciendas`, tool `get_breakdown_by_hacienda`). El cliente usó "proveedor" como sinónimo de hacienda. |
| **OEE de báscula** | OEE = Disponibilidad × Rendimiento × Calidad. Requiere: (a) tracking de uptime/downtime de la báscula, (b) velocidad nominal de pesaje, (c) tasa de defectos. Ninguna de estas métricas existe en SIP-Edge hoy. Implementar OEE real requeriría sensores de disponibilidad + contador de tiempo operativo. Se puede aproximar con `tiempo_promedio_pesaje` y `tasa_rechazo` como proxies simplificados. |

---

## 4. Advertencia técnica — Impacto en el LLM local

Cada herramienta de análisis estadístico que se agregue se registra en `TOOL_DEFINITIONS`
como una definición de función OpenAI-style. El inventario actual (12 tools) ya consume
aproximadamente **3,200 tokens** solo en definiciones. Con las 4 tools nuevas propuestas
más las 3 modificadas, el bloque de herramientas crecerá a ~**4,500 tokens**.

Esto tiene una consecuencia directa en el EdgeBox, donde el LLM corre localmente sobre
**llama.cpp** con modelos pequeños:

| Modelo | Tamaño | Ventana de contexto |
|--------|--------|-------------------|
| Qwen2.5 1.5B (Q4_K_M) | 1.1 GB | 32K tokens |
| Gemma 4 2B (Q4_K_M) | 2.9 GB | 8K tokens |
| Qwen3.5 2B (Q2_K_XL) | 922 MB | 32K tokens |

> ⚠️ **El tiempo de respuesta del LLM crecerá linealmente con el tamaño del prompt.**
>
> - Las definiciones de herramientas se envían en **cada consulta SMS** al LLM, no solo
>   cuando se usan.
> - Un modelo de 1.5B parámetros procesando ~5K tokens de tools + historial de conversación
>   + consulta del usuario puede tardar entre **30 y 60 segundos** adicionales respecto al
>   inventario actual, dependiendo del modelo y la carga del sistema.
> - Si en el futuro se agregan más herramientas sin depurar las obsoletas, el prompt puede
>   saturar la ventana de contexto de modelos pequeños como Gemma 4 (8K), dejando poco
>   espacio para el historial de la conversación y los resultados de tools anteriores.
>
> **Recomendación:** Evaluar, antes de cada nuevo despliegue, si el tiempo de respuesta
> total (inferencia LLM + ejecución SQL + envío SMS) se mantiene dentro de un umbral
> aceptable para el corresponsal en campo (≤ 60 segundos). Si se excede, considerar:
> - Usar un modelo de mayor capacidad (agregando hardware especializado en inferencia).
> - Agrupar herramientas relacionadas en una sola tool con parámetro `mode`.

