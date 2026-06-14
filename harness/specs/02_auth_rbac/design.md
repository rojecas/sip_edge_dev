# Design — auth_rbac

> Decisiones tecnicas para autenticacion JWT, RBAC, bloqueo por inactividad
> y persistencia en MariaDB.

## Archivos creados / modificados

| Archivo | Accion | Proposito |
|---------|--------|-----------|
| `src/database.py` | **CREAR** | Conexion SQLAlchemy (engine + session factory) |
| `src/models.py` | **CREAR** | Modelo ORM `User` (SQLAlchemy DeclarativeBase) |
| `src/auth.py` | **CREAR** | Logica JWT + dependencias FastAPI (`get_current_user`, `require_role`, `check_inactivity`) |
| `src/seed.py` | **CREAR** | Funcion `seed_admin_user()` para crear admin inicial |
| `src/config.py` | MODIFICAR | Anadir `SessionConfig` dataclass + `load_session_config` + `save_session_config` |
| `src/main.py` | MODIFICAR | Anadir lifespan DB init, seed, rutas `/api/auth/login`, `/api/setup/session`, proteger endpoints existentes |
| `tests/test_auth.py` | **CREAR** | Tests de login, JWT, RBAC, inactividad |
| `tests/test_database.py` | **CREAR** | Tests de conexion DB, seed admin, modelos |
| `config.yaml` | **MODIFICADO** (runtime) | Nueva seccion `session` anadida en arranque si no existe |

---

## Arquitectura de capas

```
FastAPI (main.py, auth.py) → dominio (config.py, models.py) → persistencia (database.py, config.yaml)
```

- `main.py`: endpoints HTTP, lifespan (inicializacion DB, seed)
- `auth.py`: dependencias FastAPI (`get_current_user`, `require_role`, `check_inactivity`), funciones JWT (`create_access_token`, `verify_password`, `hash_password`)
- `config.py`: dataclasses `SystemConfig`, `SessionConfig`, carga/guardado YAML
- `models.py`: modelo SQLAlchemy `User` (mapeo a tabla `users`)
- `database.py`: `engine`, `SessionLocal` (sessionmaker), `get_db` dependency
- `seed.py`: `seed_admin_user()` (crea admin si tabla vacia)

---

## Modelo de datos: `src/models.py`

### Clase `User` (SQLAlchemy ORM)

```python
from sqlalchemy import Column, BigInteger, String, Boolean, Enum, TIMESTAMP, func
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(64), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False, default="")
    document = Column(String(32), nullable=False, default="")
    role = Column(Enum("admin", "operator", "corresponsal"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(),
                        server_onupdate=func.current_timestamp())
```

Los campos `full_name`, `document`, `is_active` pertenecen a feature 3
(`user_management`) pero se declaran aqui para que la tabla este completa desde
el inicio (la migracion se hace una sola vez).

---

## Base de datos: `src/database.py`

### Funciones / objetos

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(DATABASE_URL)  # mysql+pymysql://user:pass@mariadb:3306/sip_edge
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    """FastAPI dependency: yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

`DATABASE_URL` se construye desde variables de entorno:
`mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}`

---

## Autenticacion: `src/auth.py`

### Constantes

```python
JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = None  # No time-based expiry; inactivity-based instead
```

### Funciones

```python
def hash_password(password: str) -> str:
    """Hashes a password with bcrypt via passlib."""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_id: int, role: str) -> str:
    """Creates a JWT with sub, role, iat claims. No exp claim."""
    import time
    from jose import jwt
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    """Decodes and validates JWT. Raises JWTError on failure."""
    from jose import jwt, JWTError
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
```

### Dependencias FastAPI

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Extracts user info from JWT. Returns {'user_id': int, 'role': str}."""
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = payload.get("sub")
    role = payload.get("role")
    iat = payload.get("iat")
    if user_id is None or role is None or iat is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return {"user_id": int(user_id), "role": role, "iat": iat}

def require_role(required_role: str):
    """Factory: returns a dependency that checks role."""
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

