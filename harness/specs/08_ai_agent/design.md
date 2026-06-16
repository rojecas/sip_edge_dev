# Design — Sistema Inteligente de Reportería y Detección de Anomalías (TinyLLM)

> Feature 8 — ai_agent  
> Dependencies: 6 (weighing_capture), 7 (sms_service), 12 (password_reset_sms)

---

## Arquitectura

### Vista general de los tres flujos

```
┌──────────────────────────────────────────────────────────────────┐
│                        AGENT ORCHESTRATOR                       │
│  ┌─────────────┐  ┌────────────────┐  ┌──────────────────────┐  │
│  │ Report      │  │ Anomaly        │  │ SMS Query            │  │
│  │ Templates   │  │ Detector       │  │ Handler              │  │
│  │ (CRUD +     │  │ (3 capas:      │  │ (LLM + SQL Tools)    │  │
│  │  Scheduler) │  │  Z-Score       │  │                      │  │
│  │             │  │  Relational    │  │  ┌────────────────┐  │  │
│  │ SQL direct  │  │  Temporal)     │  │  │ LlamaClient    │  │  │
│  │ (no LLM)    │  │                │  │  │ (HTTP + FC)    │  │  │
│  │             │  │  ──anomaly──►  │  │  └────────────────┘  │  │
│  │             │  │  LlamaClient   │  │         │             │  │
│  │             │  │  ──SMS──►      │  │         ▼             │  │
│  │             │  │  SMSService    │  │  ┌────────────────┐  │  │
│  │             │  │                │  │  │ SQL Tools (12) │  │  │
│  │             │  │                │  │  └────────────────┘  │  │
│  └─────────────┘  └────────────────┘  └──────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### Flujo de detección de anomalías

```
POST /api/weighings → 201 → AnomalyDetector.run(weighing)
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
              Z-Score    Relacional    Temporal
                    │           │           │
                    └───────────┼───────────┘
                                ▼
                         ¿alguna anomalía?
                           /         \
                          Sí          No
                          │           │
                          ▼           ▼
                   LlamaClient    Fin (log
                   (narrativa)    sin anomalía)
                          │
                          ▼
                   SMSService.send_sms()
                          │
                          ▼
                   anomaly_log.insert()
```

### Flujo de consulta SMS

```
SMS entrante → IncomingSmsDispatcher
                → ¿comando conocido?
                    ├─ Sí → handler existente (emergency, password_reset)
                    └─ No → AgentOrchestrator.handle_query(sender, text)
                              │
                              ▼
                         LlamaClient.chat(msgs + tools)
                              │
                              ▼
                         ¿tool_calls?
                            ├─ Sí → ejecutar SQL Tool → resultado real
                            │        └─ pasar resultado al LLM
                            │           └─ LLM parafrasea
                            └─ No → error / respuesta directa
                              │
                              ▼
                         SMSService.send_sms(sender, respuesta)
```

---

## Archivos a crear

| Archivo | Propósito |
|---------|-----------|
| `src/llm_client.py` | Cliente HTTP para llama-server API `/v1/chat/completions` con soporte de Function Calling. Modo dev simulado. |
| `src/anomaly_detector.py` | Detector de anomalías en 3 capas: Z-Score, relacional, temporal. |
| `src/report_templates.py` | Gestión CRUD de plantillas de reporte programado. Modelo SQLAlchemy `ReportTemplate`. |
| `src/sql_tools.py` | Catálogo de 12 herramientas SQL parametrizadas invocables por el LLM. |
| `src/agent_orchestrator.py` | Orquestador que conecta LLM + tools + SMS: maneja consultas ad-hoc y anomalías. |
| `tests/test_llm_client.py` | Tests del cliente LLM (modo real y simulado). |
| `tests/test_anomaly_detector.py` | Tests de las 3 capas de detección. |
| `tests/test_sql_tools.py` | Tests de las 12 herramientas SQL. |
| `tests/test_agent_orchestrator.py` | Tests de integración del orquestador. |

---

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `src/models.py` | Añadir modelos `ReportTemplate` y `AnomalyLog`. |
| `src/main.py` | Registrar nuevos servicios en lifespan: `AnomalyDetector`, `AgentOrchestrator`, `LlamaClient`. Añadir endpoints para plantillas e historial de anomalías. Registrar handler de consultas SMS en `IncomingSmsDispatcher`. Extender hook de pesaje para ejecutar detección. |
| `src/sms_incoming.py` | No requiere cambios estructurales; el nuevo handler se registra externamente. |
| `src/sms_service.py` | Extender `_check_and_send_reports()` para iterar sobre plantillas de `report_templates` (no solo horarios fijos de `config.yaml`). Extender `send_scheduled_report()` para aceptar destinatarios personalizados. |
| `src/config.py` | Añadir `AgentConfig` (dataclass) con parámetros: `llm_url`, `llm_model`, `window_size`, `window_hours`, `z_threshold`, `max_vegetal_to_muestra`, `max_mineral_to_muestra`, `max_rate_change`, `max_consecutive_anomalies`. |
| `database/migrations/` | Migraciones SQL para tablas nuevas. |

---

## Firmas nuevas

### `src/config.py`

```python
@dataclass(frozen=True)
class AgentConfig:
    llm_url: str = "http://localhost:8080"
    llm_model: str = "qwen2.5-1.5b-instruct-q4_k_m"
    llm_timeout: int = 30
    window_size: int = 120
    window_hours: int = 4
    z_threshold: float = 3.0
    max_vegetal_to_muestra: float = 0.5
    max_mineral_to_muestra: float = 0.3
    max_rate_change: float = 0.5
    max_consecutive_anomalies: int = 3
