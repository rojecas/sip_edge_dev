# Design — Gestión de Usuarios (CRUD)

## Archivos a crear

| Archivo                        | Propósito                                        |
|-------------------------------|--------------------------------------------------|
| `src/users.py`                | Módulo con schemas Pydantic y endpoints CRUD     |
| `tests/test_users.py`         | Tests unitarios y de integración                 |

## Archivos a modificar

| Archivo                        | Cambio                                           |
|-------------------------------|--------------------------------------------------|
| `src/main.py`                 | Registrar router de users                        |

## Schemas Pydantic (en `src/users.py`)

### UserCreate (request body para POST)
```
username: str (min_length=1)
password: str (min_length=1)
full_name: str (min_length=1)
document: str (default "")
role: Literal["admin", "operator", "corresponsal"]
```

### UserUpdate (request body para PUT — todos opcionales)
```
full_name: str | None = None
document: str | None = None
role: Literal["admin", "operator", "corresponsal"] | None = None
is_active: bool | None = None
new_password: str | None = None
```
Nota: `new_password` cuando se envía, se hashea y actualiza `password_hash`.

### UserResponse (response — sin password_hash)
```
id: int
username: str
full_name: str
document: str
role: str
is_active: bool
created_at: datetime
updated_at: datetime
```
Se construye desde el ORM User excluyendo `password_hash`.

## Endpoints (todos bajo prefix `/api/users`)

Cada endpoint usa:
1. `Depends(check_inactivity)` — verifica expiración por inactividad.
2. `Depends(require_role("admin"))` — solo admin.
3. `db: Session = Depends(get_db)` — sesión DB.

| Método | Ruta              | Schema Request  | Status éxito | Descripción                |
|--------|-------------------|-----------------|--------------|----------------------------|
| GET    | `/api/users`       | —               | 200          | Lista todos los usuarios   |
| GET    | `/api/users/{id}`  | —               | 200          | Usuario por ID             |
| POST   | `/api/users`       | `UserCreate`    | 201          | Crear usuario              |
| PUT    | `/api/users/{id}`  | `UserUpdate`    | 200          | Actualizar usuario         |
| DELETE | `/api/users/{id}`  | —               | 200          | Desactivación lógica       |

## Funciones internal API en `src/users.py`

Todas son funciones regulares que reciben `db: Session` — **no dependencias de FastAPI**.
Así son testeables sin cliente HTTP.

```
list_users(db) -> list[UserResponse]
get_user(db, user_id) -> UserResponse
create_user(db, data: UserCreate) -> UserResponse  (hashea password)
update_user(db, user_id, data: UserUpdate) -> UserResponse
deactivate_user(db, user_id) -> UserResponse
```

## Excepciones

- `HTTPException(404, detail="User not found")` — en GET/PUT/DELETE por ID inexistente.
- `HTTPException(409, detail="Username already exists")` — en POST con username duplicado.
- Las validaciones de schema son manejadas por Pydantic (422 automático).

## Alternativa descartada

Router separado en `src/routers/users.py` — descartado por simplicidad.
El proyecto actual no usa `APIRouter` ni tiene carpeta `routers/`.
Se prefiere una función `register_user_routes(app)` en `src/users.py` que
llame a `app.add_api_route(...)` manteniendo coherencia con el estilo existente
(ver `src/main.py` donde las rutas se registran como decoradores en el objeto `app`).
Sin embargo, para mejor organización, usaremos `APIRouter(prefix="/api/users")`
y lo registraremos en `main.py` con `app.include_router(users_router)`.

## Persistencia

No se requieren cambios en el esquema de base de datos. La tabla `users` ya
existe con todos los campos necesarios (`is_active`, `document`, `full_name`,
`role`, `password_hash`, `created_at`, `updated_at`). No hay migraciones nuevas.

## Trazabilidad de requirements

| R   | Archivo(s) que lo cubren         |
|-----|----------------------------------|
| R1  | `src/users.py` — `list_users`    |
| R2  | `src/users.py` — `get_user`      |
| R3  | `src/users.py` — `create_user`   |
| R4  | `src/users.py` — `update_user`   |
| R5  | `src/users.py` — `deactivate_user` |
| R6  | `src/main.py` — `require_role("admin")` en cada ruta |
| R7  | `src/auth.py` — `get_current_user` (incluido en `check_inactivity`) |
| R8  | Pydantic validation en `UserCreate` |