def check_inactivity(
    current_user: dict = Depends(get_current_user),
    request: Request = None,
) -> dict:
    """Checks inactivity timeout. Raises 401 if session expired."""
    import time
    from src.config import load_session_config
    session_config = load_session_config(CONFIG_PATH)
    now = int(time.time())
    elapsed_minutes = (now - current_user["iat"]) / 60
    if elapsed_minutes > session_config.session_timeout_minutes:
        raise HTTPException(status_code=401, detail="Session expired due to inactivity")
    return current_user
```

NOTA: `check_inactivity` debe tener acceso a `CONFIG_PATH`. Alternativamente,
se puede usar `request.app.state.session` si se almacena en el estado de la app.
Se opta por leerlo del estado de la app (inyectado via `Request`) para evitar
releer el archivo YAML en cada peticion.

---

## Seed de admin: `src/seed.py`

```python
def seed_admin_user(db: Session) -> None:
    """Creates default admin if users table is empty."""
    from src.models import User
    from src.auth import hash_password
    import os

    if db.query(User).count() > 0:
        return

    password = os.environ.get("ADMIN_DEFAULT_PASSWORD", "admin")
    admin = User(
        username="admin",
        password_hash=hash_password(password),
        role="admin",
        full_name="Administrador",
        document="",
        is_active=True,
    )
    db.add(admin)
    db.commit()
```

Se invoca en el `lifespan` de FastAPI despues de `metadata.create_all()`.

---

## Modelo de sesion en `src/config.py`

### Dataclass nuevo

```python
@dataclass(frozen=True)
class SessionConfig:
    session_timeout_minutes: int  # > 0

DEFAULT_SESSION_TIMEOUT_MINUTES = 15
```

### Constantes nuevas

```python
DEFAULT_SESSION_TIMEOUT_MINUTES = 15
```

### Funciones modificadas / nuevas

`load_config` cambia su firma de retorno de `SystemConfig` a
`tuple[SystemConfig, SessionConfig]`. Esto rompe compatibilidad hacia atras con
los callers actuales (`lifespan` en `main.py`), los cuales DEBEN adaptarse.

```python
def load_config(path: str) -> tuple[SystemConfig, SessionConfig]
```

Lee el YAML completo. Para la seccion `session`, si no existe crea
`SessionConfig(DEFAULT_SESSION_TIMEOUT_MINUTES)`.

`save_config` actual solo persiste `SystemConfig`. Se reemplaza por dos
funciones que leen el YAML existente, modifican su seccion, y escriben
atomicamente:

```python
def save_system_config(config: SystemConfig, path: str) -> None

def save_session_config(config: SessionConfig, path: str) -> None
```

Ambas siguen el mismo patron atomico: cargar YAML completo, modificar la
seccion correspondiente, escribir a temp file, `os.replace()`.

### Formato `config.yaml` extendido

```yaml
rs485:
  path: /dev/ttyACM0
  baudrate: 115200
  parity: N
  data_bits: 8
  stop_bits: 1.0
rs232:
  path: /dev/ttyACM1
  baudrate: 115200
  parity: N
  data_bits: 8
  stop_bits: 1.0
gsm:
  modem_index: 0
last_updated: "2026-06-13T14:30:00"
session:
  session_timeout_minutes: 15
