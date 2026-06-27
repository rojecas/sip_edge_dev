# Design — Campo tipo de cosecha en registro de pesaje

> Feature 18 — harvest_type  
> Dependencies: 6 (weighing_capture - done), 8 (ai_agent - done), 13 (frontend_login_kiosk - done)

---

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `src/models.py` | Añadir columna `tipo_cosecha` a la clase `Weighing` (SQLAlchemy Enum, NOT NULL, default `'Mecanico - Verde'`). |
| `src/weighings.py` | Añadir campo `tipo_cosecha` en `WeighingCreate` (str opcional, default `'Mecanico - Verde'`, con validator). Añadir campo en `WeighingResponse`. En `create_weighing()`, usar el valor del body o default. En `_build_frame_data()`, incluir `tipo_cosecha` en el dict RS232. |
| `src/main.py` | Endpoint `GET /api/anomalies`: añadir query param opcional `tipo_cosecha: Optional[str] = Query(None)` y pasarlo a `detect_on_demand()`. |
| `src/anomaly_detector.py` | Método `detect_on_demand()`: añadir parámetro opcional `tipo_cosecha: str | None`. Método `_get_window()`: añadir filtro por `tipo_cosecha` si se proporciona. |
| `src/sql_tools.py` | Las herramientas SQL que consultan `weighings` (`get_basic_stats`, `get_breakdown_by_hacienda`, `get_breakdown_by_operator`, `get_material_composition`, `get_daily_summary`, `get_custom_period_summary`, `check_thresholds`, etc.) DEBEN añadir parámetro opcional `tipo_cosecha` para filtrar por tipo de cosecha. Método `_weight_column()` se mantiene; el filtro se aplica como condición adicional en el WHERE. |
| `frontend/src/lib/constants.js` | Añadir constante `HARVEST_TYPES` con el array de 6 valores string. |
| `frontend/src/components/KioskForm.svelte` | Añadir variable reactiva `tipoCosecha` con default `'Mecanico - Verde'`. Añadir `<select>` en el formulario con las 6 opciones. Incluir `tipo_cosecha` en el body de `POST /api/weighings`. |
| `frontend/src/components/HistoryTable.svelte` | Añadir columna "Tipo Cosecha" en `<thead>` y celda correspondiente en `<tbody>` con el valor de `w.tipo_cosecha`. |
| `database/migrations/` | Nueva migración SQL para añadir la columna a la tabla `weighings`. |
| `tests/test_weighings.py` | Añadir tests para cobertura de tipo_cosecha: valor válido por defecto, valor explícito, valor inválido. |

---

## Firmas nuevas / modificadas

### Constante en `frontend/src/lib/constants.js`

```javascript
export const HARVEST_TYPES = [
  "Manual - Incendio",
  "Manual - Quemado",
  "Manual - Verde",
  "Mecanico - Incendio",
  "Mecanico - Verde",
  "No convencional - Verde",
];
```

### Schema `WeighingCreate` modificado en `src/weighings.py`

```python
from pydantic import field_validator

TIPO_COSECHA_VALUES = [
    "Manual - Incendio", "Manual - Quemado", "Manual - Verde",
    "Mecanico - Incendio", "Mecanico - Verde", "No convencional - Verde",
]

class WeighingCreate(BaseModel):
    tractomula: str = Field(default="", max_length=32)
    vagon: str = Field(default="", max_length=32)
    numero_guia: str = Field(default="", max_length=32)
    hacienda_id: int = Field(gt=0)
    suerte_id: int = Field(gt=0)
    peso_muestra: Decimal = Field(ge=0)
    peso_mineral: Decimal = Field(ge=0)
    peso_vegetal_extrano: Decimal = Field(ge=0)
    manual_entry: bool = Field(default=False)
    tipo_cosecha: str = Field(default="Mecanico - Verde")

    @field_validator("tipo_cosecha")
    @classmethod
    def validate_tipo_cosecha(cls, v):
        if v not in TIPO_COSECHA_VALUES:
            raise ValueError(
                f"tipo_cosecha debe ser uno de: {', '.join(TIPO_COSECHA_VALUES)}"
            )
        return v
```

### Schema `WeighingResponse` modificado en `src/weighings.py`

```python
class WeighingResponse(BaseModel):
    id: int
    ...
    tipo_cosecha: str

    class Config:
        from_attributes = True
```

### `create_weighing()` en `src/weighings.py`

```python
record = Weighing(
    ...
    tipo_cosecha=body.tipo_cosecha,
)
```

### `_build_frame_data()` en `src/weighings.py`

```python
def _build_frame_data(record, hacienda, suerte):
    return {
        ...
        "tipo_cosecha": record.tipo_cosecha,
    }
```

### `GET /api/anomalies` en `src/main.py` — modificado

