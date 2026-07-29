# Design — AlertMonitor

> Feature 34: Monitor de Alertas Automáticas
> ERS Ref: ERS_V1.4_Adendas.md §A.3, §A.5

---

## Resumen

Se implementa un `AlertMonitor` como tarea asíncrona periódica dentro de FastAPI (lifespan). Evalúa 6 condiciones contra la base de datos cada `check_interval_minutes` minutos durante horario laboral activo. Las alertas se persisten en una nueva tabla `alert_log` para deduplicación y resolución automática. Los SMS de alerta se envían usando el `SMSService` existente.

---

## Archivos a crear

| Archivo | Propósito |
|---------|-----------|
| `src/alert_monitor.py` | Clase `AlertMonitor` con evaluación periódica y lógica de 6 condiciones |
| `tests/test_alert_monitor.py` | Tests unitarios para `AlertMonitor` |

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `src/config.py` | Agregar dataclass `AlertConfig` con los 12 umbrales configurables |
| `src/config.py` | Modificar `load_config()` para cargar sección `alerts:` de config.yaml |
| `src/config.py` | Modificar `_atomic_write_sections()` para preservar sección `alerts:` |
| `src/models.py` | Agregar modelo ORM `AlertLog` (tabla `alert_log`) |
| `src/main.py` | Inicializar `AlertMonitor` en lifespan, iniciar/detener tarea, agregar router de consulta de alertas |
| `config.yaml` | Agregar sección `alerts:` con valores por defecto |

---

## Firmas nuevas

### AlertConfig (src/config.py)

```python
@dataclass(frozen=True)
class AlertConfig:
    materia_extrana_pct: float = 0.15
    z_threshold: float = 3.0
    zscore_window_size: int = 120
    zscore_window_hours: int = 4
    muestra_min_kg: float = 10.0
    production_drop_pct: float = 0.20
    production_drop_window_days: int = 7
    outlier_stddev: float = 3.0
    inactivity_minutes: int = 120
    check_interval_minutes: int = 15
    active_hours_weekday: str = "06:00-18:00"
    active_hours_saturday: str = "06:00-12:00"
```

### AlertLog (src/models.py)

Nuevo modelo ORM para la tabla `alert_log`. Ver sección Persistencia.

### AlertMonitor (src/alert_monitor.py)

```python
class AlertMonitor:
    """Monitor periódico de condiciones de alerta.

    Evalúa 6 condiciones en un loop asíncrono y envía SMS al administrador
    cuando se detectan nuevas alertas. Deduplica contra alert_log activas.
    """

    def __init__(
        self,
        db_session_factory,
        sms_service,
        config: AlertConfig,
    ) -> None: ...

    def start(self) -> None:
        """Lanza la corutina asíncrona del evaluador periódico."""

    def stop(self) -> None:
        """Cancela la corutina del evaluador."""

    async def _evaluation_loop(self) -> None:
        """Bucle principal: duerme check_interval, luego evalúa condiciones."""

    async def _check_all_conditions(self) -> None:
        """Evalúa las 6 condiciones secuencialmente."""

    def _check_materia_extrana(self) -> list[dict]:
        """Busca pesajes con (mineral+vegetal)/muestra > materia_extrana_pct."""

    def _check_zscore(self) -> list[dict]:
        """Busca pesajes con Z-Score del peso total > z_threshold en ventana móvil."""

    def _check_muestra_insuficiente(self) -> list[dict]:
        """Busca pesajes con peso_muestra < muestra_min_kg."""

    def _check_production_drop(self) -> dict | None:
        """Compara conteo de hoy vs promedio últimos 7 días hábiles."""

    def _check_outliers(self) -> list[dict]:
        """Busca pesajes fuera de N desviaciones estándar de la media del día."""

    def _check_inactivity(self) -> dict | None:
        """Verifica si no hay pesajes en los últimos inactivity_minutes."""

    @staticmethod
    def _is_business_hours(
        weekday_hours: str, saturday_hours: str
    ) -> bool:
        """Determina si la hora actual está dentro del horario laboral activo."""

    def _is_alert_active(self, alert_type: str) -> bool:
        """Consulta si existe una alerta activa sin resolver del tipo dado."""

    def _create_alert(self, alert_type: str, severity: str,
                      metric_value: float, threshold: float,
                      detail: str) -> int | None:
        """Persiste una alerta en alert_log. Retorna id o None si ya existe activa."""

    def _resolve_alert(self, alert_type: str) -> None:
        """Marca alertas activas del tipo dado como resueltas."""

    def _send_sms_for_alert(self, alert_id: int, alert_type: str,
                            detail: str) -> None:
        """Envía SMS y marca sent_sms = True."""
```

