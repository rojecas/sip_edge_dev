# Design — Captura de Pesaje Multipaso con Confirmacion y Envio RS232

## Archivos nuevos

| Archivo | Proposito |
|---------|-----------|
| `src/weighings.py` | Pydantic schemas + endpoints CRUD para weighings, WebSocket `/ws/scale` |
| `tests/test_weighings.py` | Tests unitarios con SQLite in-memory |

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/models.py` | Anadir modelo ORM `Weighing` |
| `src/main.py` | Registrar `weighings_router`; anadir endpoint WebSocket `/ws/scale`; registrar callback async del ScaleService; exponer endpoint GET `/api/haciendas` y GET `/api/suertes` con rol operator |
| `src/haciendas.py` | Refactorizar routers para aceptar rol operator en endpoints GET (haciendas list, suertes list con filtro) |
| `src/auth.py` | Anadir helper `require_any_role` para permitir admin y operator en weighings |

## Modelo ORM nuevo: `Weighing` (en `src/models.py`)

```python
class Weighing(Base):
    __tablename__ = "weighings"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    tractomula = Column(String(32), nullable=False, default="")
    vagon = Column(String(32), nullable=False, default="")
    numero_guia = Column(String(32), nullable=False, default="")
    hacienda_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("haciendas.id"), nullable=False)
    suerte_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("suertes.id"), nullable=False)
    peso_muestra = Column(Numeric(10, 3), nullable=False)
    peso_mineral = Column(Numeric(10, 3), nullable=False)
    peso_vegetal_extrano = Column(Numeric(10, 3), nullable=False)
    usuario_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("users.id"), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    enviado_pc = Column(Boolean, nullable=False, default=False)
```

## Persistencia

### Tabla nueva: `weighings`

| Columna              | Tipo             | Nullable | Default           | Notas                        |
|----------------------|------------------|----------|-------------------|------------------------------|
| id                   | BIGINT UNSIGNED  | NO       | AUTO_INCREMENT    | PK                           |
| fecha                | DATE             | NO       |                   | Fecha actual del servidor    |
| hora                 | TIME             | NO       |                   | Hora actual del servidor     |
| tractomula           | VARCHAR(32)      | NO       | ''                | Texto libre                  |
| vagon                | VARCHAR(32)      | NO       | ''                | Texto libre                  |
| numero_guia          | VARCHAR(32)      | NO       | ''                | Texto libre                  |
| hacienda_id          | BIGINT UNSIGNED  | NO       |                   | FK → haciendas.id            |
| suerte_id            | BIGINT UNSIGNED  | NO       |                   | FK → suertes.id              |
| peso_muestra         | DECIMAL(10,3)    | NO       |                   |                              |
| peso_mineral         | DECIMAL(10,3)    | NO       |                   |                              |
| peso_vegetal_extrano | DECIMAL(10,3)    | NO       |                   |                              |
| usuario_id           | BIGINT UNSIGNED  | NO       |                   | FK → users.id                |
| created_at           | TIMESTAMP        | NO       | CURRENT_TIMESTAMP |                              |
| enviado_pc           | BOOLEAN          | NO       | FALSE             | TRUE si RS232 envio exitoso  |

FK: `FOREIGN KEY (hacienda_id) REFERENCES haciendas(id)`
FK: `FOREIGN KEY (suerte_id) REFERENCES suertes(id)`
FK: `FOREIGN KEY (usuario_id) REFERENCES users(id)`

### Migraciones
1. `database/migrations/2026_06_13_000003_create_weighings.py`

## Esquemas Pydantic (en `src/weighings.py`)

```python
class WeighingCreate(BaseModel):
    tractomula: str = Field(default="", max_length=32)
    vagon: str = Field(default="", max_length=32)
    numero_guia: str = Field(default="", max_length=32)
    hacienda_id: int = Field(gt=0)
    suerte_id: int = Field(gt=0)
    peso_muestra: Decimal = Field(ge=0, decimal_places=3)
    peso_mineral: Decimal = Field(ge=0, decimal_places=3)
    peso_vegetal_extrano: Decimal = Field(ge=0, decimal_places=3)

