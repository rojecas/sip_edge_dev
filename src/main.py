"""SIP-Edge: Sistema Inteligente de Pesaje y Control de Materia Extrana."""
import asyncio
import json
import logging
import os
import subprocess
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.auth import (
    LoginRequest,
    SessionTimeoutRequest,
    TokenResponse,
    check_inactivity,
    create_access_token,
    get_current_user,
    require_role,
    verify_password,
)
from src.config import (
    BackupConfig,
    GsmConfig,
    ScaleConfig,
    SerialPortConfig,
    SessionConfig,
    SmsConfig,
    SystemConfig,
    VALID_TEST_PORTS,
    load_config,
    save_scale_config,
    save_session_config,
    save_system_config,
    validate_config,
)
import src.database as _db
from src.database import get_db, init_db
from src.models import BackupLog, Base, User, Weighing
from src.sms_service import SMSService
from src.haciendas import haciendas_router, suertes_router
from src.weighings import router as weighings_router
from src.users import router as users_router

logger = logging.getLogger(__name__)

CONFIG_PATH = "config.yaml"

scale_clients: set[WebSocket] = set()


def _resolve_event_loop() -> asyncio.AbstractEventLoop:
    """Resuelve el event loop: usa el running loop o crea uno nuevo."""
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.new_event_loop()


def _on_scale_data(data: dict, clients: set[WebSocket]) -> None:
    message = json.dumps({
        "type": "scale_reading",
        "data": {
            "net_weight": data.get("net_weight", 0.0),
            "is_stable": data.get("is_stable", False),
            "unit": data.get("unit", "kg"),
        },
    })
    loop = _resolve_event_loop()
    for ws in list(clients):
        try:
            asyncio.run_coroutine_threadsafe(
                ws.send_text(message), loop
            )
        except Exception:
            clients.discard(ws)


@asynccontextmanager
async def lifespan(app: FastAPI):
    (
        app.state.config,
        app.state.session,
        app.state.scale_config,
        app.state.backup_config,
        app.state.sms_config,
    ) = load_config(CONFIG_PATH)
    from src.scale import ScaleService

    dev_mode = os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes")
    app.state.scale_service = ScaleService(
        app.state.scale_config, app.state.config.rs485, dev_mode=dev_mode
    )
    app.state.scale_service.start()
    app.state.scale_service.async_listener(
        lambda data: _on_scale_data(data, scale_clients)
    )
    init_db()
    Base.metadata.create_all(bind=_db.engine)
    from src.seed import seed_admin_user

    db = _db.SessionLocal()
    try:
        seed_admin_user(db)
    finally:
        db.close()

    # Inicializar SMSService
    sms_config: SmsConfig = app.state.sms_config
    modem_index = app.state.config.gsm.modem_index
    app.state.sms_service = SMSService(sms_config, modem_index, dev_mode=dev_mode)
    app.state.sms_service.start_scheduler()

    yield

    app.state.sms_service.stop_scheduler()
    app.state.scale_service.stop()