### Endpoint nuevo (opcional)

```python
@alert_router.get("/api/alerts/history")
# Retorna historial paginado de alert_log
```

Este endpoint permite al admin consultar el historial de alertas desde el frontend. No es obligatorio para la feature (el core es el monitoreo automático), pero se incluye como API de soporte.

---

## Alternativa descartada

**Alternativa:** Integrar las condiciones de alerta dentro del `AgentOrchestrator` existente, reutilizando el flujo LLM para generar el texto del SMS.

**Motivo de descarte:** El `AgentOrchestrator` depende del LLM local para generar narrativa, lo que introduce latencia (~5-15s), riesgo de fallo del LLM, y un gasto de tokens innecesario para mensajes de alerta estandarizados (formulario fijo: "ALERTA [tipo]: [detalle]"). Además, el LLM está diseñado para consultas ad-hoc de corresponsales, no para monitoreo proactivo. Separar el `AlertMonitor` como un servicio independiente sigue el principio de responsabilidad única (S de SOLID) y permite que las alertas funcionen incluso si el LLM está caído.

---

## Persistencia

### Tabla nueva: `alert_log`

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK |
| alert_type | VARCHAR(32) | NO | | `materia_extrana`, `zscore_anomaly`, `muestra_insuficiente`, `production_drop`, `outlier`, `inactivity` |
| severity | VARCHAR(16) | NO | `warning` | `info`, `warning`, `critical` |
| metric_value | DECIMAL(12,4) | YES | NULL | Valor métrico que disparó la alerta |
| threshold | DECIMAL(12,4) | YES | NULL | Umbral configurado contra el cual se evaluó |
| detail | TEXT | YES | NULL | Descripción legible de la alerta |
| status | VARCHAR(16) | NO | `active` | `active`, `resolved` |
| sent_sms | BOOLEAN | NO | FALSE | Indica si ya se envió SMS de notificación |
| resolved_at | TIMESTAMP | YES | NULL | Momento en que se resolvió la condición |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | |

Índices:
- `(alert_type, status)` — para deduplicación y resolución rápida
- `(created_at)` — para consultas de historial ordenadas por fecha

### Migraciones
1. `database/migrations/2026_07_27_000000_create_alert_log_table.sql` — CREATE TABLE alert_log

---

## Impacto en APIs existentes

### Endpoint nuevo: `GET /api/alerts/history`

Responde con historial paginado de alertas. Contrato:

```
GET /api/alerts/history?page=1&page_size=20&status=active&alert_type=materia_extrana
Authorization: Bearer <token>
```