class WeighingResponse(BaseModel):
    id: int
    fecha: date
    hora: time
    tractomula: str
    vagon: str
    numero_guia: str
    hacienda_id: int
    suerte_id: int
    peso_muestra: Decimal
    peso_mineral: Decimal
    peso_vegetal_extrano: Decimal
    usuario_id: int
    created_at: datetime
    enviado_pc: bool
    class Config: from_attributes = True

class ResetResponse(BaseModel):
    mensaje: str = "Formulario reiniciado"
```

## `require_any_role` helper (en `src/auth.py`)

```python
def require_any_role(*roles: str):
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker
```

## Endpoints

### `POST /api/weighings` — Confirmar pesaje

```python
@router.post("", response_model=WeighingResponse, status_code=201)
def create_weighing(
    body: WeighingCreate,
    current_user: dict = Depends(check_inactivity),
    _: dict = Depends(require_any_role("admin", "operator")),
    db: Session = Depends(get_db),
):
    # Validar que hacienda existe
    # Validar que suerte existe y pertenece a hacienda
    # Establecer fecha, hora = now()
    # Establecer usuario_id = current_user["user_id"]
    # Crear Weighing
    # Commit
    # Intentar send_frame con pesos + metadata
    # Si send_frame ok -> enviado_pc = True, commit again
    # Si send_frame falla -> log error, no rollback
    # Return created record
```

### `GET /api/weighings` — Listar pesajes

```python
@router.get("", response_model=List[WeighingResponse])
def list_weighings(
    current_user: dict = Depends(check_inactivity),
    _: dict = Depends(require_any_role("admin", "operator")),
    db: Session = Depends(get_db),
):
    if current_user["role"] == "admin":
        return db.query(Weighing).all()
    # operator: solo propios
    return db.query(Weighing).filter(
        Weighing.usuario_id == current_user["user_id"]
    ).all()
```

### `GET /api/weighings/{id}` — Obtener pesaje

```python
@router.get("/{weighing_id}", response_model=WeighingResponse)
def get_weighing(
    weighing_id: int,
    current_user: dict = Depends(check_inactivity),
    _: dict = Depends(require_any_role("admin", "operator")),
    db: Session = Depends(get_db),
):
    w = db.query(Weighing).filter(Weighing.id == weighing_id).first()
    if w is None:
        raise HTTPException(404, "Weighing not found")
    if current_user["role"] == "operator" and w.usuario_id != current_user["user_id"]:
        raise HTTPException(404, "Weighing not found")
    return w
```

### `POST /api/weighings/reset` — Reset formulario

```python
@router.post("/reset", response_model=ResetResponse)
def reset_weighing_form(
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_any_role("admin", "operator")),
):
    # Backend state cleanup (if any), otherwise just acknowledge
    return ResetResponse()
```

### `WS /ws/scale` — WebSocket de lecturas de balanza

```python
@app.websocket("/ws/scale")
async def websocket_scale(websocket: WebSocket):
    await websocket.accept()
    # Verificar token via query param
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return
    try:
        payload = decode_access_token(token)
    except JWTError:
        await websocket.close(code=4001)
        return
    role = payload.get("role")
    if role not in ("admin", "operator"):
        await websocket.close(code=4001)
        return
    # Registrar este websocket en un set de clientes
    scale_clients.add(websocket)
    try:
        while True:
            # Keep connection alive, receive pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        scale_clients.discard(websocket)