```python
@anomaly_router.get("")
async def detect_anomalies_on_demand(
    window: int = 120,
    threshold: float = 3.0,
    tipo_cosecha: Optional[str] = Query(None),
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_role("admin")),
):
    detector = app.state.anomaly_detector
    try:
        results = detector.detect_on_demand(window, threshold, tipo_cosecha=tipo_cosecha)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return [
        {
            "record_id": r.record_id,
            "layer": r.layer,
            "z_score": r.z_score,
            "metric_value": r.metric_value,
            "threshold": r.threshold,
            "detail": r.detail,
        }
        for r in results
    ]
```

### `AnomalyDetector.detect_on_demand()` en `src/anomaly_detector.py` — modificado

```python
def detect_on_demand(
    self, window_size: int, z_threshold: float, tipo_cosecha: str | None = None
) -> list[AnomalyResult]:
    records = self._get_window(window_size, tipo_cosecha=tipo_cosecha)
    # ... resto igual
```

### `AnomalyDetector._get_window()` en `src/anomaly_detector.py` — modificado

```python
def _get_window(self, window_size: int, tipo_cosecha: str | None = None) -> list[Weighing]:
    db = self._db_session_factory()
    try:
        query = db.query(Weighing).order_by(Weighing.id.desc())
        if tipo_cosecha:
            query = query.filter(Weighing.tipo_cosecha == tipo_cosecha)
        return query.limit(window_size).all()
    finally:
        db.close()
```

### Modelo ORM `Weighing` en `src/models.py` — columna nueva

```python
from sqlalchemy import Enum as SAEnum

class Weighing(Base):
    __tablename__ = "weighings"
    ...
    tipo_cosecha = Column(
        SAEnum(
            "Manual - Incendio", "Manual - Quemado", "Manual - Verde",
            "Mecanico - Incendio", "Mecanico - Verde", "No convencional - Verde",
            name="tipo_cosecha_enum",
        ),
        nullable=False,
        default="Mecanico - Verde",
        server_default=text("'Mecanico - Verde'"),
    )
```

### SqlTools — métodos modificados (parámetro opcional tipo_cosecha)

Las herramientas que filtran por `Weighing.fecha` deben añadir filtro opcional por `tipo_cosecha`:

```python
def get_basic_stats(self, fecha_inicio: str, fecha_fin: str, tipo_material: str | None = None, tipo_cosecha: str | None = None) -> dict:
    db = self._get_db()
    try:
        fi = date.fromisoformat(fecha_inicio)
        ff = date.fromisoformat(fecha_fin)
        weight_expr = self._weight_column(tipo_material)
        query = db.query(
            func.count(Weighing.id).label("count"),
            ...
        ).filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
        if tipo_cosecha:
            query = query.filter(Weighing.tipo_cosecha == tipo_cosecha)
        row = query.first()
        ...
```

Las tools a modificar: `get_basic_stats`, `get_percentiles`, `get_breakdown_by_hacienda`, `get_breakdown_by_operator`, `get_material_composition`, `get_shift_summary`, `get_daily_summary`, `get_custom_period_summary`, `check_thresholds`. También se deben actualizar las definiciones en `TOOL_DEFINITIONS` para incluir el parámetro `tipo_cosecha` en el schema JSON.

---

## Persistencia

### Tabla modificada: `weighings`

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| `tipo_cosecha` | ENUM('Manual - Incendio','Manual - Quemado','Manual - Verde','Mecanico - Incendio','Mecanico - Verde','No convencional - Verde') | NO | `'Mecanico - Verde'` | Nueva columna |

### Migración

1. `database/migrations/2026_06_25_000001_add_tipo_cosecha_to_weighings.sql`

```sql
ALTER TABLE weighings
ADD COLUMN tipo_cosecha ENUM(
    'Manual - Incendio',
    'Manual - Quemado',
    'Manual - Verde',
    'Mecanico - Incendio',
    'Mecanico - Verde',
    'No convencional - Verde'
) NOT NULL DEFAULT 'Mecanico - Verde';
```

La migración debe ejecutarse después de la creación de `weighings` (migración 2026_06_13_000003_create_weighings.py).

### Nota sobre SQLite (tests)

SQLite no soporta ENUM nativo. SQLAlchemy almacenará la columna como VARCHAR con una constraint CHECK. El comportamiento debe ser transparente para los tests.

---

## Contrato API