app = FastAPI(
    title="SIP-Edge",
    description="Sistema Inteligente de Pesaje y Control de Materia Extrana",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(users_router)
app.include_router(haciendas_router)
app.include_router(suertes_router)
app.include_router(weighings_router)

backup_router = APIRouter(prefix="/api/backup", tags=["backup"])


@backup_router.get("/status")
async def get_backup_status(
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    logs = (
        db.query(BackupLog)
        .order_by(BackupLog.created_at.desc())
        .limit(10)
        .all()
    )
    return [
        {
            "id": log.id,
            "filename": log.filename,
            "file_size": log.file_size,
            "local_checksum": log.local_checksum,
            "usb_copied": log.usb_copied,
            "usb_checksum": log.usb_checksum,
            "error_message": log.error_message,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


def _run_backup_background():
    """Wrapper para ejecutar backup en background thread."""
    from src.backup import run_backup
    config: BackupConfig = app.state.backup_config
    run_backup(config.usb_mount_path, config.local_dir, config.keep_days)


@backup_router.post("/run")
async def run_backup_endpoint(
    background_tasks: BackgroundTasks,
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_role("admin")),
):
    background_tasks.add_task(_run_backup_background)
    return JSONResponse(
        status_code=202,
        content={"status": "accepted", "message": "Backup started"},
    )


app.include_router(backup_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "ok", "service": "SIP-Edge", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.websocket("/ws/scale")
async def websocket_scale(websocket: WebSocket):
    await websocket.accept()
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return
    from src.auth import decode_access_token
    from jose import JWTError
    try:
        payload = decode_access_token(token)
    except JWTError:
        await websocket.close(code=4001)
        return
    role = payload.get("role")
    if role not in ("admin", "operator"):
        await websocket.close(code=4001)
        return
    scale_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        scale_clients.discard(websocket)


@app.post("/api/auth/login")
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if user.role == "corresponsal":
        raise HTTPException(
            status_code=403, detail="Corresponsal role does not permit system login"
        )
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not verify_password(body.password, user.password_hash):
        # Contador de intentos fallidos
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        db.commit()
        if user.failed_login_attempts >= 3:
            sms_service = app.state.sms_service
            alert_msg = (
                f"Alerta de seguridad: El usuario '{user.username}' "
                f"ha acumulado {user.failed_login_attempts} intentos fallidos "
                f"de inicio de sesion."
            )
            sms_service.send_alert_to_admins(alert_msg)
            user.failed_login_attempts = 0
            db.commit()
        raise HTTPException(status_code=401, detail="Invalid username or password")
    # Login exitoso: resetear contador
    if user.failed_login_attempts != 0:
        user.failed_login_attempts = 0
        db.commit()
    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token, token_type="bearer", role=user.role)


@app.put("/api/setup/session")
async def put_session(
    body: SessionTimeoutRequest,
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_role("admin")),
):
    config = SessionConfig(session_timeout_minutes=body.session_timeout_minutes)
    save_session_config(config, CONFIG_PATH)
    app.state.session = config
    return {"session_timeout_minutes": config.session_timeout_minutes}


class ScaleTimeoutRequest(BaseModel):
    timeout_seconds: int = Field(ge=1, le=10)


@app.put("/api/setup/scale")
async def put_scale_config(
    body: ScaleTimeoutRequest,
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_role("admin")),
):
    config = ScaleConfig(timeout_seconds=body.timeout_seconds)
    save_scale_config(config, CONFIG_PATH)
    app.state.scale_config = config
    if hasattr(app.state, "scale_service") and app.state.scale_service is not None:
        app.state.scale_service.update_timeout(config.timeout_seconds)
    return {"timeout_seconds": config.timeout_seconds}


@app.get("/api/config")
async def get_config(
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_role("admin")),
):
    config: SystemConfig = app.state.config
    return JSONResponse(content=asdict(config))


@app.put("/api/config")
async def put_config(
    request: Request,
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_role("admin")),
):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid JSON body"},
        )
    try:
        new_config = SystemConfig(
            rs485=SerialPortConfig(**body["rs485"]),
            rs232=SerialPortConfig(**body["rs232"]),
            gsm=GsmConfig(**body["gsm"]),
            last_updated=datetime.now(timezone.utc).isoformat(),
        )
        validate_config(new_config)
        save_system_config(new_config, CONFIG_PATH)
        app.state.config = new_config
        return JSONResponse(content=asdict(new_config))
    except (KeyError, TypeError) as e:
        return JSONResponse(
            status_code=422,
            content={"detail": f"Missing or invalid field: {e}"},
        )
    except ValueError as e:
        return JSONResponse(
            status_code=422,
            content={"detail": str(e)},
        )


@app.post("/api/config/test/{port}")
async def test_port(
    port: str,
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_role("admin")),
):
    if port not in VALID_TEST_PORTS:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Unknown port '{port}'. Valid: rs485, rs232, gsm"},
        )
    config: SystemConfig = app.state.config
    if port in ("rs485", "rs232"):
        serial_cfg = config.rs485 if port == "rs485" else config.rs232
        import serial

        try:
            ser = serial.Serial(
                port=serial_cfg.path,
                baudrate=serial_cfg.baudrate,
                parity=serial_cfg.parity,
                bytesize=serial_cfg.data_bits,
                stopbits=serial_cfg.stop_bits,
                timeout=1,
            )
            ser.close()
            return JSONResponse(content={"status": "ok"})
        except (serial.SerialException, OSError) as e:
            return JSONResponse(content={"status": "fail", "detail": str(e)})
    if port == "gsm":
        try:
            result = subprocess.run(
                ["mmcli", "-m", str(config.gsm.modem_index)],
                capture_output=True,
                timeout=10,
            )
            if result.returncode == 0:
                return JSONResponse(content={"status": "ok"})
            return JSONResponse(
                content={
                    "status": "fail",
                    "detail": result.stderr.decode().strip() or f"exit code {result.returncode}",
                }
            )
        except FileNotFoundError:
            return JSONResponse(
                content={"status": "fail", "detail": "mmcli not found"},
            )
        except subprocess.TimeoutExpired:
            return JSONResponse(
                content={"status": "fail", "detail": "mmcli timed out"},
            )
        except OSError as e:
            return JSONResponse(
                content={"status": "fail", "detail": str(e)},
            )
