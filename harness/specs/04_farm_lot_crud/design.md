# Design — Gestión de Haciendas y Suertes

## Archivos nuevos

| Archivo | Propósito |
|---------|-----------|
| `src/haciendas.py` | Pydantic schemas + APIRouter (mismo patrón que `src/users.py`) |
| `tests/test_haciendas.py` | Tests unitarios con SQLite in-memory (mismo patrón que `test_users.py`) |

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/models.py` | Añadir modelos ORM `Hacienda` y `Suerte` |
| `src/main.py` | Registrar router `haciendas_router` |

## Persistencia

### Tabla nueva: `haciendas`

| Columna     | Tipo              | Nullable | Default              | Notas                  |
|-------------|-------------------|----------|----------------------|------------------------|
| id          | BIGINT UNSIGNED   | NO       | AUTO_INCREMENT       | PK                     |
| codigo      | VARCHAR(8)        | NO       |                      | UNIQUE                 |
| nombre      | VARCHAR(255)      | NO       |                      |                        |
| created_at  | TIMESTAMP         | NO       | CURRENT_TIMESTAMP    |                        |
| updated_at  | TIMESTAMP         | NO       | CURRENT_TIMESTAMP    | ON UPDATE              |
| deleted_at  | TIMESTAMP         | YES      | NULL                 | Soft delete marker     |

Índices: `UNIQUE (codigo)`

### Tabla nueva: `suertes`

| Columna       | Tipo              | Nullable | Default              | Notas                       |
|---------------|-------------------|----------|----------------------|-----------------------------|
| id            | BIGINT UNSIGNED   | NO       | AUTO_INCREMENT       | PK                          |
| hacienda_id   | BIGINT UNSIGNED   | NO       |                      | FK → haciendas.id           |
| codigo_suerte | VARCHAR(4)        | NO       |                      |                             |
| created_at    | TIMESTAMP         | NO       | CURRENT_TIMESTAMP    |                             |
| updated_at    | TIMESTAMP         | NO       | CURRENT_TIMESTAMP    | ON UPDATE                   |
| deleted_at    | TIMESTAMP         | YES      | NULL                 | Soft delete marker          |

FK: `FOREIGN KEY (hacienda_id) REFERENCES haciendas(id) ON DELETE RESTRICT`
Índices: `UNIQUE (hacienda_id, codigo_suerte)`

### Migraciones
1. `database/migrations/2026_06_13_000001_create_haciendas.py`
2. `database/migrations/2026_06_13_000002_create_suertes.py`

## Esquemas Pydantic (en `src/haciendas.py`)

```python
class HaciendaCreate(BaseModel):
    codigo: str = Field(min_length=1, max_length=8)
    nombre: str = Field(min_length=1, max_length=255)

class HaciendaUpdate(BaseModel):
    codigo: Optional[str] = Field(None, min_length=1, max_length=8)
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)

class HaciendaResponse(BaseModel):
    id: int
    codigo: str
    nombre: str
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True

class SuerteCreate(BaseModel):
    hacienda_id: int
    codigo_suerte: str = Field(min_length=1, max_length=4)

class SuerteUpdate(BaseModel):
    codigo_suerte: Optional[str] = Field(None, min_length=1, max_length=4)

class SuerteResponse(BaseModel):
    id: int
    hacienda_id: int
    codigo_suerte: str
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True
```

## Endpoints

### Haciendas (`/api/haciendas`)

| Método | Path | Función | Esquema request | Esquema response |
|--------|------|---------|-----------------|------------------|
| GET | `/api/haciendas` | `list_haciendas` | — | `List[HaciendaResponse]` |
| POST | `/api/haciendas` | `create_hacienda` | `HaciendaCreate` | `HaciendaResponse` (201) |
| GET | `/api/haciendas/{id}` | `get_hacienda` | — | `HaciendaResponse` |
| PUT | `/api/haciendas/{id}` | `update_hacienda` | `HaciendaUpdate` | `HaciendaResponse` |
| DELETE | `/api/haciendas/{id}` | `soft_delete_hacienda` | — | `HaciendaResponse` |

### Suertes (`/api/suertes`)

| Método | Path | Función | Esquema request | Esquema response |
|--------|------|---------|-----------------|------------------|
| GET | `/api/suertes` | `list_suertes` | — | `List[SuerteResponse]` |
| POST | `/api/suertes` | `create_suerte` | `SuerteCreate` | `SuerteResponse` (201) |
| GET | `/api/suertes/{id}` | `get_suerte` | — | `SuerteResponse` |
| PUT | `/api/suertes/{id}` | `update_suerte` | `SuerteUpdate` | `SuerteResponse` |
| DELETE | `/api/suertes/{id}` | `soft_delete_suerte` | — | `SuerteResponse` |

Todos los endpoints protegidos con `Depends(check_inactivity)` + `Depends(require_role("admin"))`.

## Alternativa descartada

**Tabla única con discriminador de tipo.** Se descartó porque las suertes
tienen un `hacienda_id` FK obligatorio y un `codigo_suerte` que solo tiene
sentido dentro de una hacienda. Dos tablas normalizadas reflejan mejor la
relación 1:N y permiten la constraint única compuesta `(hacienda_id, codigo_suerte)`.

## Seguridad

- Todos los endpoints requieren token JWT válido con rol `admin`.
- Endpoints devuelven 401 si no hay token, 403 si el rol no es admin.
- No hay endpoints públicos para haciendas/suertes.

## Comportamiento de soft delete

- `list_haciendas` filtra `WHERE deleted_at IS NULL` (excluye eliminadas).
- `list_suertes` filtra `WHERE deleted_at IS NULL`; si `hacienda_id` está presente, filtra también por ese campo.
- `get_hacienda` / `get_suerte` devuelven 404 si `deleted_at IS NOT NULL`.
- `DELETE` establece `deleted_at = datetime.utcnow()`.
- La FK `ON DELETE RESTRICT` está declarada pero nunca se ejecuta hard delete desde la API; la constraint protege contra borrados accidentales a nivel BD.

## GitHub labels

`haciendas`, `suertes`, `crud`, `soft-delete`, `admin-only`