```

---

## Endpoints en `src/main.py`

### `POST /api/auth/login` (publico, sin autenticacion)

Request body:
```json
{"username": "admin", "password": "secret"}
```

Response 200:
```json
{"access_token": "eyJ...", "token_type": "bearer", "role": "admin"}
```

Response 401 (credenciales invalidas):
```json
{"detail": "Invalid username or password"}
```

Response 403 (rol corresponsal):
```json
{"detail": "Corresponsal role does not permit system login"}
```

Response 422 (body invalido):
```json
{"detail": "Missing required field: username"}
```

Logica:
1. Validar que body contiene `username` y `password` no vacios
2. Buscar usuario por `username` en DB
3. Si no existe → 401
4. Si `role == "corresponsal"` → 403
5. Si `verify_password()` falla → 401
6. Si `is_active` es False → 401 (feature 3, pero el chequeo se incluye aqui para robustez)
7. Generar `create_access_token(user.id, user.role)`
8. Devolver token

### `PUT /api/setup/session` (protegido, solo admin)

Headers: `Authorization: Bearer <token>`

Request body:
```json
{"session_timeout_minutes": 30}
```

Response 200:
```json
{"session_timeout_minutes": 30}
```

Response 422:
```json
{"detail": "session_timeout_minutes must be a positive integer"}
```

Dependencias: `Depends(check_inactivity)`, `Depends(require_role("admin"))`

Logica:
1. Validar que `session_timeout_minutes` es int > 0
2. Construir `SessionConfig(session_timeout_minutes=valor)`
3. `save_session_config(config, CONFIG_PATH)`
4. Actualizar `app.state.session = config`
5. Devolver JSON con el nuevo valor

### Endpoints existentes protegidos

Los endpoints existentes (`/api/config`, `/api/config/test/{port}`) DEBEN
anadirse las dependencias `check_inactivity` y `require_role("admin")`:

```python
@app.get("/api/config")
async def get_config(
    current_user: dict = Depends(check_inactivity),
    _: dict = Depends(require_role("admin")),
):
    ...
```

Esto aplica a: `GET /api/config`, `PUT /api/config`, `POST /api/config/test/{port}`.

Los endpoints publicos (`/`, `/health`, `/api/auth/login`) NO requieren
autenticacion.

---

## Lifespan modificado en `src/main.py`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Cargar configuracion YAML (system + session)
    app.state.config, app.state.session = load_config(CONFIG_PATH)

    # 2. Inicializar base de datos
    from src.database import engine
    from src.models import Base
    Base.metadata.create_all(bind=engine)

    # 3. Seed admin si tabla vacia
    from src.database import SessionLocal
    from src.seed import seed_admin_user
    db = SessionLocal()
    try:
        seed_admin_user(db)
    finally:
        db.close()

    yield
```

---

## Persistencia

### Tabla nueva: `users`

| Columna | Tipo | Nullable | Default | Notas |
|---------|------|----------|---------|-------|
| id | BIGINT UNSIGNED | NO | AUTO_INCREMENT | PK |
| username | VARCHAR(64) | NO | | UNIQUE |
| password_hash | VARCHAR(255) | NO | | bcrypt hash |
| full_name | VARCHAR(255) | NO | "" | feature 3 |
| document | VARCHAR(32) | NO | "" | feature 3 |
| role | ENUM('admin','operator','corresponsal') | NO | | |
| is_active | BOOLEAN | NO | TRUE | feature 3 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP ON UPDATE | |

Indices: UNIQUE en `username`. El indice `PRIMARY KEY` en `id` es el default.

### Migraciones

No se usa sistema de migraciones (Alembic). La tabla se crea via
`Base.metadata.create_all()` en cada arranque. Si la tabla ya existe, no se
modifica (`CREATE IF NOT EXISTS`).

### Datos semilla

Admin inicial (si la tabla `users` esta vacia):
- username: `admin`
- password: `ADMIN_DEFAULT_PASSWORD` env var (fallback `"admin"`)
- role: `admin`
- full_name: `"Administrador"`
- document: `""`
- is_active: `True`

---

## Excepciones

| Excepcion | Contexto |
|-----------|----------|
| `jose.exceptions.JWTError` | Token invalido, expirado o malformado. Capturada en `get_current_user` → HTTP 401 |
| `ValueError` | Validacion de `session_timeout_minutes` <= 0 → HTTP 422 |
| `sqlalchemy.exc.SQLAlchemyError` | Error de conexion o query a MariaDB |
| `HTTPException` (FastAPI) | Usada directamente por las dependencias para devolver 401 / 403 |

---

## Alternativas descartadas

### Alternativa 1: JWT con `exp` claim en lugar de `iat` + inactivity check