### POST /api/weighings — Crear pesaje (modificado)
Request body:
```json
{
  "tractomula": "ABC123",
  "vagon": "VAG-01",
  "numero_guia": "G-001",
  "hacienda_id": 1,
  "suerte_id": 1,
  "peso_muestra": 1.250,
  "peso_mineral": 0.800,
  "peso_vegetal_extrano": 0.050,
  "manual_entry": false,
  "tipo_cosecha": "Mecanico - Verde"
}
```
Response (201):
```json
{
  "id": 1,
  "fecha": "2026-06-25",
  "hora": "09:53:00",
  "tractomula": "ABC123",
  "vagon": "VAG-01",
  "numero_guia": "G-001",
  "hacienda_id": 1,
  "suerte_id": 1,
  "peso_muestra": 1.250,
  "peso_mineral": 0.800,
  "peso_vegetal_extrano": 0.050,
  "usuario_id": 2,
  "created_at": "2026-06-25T09:53:00",
  "enviado_pc": false,
  "manual_entry": false,
  "tipo_cosecha": "Mecanico - Verde"
}
```

### GET /api/anomalies — Detección bajo demanda (modificado)
Query params: `window` (int, default 120), `threshold` (float, default 3.0), `tipo_cosecha` (string, opcional)

Respuesta: same format as existing, pero filtrada por tipo_cosecha si se proporciona.

### GET /api/weighings — Listar pesajes (modificado implícitamente)
La respuesta paginada existente ahora incluye `tipo_cosecha` en cada item del array `items[]`.

---

## Impacto en APIs existentes

### Feature 6 — weighing_capture
| Item | Archivo | Cambio requerido |
|------|---------|-----------------|
| Schema WeighingCreate | src/weighings.py | Agregar campo `tipo_cosecha: str = Field(default="Mecanico - Verde")` + validator |
| Schema WeighingResponse | src/weighings.py | Agregar campo `tipo_cosecha: str` |
| Endpoint POST /api/weighings | src/weighings.py | Incluir `tipo_cosecha=body.tipo_cosecha` en creación del registro |
| Endpoint GET /api/weighings | src/weighings.py | Incluir `tipo_cosecha` en la construcción de `WeighingResponse` dentro del listado |
| Endpoint GET /api/weighings/{id} | src/weighings.py | Ya cubierto por `WeighingResponse.from_attributes` |
| RS232 frame data | src/weighings.py | Incluir `tipo_cosecha` en dict de `_build_frame_data()` |
| Modelo Weighing | src/models.py | Agregar columna `tipo_cosecha` |

### Feature 8 — ai_agent
| Item | Archivo | Cambio requerido |
|------|---------|-----------------|
| Endpoint GET /api/anomalies | src/main.py | Agregar query param `tipo_cosecha` y pasarlo a detect_on_demand |
| AnomalyDetector.detect_on_demand | src/anomaly_detector.py | Agregar parámetro `tipo_cosecha` y filtrar en `_get_window` |
| SqlTools (hasta 9 métodos) | src/sql_tools.py | Agregar parámetro `tipo_cosecha` en tools que filtran weighings |
| TOOL_DEFINITIONS schemas | src/sql_tools.py | Agregar `tipo_cosecha` como property opcional en definitions de funciones relevantes |

### Feature 13 — frontend_login_kiosk
| Item | Archivo | Cambio requerido |
|------|---------|-----------------|
| Constantes | frontend/src/lib/constants.js | Agregar `HARVEST_TYPES` array |
| Componente KioskForm | frontend/src/components/KioskForm.svelte | Agregar select "Tipo de Cosecha" y enviar en POST body |
| Componente HistoryTable | frontend/src/components/HistoryTable.svelte | Agregar columna "Tipo Cosecha" en tabla |

---

## Excepciones

La validación de `tipo_cosecha` se realiza mediante `@field_validator` en `WeighingCreate` de Pydantic, que lanza `ValueError` automáticamente convertido a HTTP 422 por FastAPI. No se requieren nuevas excepciones nombradas.

---

## Alternativa descartada

**Type alias / Literal en Pydantic en lugar de validator con lista.** La alternativa era usar `typing.Literal` con los 6 valores como union, lo que daría validación automática en Pydantic v2 sin validator explícito:

```python
from typing import Literal
TipoCosecha = Literal[
    "Manual - Incendio", "Manual - Quemado", "Manual - Verde",
    "Mecanico - Incendio", "Mecanico - Verde", "No convencional - Verde",
]
```

**Descartada porque:**
1. Los valores `Literal` con strings largas y caracteres especiales (guiones, espacios) son verbosos de mantener.
2. El mensaje de error por defecto de Pydantic para Literal no lista las opciones válidas de forma amigable para el operador.
3. El validator explícito permite reutilizar `TIPO_COSECHA_VALUES` como lista tanto para la validación como para renderizar el frontend (selector de opciones).
4. La lista `TIPO_COSECHA_VALUES` puede exportarse y reutilizarse en el frontend si se decide centralizar la definición.

---

## github_labels

`harvest_type`, `weighing`, `kiosk`, `migration`, `filter`, `anomalies`
