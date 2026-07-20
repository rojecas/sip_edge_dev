# Design — Feature 39: Trazabilidad: Registro de usuario creador en Haciendas y Suertes

## Archivos a modificar

| Archivo | Tipo | Cambio |
|---------|------|--------|
| `database/migrations/2026_07_19_000001_add_created_by_to_haciendas.py` | Crear | ALTER TABLE haciendas ADD created_by + FK |
| `database/migrations/2026_07_19_000002_add_created_by_to_suertes.py` | Crear | ALTER TABLE suertes ADD created_by + FK |
| `src/models.py` | Modificar | Agregar `created_by` y relación `creator` en Hacienda y Suerte |
| `src/haciendas.py` | Modificar | Schemas HaciendaResponse/SuerteResponse: agregar `created_by` y `created_by_username`. Funciones `_to_response` y `create_*`: aceptar/inyectar `user_id`. Routers: pasar `current_user["user_id"]` |
| `frontend/src/components/AdminHaciendas.svelte` | Modificar | Agregar columna "Creado por" en `<thead>` y `<tbody>` |
| `frontend/src/components/AdminSuertes.svelte` | Modificar | Agregar columna "Creado por" en `<thead>` y `<tbody>` |
| `tests/test_haciendas.py` | Modificar | Agregar tests para created_by en creación y respuesta |

## Firmas nuevas / modificadas

### `src/models.py`

```python
class Hacienda(Base):
    # ... columnas existentes ...
    created_by = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.id"),
        nullable=True,
        default=None,
    )
    creator = relationship("User", foreign_keys=[created_by])

class Suerte(Base):
    # ... columnas existentes ...
    created_by = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.id"),
        nullable=True,
        default=None,
    )
    creator = relationship("User", foreign_keys=[created_by])
```

### `src/haciendas.py` — Schemas

```python
class HaciendaResponse(BaseModel):
    # ... campos existentes ...
    created_by: Optional[int] = None
    created_by_username: Optional[str] = None

class SuerteResponse(BaseModel):
    # ... campos existentes ...
    created_by: Optional[int] = None
    created_by_username: Optional[str] = None
```

### `src/haciendas.py` — Funciones modificadas

```python
def _hacienda_to_response(h: Hacienda) -> HaciendaResponse:
    return HaciendaResponse(
        # ... campos existentes ...
        created_by=h.created_by,
        created_by_username=h.creator.username if h.creator else None,
    )

def _suerte_to_response(s: Suerte) -> SuerteResponse:
    return SuerteResponse(
        # ... campos existentes ...
        created_by=s.created_by,
        created_by_username=s.creator.username if s.creator else None,
    )

def create_hacienda(db: Session, data: HaciendaCreate, user_id: int) -> HaciendaResponse:
    # ... validación existente ...
    h = Hacienda(codigo=data.codigo, nombre=data.nombre, created_by=user_id)
    # ...

def create_suerte(db: Session, data: SuerteCreate, user_id: int) -> SuerteResponse:
    # ... validación existente ...
    s = Suerte(hacienda_id=data.hacienda_id, codigo_suerte=data.codigo_suerte, created_by=user_id)
    # ...
```

### Routers modificados

```python
@haciendas_router.post("", response_model=HaciendaResponse, status_code=201)
def create_new_hacienda(
    body: HaciendaCreate,
    current_user: dict = Depends(check_inactivity),
    __: dict = Depends(require_any_role("admin", "operator")),
    db: Session = Depends(get_db),
):
    return create_hacienda(db, body, current_user["user_id"])

@suertes_router.post("", response_model=SuerteResponse, status_code=201)
def create_new_suerte(
    body: SuerteCreate,
    current_user: dict = Depends(check_inactivity),
    __: dict = Depends(require_any_role("admin", "operator")),
    db: Session = Depends(get_db),
):
    return create_suerte(db, body, current_user["user_id"])
```

## Excepciones

No se introducen nuevas excepciones. Se reutilizan:
- `HTTPException(401)` — No autenticado (existente en `check_inactivity`/`get_current_user`)
- `HTTPException(403)` — Sin permisos (existente en `require_any_role`)
- `HTTPException(409)` — Código duplicado (existente en `create_hacienda`/`create_suerte`)

## Persistencia

### Migración 1: `2026_07_19_000001_add_created_by_to_haciendas.py`

```sql
ALTER TABLE haciendas
ADD COLUMN created_by BIGINT UNSIGNED NULL AFTER updated_at,
ADD CONSTRAINT fk_haciendas_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
```

### Migración 2: `2026_07_19_000002_add_created_by_to_suertes.py`

```sql
ALTER TABLE suertes
ADD COLUMN created_by BIGINT UNSIGNED NULL AFTER updated_at,
ADD CONSTRAINT fk_suertes_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
```