**Descartada porque:** El bloqueo por inactividad requiere que el timeout se
reinicie con cada peticion del usuario (ventana deslizante). Si usaramos `exp`,
el token tendria una fecha de caducidad fija y el usuario seria expulsado a los
N minutos independientemente de si estuvo activo. El enfoque `iat` permite que
cada peticion extienda implicitamente la sesion al validar `now - iat <=
timeout`. Si se quisiera un verdadero "sliding window" con renovacion de `iat`,
eso seria una feature futura. Por ahora, el timeout se mide desde la emision del
token (login) y el usuario debe re-login tras N minutos de inactividad.

### Alternativa 2: Usar SQLite en lugar de MariaDB para auth

**Descartada porque:** La decision de arquitectura ya establecida por el humano
especifica MariaDB. SQLite no soporta el tipo `ENUM` nativo y crearia una
divergencia entre desarrollo y produccion. Ademas, MariaDB ya esta corriendo en
Docker via `compose.yml`.

### Alternativa 3: Usar `fastapi-users` library

**Descartada porque:** El proyecto sigue la regla de "sin dependencias externas"
salvo las ya aprobadas en `requirements.txt`. `fastapi-users` anadiria
dependencias adicionales (fastapi-mail, httpx-oauth, etc.) sin justificacion
suficiente para este caso de uso. La combinacion `python-jose` + `passlib` +
`bcrypt` ya cubre todas las necesidades y ya estan en `requirements.txt`.

### Alternativa 4: SessionConfig como campo de SystemConfig

**Descartada porque:** `SystemConfig` representa configuracion de hardware y
tiene su propia logica de validacion (baudrate, parity, etc.). Mezclar
`session_timeout_minutes` en `SystemConfig` viola el principio de
responsabilidad unica (SRP). Mantener `SessionConfig` como dataclass separado
permite que cada endpoint acceda solo a la configuracion que necesita.

### Alternativa 5: Usar middleware de FastAPI en lugar de dependencias para inactivity

**Descartada porque:** Las dependencias de FastAPI permiten un control mas
granular: se puede aplicar `check_inactivity` selectivamente a endpoints
protegidos, mientras que un middleware afectaria a todas las rutas incluyendo
`/health`, `/`, y `/api/auth/login`. Ademas, las dependencias permiten inyectar
`current_user` en el endpoint, algo que un middleware no puede hacer
limpiamente.

---

## Tests

### `tests/test_database.py`

Usa `tempfile.TemporaryDirectory()` + SQLite en memoria (via
`sqlalchemy.create_engine("sqlite://")`) para tests de modelos y seed. Esto evita
depender de MariaDB real en tests unitarios. Se usa `Base.metadata.create_all()`
contra el engine de SQLite en memoria.

NOTA: SQLite no soporta `ENUM` nativo. Para tests se usa `VARCHAR` en el
modelo, o se usa un dialecto SQLite que ignore `ENUM`. Alternativamente, se
puede usar `pytest` con una base MariaDB de test si esta disponible en Docker.
Decision: usar SQLite en memoria para tests unitarios (rapido, sin Docker), y
MariaDB real solo para tests de integracion.

Clases de test:
- `TestUserModel`: creacion de instancia, campos requeridos, valores default
- `TestSeedAdmin`: `seed_admin_user` crea admin cuando tabla vacia, no duplica
- `TestHashPassword`: bcrypt hash/verify roundtrip

### `tests/test_auth.py`

Usa `TestClient` con una app FastAPI que tiene MariaDB o SQLite en memoria.
Se necesita una fixture que:
1. Cree la tabla `users`
2. Inserte usuarios de prueba (admin, operator, corresponsal)
3. Ejecute los tests de endpoints

Clases de test:
- `TestLoginEndpoint`: login valido → 200 + token, credenciales invalidas → 401,
  campos faltantes → 422, corresponsal → 403
- `TestAuthDependencies`: token valido → extrae user, token invalido → 401,
  sin token → 401, rol incorrecto → 403
- `TestInactivity`: token recien creado → ok, token con iat antiguo
  (simulado) → 401 "Session expired"
- `TestSessionEndpoint`: `PUT /api/setup/session` con admin → 200, sin token
  → 401, con rol operator → 403, valor <= 0 → 422

---

## `github_labels`

No se requieren etiquetas adicionales.