```

### `src/llm_client.py`

```python
class LlamaClient:
    def __init__(self, base_url: str, model: str, timeout: int, dev_mode: bool) -> None:
        ...

    def chat_completion(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict:
        """Envía un chat completion a llama-server.
        En dev mode, retorna respuesta simulada.
        En prod, hace POST a /v1/chat/completions.
        """

    def close(self) -> None:
        """Cierra la sesión HTTP."""
```

### `src/anomaly_detector.py`

```python
@dataclass(frozen=True)
class AnomalyResult:
    record_id: int
    layer: str          # "zscore" | "relacional" | "temporal"
    z_score: float | None
    metric_value: float
    threshold: float
    detail: str


class AnomalyDetector:
    def __init__(
        self,
        db_session_factory,
        config: AgentConfig,
    ) -> None:
        ...

    def run(self, weighing: Weighing) -> list[AnomalyResult]:
        """Ejecuta las 3 capas contra la ventana actual.
        Retorna lista de anomalías detectadas (vacía si no hay).
        """

    def _get_window(self, db: Session) -> list[Weighing]:
        """Obtiene los registros de la ventana móvil configurada."""

    def _detect_zscore(self, records: list[Weighing]) -> list[AnomalyResult]:
        """Capa 1: Z-Score con ventana móvil."""

    def _detect_relational(self, records: list[Weighing]) -> list[AnomalyResult]:
        """Capa 2: ratios entre materiales."""

    def _detect_temporal(self, records: list[Weighing]) -> list[AnomalyResult]:
        """Capa 3: tasa de cambio y rachas."""

    def detect_on_demand(
        self, window_size: int, z_threshold: float
    ) -> list[AnomalyResult]:
        """Ejecuta detección bajo demanda (endpoint GET /api/anomalies)."""
```

### `src/sql_tools.py`

```python
TOOL_DEFINITIONS: list[dict] = [
    # 12 tool definitions en formato OpenAI tool calling
    # Cada una con nombre, descripción, parámetros JSON Schema
]


class SqlTools:
    def __init__(self, db_session_factory) -> None:
        ...

    def get_basic_stats(self, fecha_inicio: str, fecha_fin: str, tipo_material: str | None = None) -> dict:
        ...

    def get_percentiles(self, fecha_inicio: str, fecha_fin: str, percentil: float) -> dict:
        ...

    def get_moving_average(self, window_size: int, tipo_material: str | None = None) -> dict:
        ...

    def get_trend(self, fecha_inicio: str, fecha_fin: str, tipo_material: str | None = None) -> dict:
        ...

    def get_breakdown_by_hacienda(self, fecha_inicio: str, fecha_fin: str) -> list[dict]:
        ...

    def get_breakdown_by_operator(self, fecha_inicio: str, fecha_fin: str) -> list[dict]:
        ...

    def get_material_composition(self, fecha_inicio: str, fecha_fin: str) -> dict:
        ...

    def get_shift_summary(self, fecha: str, turno: str) -> dict:
        ...

    def get_daily_summary(self, fecha: str) -> dict:
        ...

    def get_custom_period_summary(self, fecha_inicio: str, fecha_fin: str) -> dict:
        ...

    def detect_anomalies(self, window_size: int, z_threshold: float) -> list[dict]:
        ...

    def check_thresholds(self, window_size: int) -> dict:
        ...

    def execute_tool(self, tool_name: str, arguments: dict) -> dict:
        """Dispatcher: ejecuta la tool por nombre y retorna el resultado."""
```

### `src/report_templates.py`

```python
class ReportTemplateService:
    def __init__(self, db_session_factory) -> None:
        ...

    def create(self, data: dict) -> ReportTemplate:
        ...

    def update(self, template_id: int, data: dict) -> ReportTemplate:
        ...

    def delete(self, template_id: int) -> None:
        ...

    def get_all(self) -> list[ReportTemplate]:
        ...

    def get_active_by_schedule(self, time: str) -> list[ReportTemplate]:
        """Retorna plantillas activas cuyo schedule incluye la hora dada."""

    def generate_report(self, template: ReportTemplate, db: Session) -> str:
        """Genera el texto del reporte con SOLO las métricas seleccionadas.
        Ejecuta consultas SQL directas (sin LLM)."""
```

### `src/agent_orchestrator.py`

```python
class AgentOrchestrator:
    def __init__(
        self,
        llm_client: LlamaClient,
        sql_tools: SqlTools,
        sms_service: SMSService,
        db_session_factory,
    ) -> None:
        ...

    def handle_anomaly(
        self, anomalies: list[AnomalyResult], context: dict
    ) -> None:
        """Invoca LLM con contexto de anomalías, genera narrativa, envía SMS."""

    def handle_sms_query(self, sender_phone: str, text: str) -> None:
        """Procesa consulta SMS: LLM → tool_calls → ejecución → respuesta SMS."""

    def _build_llm_messages(self, user_text: str, context: dict | None = None) -> list[dict]:
        """Construye el mensaje del sistema + historial + consulta."""

    def _process_tool_calls(self, response: dict) -> list[dict]:
        """Ejecuta las tool_calls y retorna resultados."""

    def _final_response_to_sms(self, llm_final: str) -> str:
        """Limpia la respuesta del LLM para SMS."""
```

---

## Excepciones

| Excepción | Módulo | Cuándo se lanza |
|-----------|--------|-----------------|
| `LlamaConnectionError` | `src/llm_client.py` | Cuando falla la conexión HTTP con llama-server (timeout, conexión rechazada, error 5xx) |
| `AnomalyDetectionError` | `src/anomaly_detector.py` | Cuando ocurre un error inesperado durante la detección (BD no disponible, datos corruptos) |
| `ToolExecutionError` | `src/sql_tools.py` | Cuando una herramienta SQL falla (parámetros inválidos, error de consulta) |
| `TemplateNotFoundError` | `src/report_templates.py` | Cuando se intenta modificar/eliminar una plantilla que no existe |

---

## Endpoints API

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/api/reports/templates` | admin | Listar todas las plantillas |
| POST | `/api/reports/templates` | admin | Crear nueva plantilla |
| PUT | `/api/reports/templates/{id}` | admin | Modificar plantilla existente |
| DELETE | `/api/reports/templates/{id}` | admin | Eliminar plantilla |
| GET | `/api/anomalies` | admin | Ejecutar detección bajo demanda (query params: `window`, `threshold`) |
| GET | `/api/anomalies/history` | admin | Historial de anomalías (query param: `limit`, default 50) |
| POST | `/api/agent/query` | admin | Consulta directa al agente (body: `{ "query": "..." }`) para pruebas |

---

## Persistencia

### Tabla nueva: `report_templates`

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `id` | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK |
| `name` | VARCHAR(255) | NO | | Nombre descriptivo de la plantilla |
| `schedule` | TEXT (JSON) | NO | | Lista de horarios "HH:MM" en JSON array |
| `recipients` | TEXT (JSON) | NO | | Lista de teléfonos en JSON array |
| `metrics` | TEXT (JSON) | NO | | Lista de métricas seleccionadas en JSON array |
| `is_active` | BOOLEAN | NO | TRUE | Si está activa para generación programada |
| `created_at` | TIMESTAMP | NO | CURRENT_TIMESTAMP | |
| `updated_at` | TIMESTAMP | NO | CURRENT_TIMESTAMP ON UPDATE | |

Índices: `(is_active)`

### Tabla nueva: `anomaly_log`

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `id` | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK |
| `record_id` | BIGINT UNSIGNED | NO | | FK → weighings.id |
| `layer` | VARCHAR(20) | NO | | "zscore", "relacional" o "temporal" |
| `z_score` | DECIMAL(10,4) | YES | NULL | Solo para capa Z-Score |
| `metric_value` | DECIMAL(10,4) | NO | | Valor de la métrica que disparó la anomalía |
| `threshold` | DECIMAL(10,4) | NO | | Umbral que se excedió |
| `llm_report` | TEXT | YES | NULL | Reporte narrativo generado por el LLM (si se invocó) |
| `sent_sms` | BOOLEAN | NO | FALSE | Indica si se envió SMS de alerta |
| `anomaly_context` | TEXT (JSON) | YES | NULL | Contexto serializado de la detección (estadísticas de ventana) |
| `created_at` | TIMESTAMP | NO | CURRENT_TIMESTAMP | |

Índices: `(record_id)`, `(layer)`, `(created_at DESC)`

### Migraciones

1. `database/migrations/2026_06_16_000004_create_report_templates.sql`
2. `database/migrations/2026_06_16_000005_create_anomaly_log.sql`

```sql
-- 2026_06_16_000004_create_report_templates.sql
CREATE TABLE report_templates (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    schedule JSON NOT NULL,
    recipients JSON NOT NULL,
    metrics JSON NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2026_06_16_000005_create_anomaly_log.sql
CREATE TABLE anomaly_log (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    record_id BIGINT UNSIGNED NOT NULL,
    layer VARCHAR(20) NOT NULL,
    z_score DECIMAL(10,4) NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    threshold DECIMAL(10,4) NOT NULL,
    llm_report TEXT NULL,
    sent_sms BOOLEAN NOT NULL DEFAULT FALSE,
    anomaly_context JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_record (record_id),
    INDEX idx_layer (layer),
    INDEX idx_created (created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Tablas modificadas: ninguna

No se modifican tablas existentes. Las FK a `weighings.id` son referenciales (sin constraint FK en SQLite, con FK opcional en MariaDB).

---

## Configuración en config.yaml

Sección nueva que se añade al archivo:

```yaml
agent:
  llm_url: "http://localhost:8080"
  llm_model: "qwen2.5-1.5b-instruct-q4_k_m"
  llm_timeout: 30
  window_size: 120
  window_hours: 4
  z_threshold: 3.0
  max_vegetal_to_muestra: 0.5
  max_mineral_to_muestra: 0.3
  max_rate_change: 0.5
  max_consecutive_anomalies: 3
```

---

## Alternativas descartadas

### 1. Usar el LLM para generar reportes programados completos

**Descartada porque:**
- Los reportes programados siguen una estructura fija con métricas predecibles.
- El LLM añadiría latencia innecesaria (500ms-2s por inferencia) para datos que
  pueden calcularse con SQL directo en <50ms.
- El LLM podría alucinar cifras en reportes programados, mientras que SQL
  garantiza precisión absoluta en los números.
- El EdgeBox tiene recursos limitados (8GB RAM, 4 cores); reservar el LLM solo
  para tareas que realmente lo requieran (narrativa de anomalías, consultas
  ad-hoc) optimiza el uso de recursos.

### 2. Detección de anomalías vía LLM

**Descartada porque:**
- La latencia del LLM (1-3s por inferencia en Qwen 1.5B) haría impracticable la
  detección en tiempo real tras cada pesaje (<1s esperado).
- El no-determinismo del LLM podría generar falsos positivos inconsistentes.
- Las 3 capas algorítmicas (Z-Score, ratios, tasa de cambio) son más precisas,
  deterministas y trazables que una aproximación por lenguaje natural.
- El consumo de CPU/GPU del LLM para tareas puramente numéricas es
  desproporcionado: SQL + Python puro consumen <5% de un core, mientras que el
  LLM consumiría 3 cores completos.

### 3. Almacenar plantillas de reporte solo en config.yaml

**Descartada porque:**
- Las plantillas requieren operaciones CRUD frecuentes desde la interfaz admin.
- `config.yaml` no soporta concurrencia ni validación relacional.
- Guardar en MariaDB permite consultas eficientes por horario activo,
  escalabilidad y consistencia transaccional.
- La tabla `report_templates` es liviana (una fila por plantilla) y no requiere
  migraciones complejas.

---

## github_labels

`ai`, `llm`, `anomaly-detection`, `reporting`, `sms-query`, `function-calling`, `tinyllm`
