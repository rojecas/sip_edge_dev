# Design — Paginación en endpoints y tablas de Usuarios y Backups

> Feature 21. Sin cambios de esquema BD, sin nuevos campos, sin alterar
> lógica de negocio. Solo extracción de modelo compartido + paginación
> de dos endpoints + UI de paginación en dos componentes Svelte.

---

## Resumen

Se modifica el endpoint GET /api/users (hoy retorna `List[UserResponse]` plano)
y GET /api/backup/status (hoy retorna array plano de dicts, hard-limited a 10)
para que devuelvan respuestas paginadas con el mismo formato que ya usan
GET /api/haciendas y GET /api/weighings.

Se extrae el modelo `PaginatedResponse` duplicado a un módulo compartido
`src/schemas.py`, eliminando las definiciones repetidas en `src/haciendas.py`
y `src/weighings.py`.

Se agrega estado y UI de paginación a `AdminUsers.svelte` y `AdminBackup.svelte`
siguiendo el patrón existente en `AdminHaciendas.svelte`.

---

## Archivos a crear

| Archivo | Propósito |
|---------|-----------|
| `src/schemas.py` | Modelo compartido `PaginatedResponse[T]` (Generic Pydantic) |

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `src/haciendas.py` | Eliminar clase `PaginatedResponse` local. Importar `from src.schemas import PaginatedResponse`. |
| `src/weighings.py` | Eliminar clase `PaginatedResponse` local. Importar `from src.schemas import PaginatedResponse`. |
| `src/users.py` | Agregar parámetros query `page` y `page_size` con defaults. Cambiar `response_model` a `PaginatedResponse[UserResponse]`. Agregar lógica de paginación (count, offset, limit, total_pages). Importar `PaginatedResponse`. |
| `src/main.py` | Definir `BackupLogResponse` Pydantic model (reemplaza dict crudo). Agregar parámetros query `page` y `page_size`. Cambiar respuesta a `PaginatedResponse[BackupLogResponse]`. Importar `PaginatedResponse`. |
| `frontend/src/components/AdminUsers.svelte` | Agregar variables de estado `currentPage`, `totalPages`, `totalItems`, `pageSize`. Agregar funciones `goToPage(page)` y `changePageSize(e)`. Modificar `loadUsers()` para usar `buildQuery` con parámetros de paginación. Agregar HTML de controles de paginación (botones, selector, texto informativo). |
| `frontend/src/components/AdminBackup.svelte` | Mismos cambios que AdminUsers.svelte pero para el endpoint de backup. |
| `tests/test_users.py` | Agregar tests de paginación para GET /api/users. |
| `tests/test_backup.py` | Agregar tests de paginación para GET /api/backup/status. |
| `frontend/src/lib/constants.js` | Opcional: agregar `CONFIG.DEFAULT_USERS_PAGE_SIZE` y `CONFIG.DEFAULT_BACKUP_PAGE_SIZE` si se desea centralizar defaults. |

---

## Firmas nuevas / modificadas

### `src/schemas.py` (NUEVO)

```python
T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response. Reusable across all list endpoints."""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
```

### `src/users.py` — endpoint modificado

```python
@router.get("", response_model=PaginatedResponse[UserResponse])
def get_users(
    _admin: dict = Depends(check_inactivity),
    __admin: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
```

### `src/main.py` — nuevo schema + endpoint modificado

```python
class BackupLogResponse(BaseModel):
    """Response schema for a single backup log entry."""
    id: int
    filename: str
    file_size: int
    local_checksum: str
    usb_copied: bool
    usb_checksum: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str  # ISO format

    class Config:
        from_attributes = True

@backup_router.get("/status", response_model=PaginatedResponse[BackupLogResponse])
async def get_backup_status(
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    query = db.query(BackupLog).order_by(BackupLog.created_at.desc())
    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size
    records = query.offset(offset).limit(page_size).all()
    items = [_backup_log_to_response(log) for log in records]
    return PaginatedResponse(
        items=items, total=total, page=page,
        page_size=page_size, total_pages=total_pages,
    )
```

### AdminUsers.svelte — nuevas variables/funciones

```javascript
let currentPage = $state(1);
let totalPages = $state(1);
let totalItems = $state(0);
let pageSize = $state(20);

async function loadUsers() {
    const qs = buildQuery({ page: currentPage, page_size: pageSize });
    const result = await api.get(`${ENDPOINTS.USERS}${qs}`);
    users = result.items || [];
    totalPages = result.total_pages || 1;
    totalItems = result.total || 0;
    // …
}

function goToPage(page) {
    currentPage = page;
    loadUsers();
}

function changePageSize(e) {
    pageSize = parseInt(e.target.value);
    currentPage = 1;
    loadUsers();
}
```

### AdminBackup.svelte — mismas variables/funciones, con pageSize default 10

---

## Contrato API

### GET /api/users

```
Request:  GET /api/users?page=1&page_size=20
Auth:     Bearer JWT (admin)
Response: {
  items: UserResponse[],
  total: number,
  page: 1,
  page_size: 20,
  total_pages: number
}
```

### GET /api/backup/status

```
Request:  GET /api/backup/status?page=1&page_size=10
Auth:     Bearer JWT (admin)
Response: {
  items: BackupLogResponse[],
  total: number,
  page: 1,
  page_size: 10,
  total_pages: number
}
```

Los endpoints conservan sus protecciones de autenticación y RBAC existentes
(admin-only para ambos).

---

## Persistencia

No hay cambios en la base de datos. La feature es exclusivamente de API
(paginación de queries existentes) y UI (controles de paginación en frontend).

No se requiere migración, ni nuevas tablas, ni nuevas columnas.

---

## Alternativa descartada

**Mantener PaginatedResponse duplicado en cada archivo.**
*Razón:* La duplicación existe actualmente en `src/haciendas.py` y
`src/weighings.py` (definiciones idénticas). Agregar una tercera copia
en `src/users.py` y una cuarta en `src/main.py` multiplica el riesgo de
inconsistencias y viola DRY. Extraer a `src/schemas.py` es un refactor
trivial, mecánico y sin cambio de comportamiento (la clase es idéntica
en los dos archivos fuente). Se actualizan los dos archivos existentes
más los dos nuevos para que importen del mismo sitio.

---

## github_labels

`pagination`, `backend`, `frontend`, `refactor`