```

El `ScaleService` callback (registrado en lifespan) itera sobre
`scale_clients` y envía cada lectura:

```python
def _on_scale_data(data: dict):
    message = json.dumps({
        "type": "scale_reading",
        "data": {"net_weight": data.get("net_weight", 0.0),
                 "is_stable": data.get("is_stable", False),
                 "unit": data.get("unit", "kg")}
    })
    for ws in list(scale_clients):
        try:
            asyncio.run_coroutine_threadsafe(
                ws.send_text(message), main_loop
            )
        except Exception:
            scale_clients.discard(ws)
```

## RS232 stubbing para feature 6

El modulo `src.rs232` NO existe en feature 6. Feature 11 lo creara.
Feature 6 DEBE llamar a `send_frame` de la siguiente forma:

```python
try:
    from src.rs232 import send_frame
    send_frame(frame_data, format="json")
    record.enviado_pc = True
except ImportError:
    # Module not implemented yet (feature 11), continue
    pass
except Exception as e:
    logger.error("RS232 send failed: %s", e)
    # Do NOT rollback, just log
```

`frame_data` es un dict con:
```python
{
    "fecha": "2026-06-13",
    "hora": "21:45:00",
    "tractomula": "ABC123",
    "vagon": "VAG-01",
    "numero_guia": "G-2026-001",
    "hacienda": {"id": 1, "codigo": "H001", "nombre": "Hacienda Uno"},
    "suerte": {"id": 1, "codigo_suerte": "A1"},
    "pesos": {
        "muestra": 1.250,
        "mineral": 0.800,
        "vegetal_extrano": 0.050
    }
}
```

## Haciendas/Suertes endpoints — refactor para rol operator

Los endpoints GET de `haciendas_router` y `suertes_router` actualmente
usan `require_role("admin")`. Feature 6 necesita que operator tambien
pueda leer haciendas y suertes (para el dropdown del formulario).

Se anade un nuevo router (o se modifica el existente) para exponer
endpoints GET con `require_any_role("admin", "operator")`:

```python
haciendas_read_router = APIRouter(prefix="/api/haciendas")

@haciendas_read_router.get("", response_model=List[HaciendaResponse])
def get_haciendas_read(
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_any_role("admin", "operator")),
    db: Session = Depends(get_db),
):
    return list_haciendas(db)

@haciendas_read_router.get("/{hacienda_id}", response_model=HaciendaResponse)
def get_hacienda_by_id_read(
    hacienda_id: int,
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_any_role("admin", "operator")),
    db: Session = Depends(get_db),
):
    return get_hacienda(db, hacienda_id)
```

Los endpoints write (POST, PUT, DELETE) permanecen admin-only.

## Modificaciones en `src/main.py`

```python
from src.weighings import weighings_router

app.include_router(weighings_router)

scale_clients: set[WebSocket] = set()

# En lifespan, despues de start():
def _scale_callback(data):
    _on_scale_data(data, scale_clients, asyncio.get_event_loop())
app.state.scale_service.async_listener(_scale_callback)
```

## Inicializacion de la tabla

`Base.metadata.create_all(bind=_db.engine)` en lifespan ya importa
todos los modelos via `from src.models import Base, User, Hacienda,
Suerte, Weighing`. Se debe actualizar el import en `src/main.py`.

## Alternativa descartada

**WebSocket con autenticacion por token en headers HTTP.** Se descarto
porque el API de WebSocket de Starlette/FastAPI no permite headers
personalizados en la conexion inicial (solo se puede pasar token via
query param). Alternativa considerada: autenticar en el primer mensaje
(texto JSON con token). Se eligio query param por simplicidad y porque
el token viaja en HTTPS/WSS, por lo que es seguro.

**Polling via `GET /api/scale/current-reading`.** Se descarto en favor
de WebSocket porque la balanza puede enviar datos espontaneamente
(boton PRINT) y el polling introduce latencia innecesaria. WebSocket
proporciona actualizaciones en tiempo real para el focus management.

## GitHub labels

`weighing`, `capture`, `operator`, `scale`, `rs232`, `websocket`, `multistep`