La FK usa `ON DELETE SET NULL` para no impedir la eliminación de usuarios.
Los registros históricos mantienen `created_by = NULL` (R9).

### Modelos SQLAlchemy

Ambos modelos agregan:
- `created_by: Column(BigInteger..., ForeignKey("users.id"), nullable=True)`
- `creator = relationship("User", foreign_keys=[created_by])`

Se importa `ForeignKey` y `relationship` si no están ya disponibles.

## Impacto en APIs existentes

Ninguna API existente cambia su contrato de entrada. Solo se agregan dos campos
opcionales (`created_by`, `created_by_username`) a las respuestas `HaciendaResponse`
y `SuerteResponse`. Los clientes existentes que ignoren campos desconocidos no
se ven afectados.

## Análisis de impacto en features existentes

### Feature 4 — farm_lot_crud
| Ítem | Archivo | Cambio |
|------|---------|--------|
| Modelo Hacienda | `src/models.py` | Nueva columna `created_by` + relación `creator` |
| Modelo Suerte | `src/models.py` | Nueva columna `created_by` + relación `creator` |
| Schema HaciendaResponse | `src/haciendas.py` | Nuevos campos `created_by`, `created_by_username` |
| Schema SuerteResponse | `src/haciendas.py` | Nuevos campos `created_by`, `created_by_username` |
| `_hacienda_to_response` | `src/haciendas.py` | Incluye `created_by`, `created_by_username` |
| `_suerte_to_response` | `src/haciendas.py` | Incluye `created_by`, `created_by_username` |
| `create_hacienda` | `src/haciendas.py` | Nuevo parámetro `user_id: int` |
| `create_suerte` | `src/haciendas.py` | Nuevo parámetro `user_id: int` |
| Tests | `tests/test_haciendas.py` | Verificar `created_by` en responses POST/GET |

**Compatibilidad hacia atrás:** Las funciones `create_hacienda` y `create_suerte`
cambian su firma (nuevo parámetro `user_id`). Esto NO rompe compatibilidad porque
son funciones internas llamadas solo desde los routers del mismo módulo.

### Feature 38 — operator_hacienda_suerte_crud
| Ítem | Archivo | Cambio |
|------|---------|--------|
| AdminHaciendas.svelte | `frontend/src/components/AdminHaciendas.svelte` | Nueva columna "Creado por" en tabla |
| AdminSuertes.svelte | `frontend/src/components/AdminSuertes.svelte` | Nueva columna "Creado por" en tabla |

**Compatibilidad hacia atrás:** Los componentes Svelte muestran la columna
adicional; no hay cambio de interfaz ni props. El componente ya es usado tanto
en admin como en kiosko (F38), por lo que el cambio aplica automáticamente en
ambas vistas.

### Ninguna otra feature se ve afectada
- `GET /api/haciendas` y `GET /api/suertes` solo agregan campos nuevos.
- `PUT` y `DELETE` no se modifican.
- `POST` recibe el `user_id` del token JWT, no del body.

## Contrato API

### GET /api/haciendas
Respuesta paginada (sin cambios en estructura):
```json
{
  "items": [
    {
      "id": 1,
      "codigo": "H001",
      "nombre": "Hacienda Test",
      "created_at": "2026-01-01T00:00:00",
      "updated_at": "2026-01-01T00:00:00",
      "created_by": 1,
      "created_by_username": "admin"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 100,
  "total_pages": 1
}
```

### POST /api/haciendas
Request (sin cambios):
```json
{ "codigo": "H001", "nombre": "Hacienda Test" }
```
Response: `HaciendaResponse` con `created_by` y `created_by_username` poblados.

### GET /api/suertes
Respuesta (array plano, sin cambios de paginación):
```json
[
  {
    "id": 1,
    "hacienda_id": 1,
    "codigo_suerte": "A1",
    "created_at": "2026-01-01T00:00:00",
    "updated_at": "2026-01-01T00:00:00",
    "created_by": 1,
    "created_by_username": "admin"
  }
]
```

### POST /api/suertes
Request (sin cambios):
```json
{ "hacienda_id": 1, "codigo_suerte": "A1" }
```
Response: `SuerteResponse` con `created_by` y `created_by_username` poblados.

## Alternativa descartada

**Alternativa:** Pasar `created_by` como campo opcional en el body del POST
(HaciendaCreate / SuerteCreate), permitiendo que el cliente decida el valor.

**Razón de rechazo:** Esto violaría el principio de trazabilidad: el creador
debe ser el usuario autenticado, no un campo manipulable por el cliente.
Cualquier cliente (incluyendo scripts maliciosos) podría falsificar el creador.
La asignación desde el token JWT garantiza que `created_by` refleje siempre
al usuario que realizó la petición, como ya se hace con `usuario_id` en
`POST /api/weighings`.

## `github_labels`

`enhancement`, `trazabilidad`, `haciendas`, `suertes`