Respuesta:
```json
{
  "items": [
    {
      "id": 1,
      "alert_type": "materia_extrana",
      "severity": "warning",
      "metric_value": 0.23,
      "threshold": 0.15,
      "detail": "ALERTA Materia extraña: Pesaje #1234 - Hacienda LA PRADERA - Suerte A12 - (mineral+vegetal)/muestra = 23.0% supera 15.0%",
      "status": "active",
      "sent_sms": true,
      "resolved_at": null,
      "created_at": "2026-07-27T14:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### Endpoint nuevo (futuro): `PUT /api/alerts/{id}/resolve`

Permite al admin resolver manualmente una alerta (para casos donde la condición ya no aplica pero la resolución automática no se disparó). No es obligatorio para el MVP de esta feature.

---

## Análisis de impacto en features existentes

### Feature 1 — system_config (config.yaml)
- **Impacto:** Se agrega la sección `alerts:` en config.yaml. Las funciones `load_config()` y `_atomic_write_sections()` en `src/config.py` deben modificarse para cargar y preservar esta sección.
- **Compatibilidad:** Hacia atrás completa. Si la sección `alerts:` no existe en config.yaml, se usan valores por defecto de `AlertConfig()`.
- **Tests:** `test_config.py` debe actualizarse con tests para `AlertConfig` y carga de sección `alerts:`.

### Feature 7 — sms_service (SMSService)
- **Impacto:** `AlertMonitor` inyecta `sms_service` y llama a `send_alert_to_admins()` para enviar SMS de alerta. No se modifica la interfaz de `SMSService`.
- **Compatibilidad:** Completa. Sin cambios en `sms_service.py`.

### Feature 8 — ai_agent (AnomalyDetector y AgentOrchestrator)
- **Impacto:** El `AlertMonitor` replica la detección Z-Score (R2) ya existente en `AnomalyDetector._detect_zscore()` para garantizar cobertura en el ciclo periódico y registro unificado en `alert_log`. La detección Z-Score original (por pesaje, en tiempo real, vía LLM) sigue operando independientemente. Las alertas de `AlertMonitor` usan SMS directo (sin LLM), lo que las hace inmunes a fallos del motor de inferencia. La condición R5 (outlier 3 sigma del día) es diferente de la detección Z-Score del AnomalyDetector (que usa ventana móvil de N registros).

### Feature 33 — sql_tools_v2
- **Impacto:** Las herramientas `get_anomaly_rate`, `get_basic_stats` (para std) y `detect_anomalies` podrían ser reutilizadas internamente por el `AlertMonitor` para eficiencia. Sin embargo, se opta por SQL directo en `AlertMonitor` para evitar la sobrecarga del catálogo `TOOL_DEFINITIONS` (ver NFR-V14-01).
- **Compatibilidad:** Completa. No se modifican herramientas existentes.

### Feature 27 — sms_persistence
- **Impacto:** Los SMS enviados por `AlertMonitor` se persisten automáticamente porque el `SMSService` ya tiene integrada la persistencia.
- **Compatibilidad:** Completa.

---

## Documentación del impacto en prompt del LLM (NFR-V14-01)

El `AlertMonitor` NO agrega herramientas al catálogo `TOOL_DEFINITIONS`. La evaluación de condiciones se realiza mediante SQL directo (SQLAlchemy queries), no mediante el LLM. Por lo tanto, esta feature no impacta el tamaño del prompt ni el tiempo de inferencia del LLM local.

Sin embargo, se documenta como advertencia general: cualquier feature futura que agregue herramientas a `TOOL_DEFINITIONS` debe considerar que cada tool agrega ~200-400 tokens al prompt, y que el tiempo de inferencia en los modelos del EdgeBox (Qwen2.5 1.5B, Gemma 4 2B, Qwen3.5 2B) crece linealmente con el tamaño del prompt. Si el catálogo excede ~25 herramientas, se recomienda evaluar:
- (a) Usar modelo de mayor capacidad (Gemma 4 2B)
- (b) Agrupar herramientas relacionadas en una sola con parámetros unificados
- (c) Migrar lógica de consultas frecuentes a endpoints dedicados (evitando el LLM)

---

## Pruebas humanas (PH)

### PH-1 — Happy path: alerta por materia extraña
1. Crear un pesaje con `peso_muestra=50.0`, `peso_mineral=10.0`, `peso_vegetal_extrano=5.0` (ratio = 0.30 > 0.15)
2. Esperar el ciclo de evaluación (máx 15 min) o ejecutar evaluación manual
3. Verificar que se genera un registro en `alert_log` con `alert_type='materia_extrana'` y `status='active'`
4. Verificar que el admin recibe un SMS con el detalle de la alerta

### PH-2 — Sad path: alerta no se reenvía (deduplicación)
1. Ejecutar el escenario de PH-1
2. Sin resolver la alerta, agregar otro pesaje que también supere el umbral
3. Ejecutar otra evaluación
4. Verificar que NO se crea un nuevo registro en `alert_log` para `materia_extrana`
5. Verificar que NO se envía un nuevo SMS

### PH-3 — Edge path: resolución automática de alerta
1. Tener una alerta activa de materia extraña (PH-1)
2. Corregir los datos: modificar los pesajes o agregar pesajes normales que estén bajo el umbral
3. Ejecutar evaluación
4. Verificar que la alerta original cambia a `status='resolved'` con `resolved_at` no nulo

### PH-4 — Happy path: alerta por inactividad
1. Asegurarse de estar en horario laboral activo (ej. lunes 10:00)
2. No registrar ningún pesaje por más de `inactivity_minutes` (default 120 min, o reducir para la prueba)
3. Verificar que se genera alerta `inactivity` y se envía SMS

### PH-5 — Configuración en config.yaml
1. Modificar `materia_extrana_pct` de 0.15 a 0.25 en config.yaml
2. Crear un pesaje con ratio 0.20 (entre 0.15 y 0.25)
3. Verificar que NO se dispara alerta (el umbral ahora es 0.25)
4. Crear un pesaje con ratio 0.30
5. Verificar que SÍ se dispara alerta

---

## github_labels

`alert-monitor`, `automation`, `sms`, `monitoring`
