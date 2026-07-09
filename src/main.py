"""SIP-Edge: Sistema Inteligente de Pesaje y Control de Materia Extrana."""
import asyncio
import json
import logging
import math
import os
import subprocess
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import datetime, timezone

from src.sd_notify import notify as sd_notify

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
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
    AgentConfig,
    BackupConfig,
    GsmConfig,
    ScaleConfig,
    SerialPortConfig,
    SessionConfig,
    SmsConfig,
    SystemConfig,
    VALID_TEST_PORTS,
    load_config,
    save_agent_config,
    save_scale_config,
    save_session_config,
    save_system_config,
    validate_config,
)
from src.schemas import PaginatedResponse
import src.database as _db
from src.database import get_db, init_db
from src.models import BackupLog, Base, User, Weighing
from src.sms_service import SMSService
from src.sms_incoming import IncomingSmsDispatcher  # Legacy v1, kept for test references
from src.sms_persistence import SmsPersistenceService
from src.sms_dispatcher_v2 import IncomingSmsDispatcherV2
from src.sms_send_queue import SmsSendQueue
from src.emergency_mode import EmergencyModeService, emergency_router
from src.password_reset import PasswordResetService, password_reset_router
from src.report_templates import TemplateNotFoundError
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



def _find_quectel_modem() -> int:
    import re
    """Auto-detecta el indice del modem Quectel EC25 via mmcli -L.
    
    Escanea los modems disponibles y retorna el indice del primero que coincida
    con QUECTEL. Si no encuentra ninguno, retorna 0 como fallback.
    El indice puede cambiar tras resets del modem o rearranques del sistema.
    """
    if os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes"):
        return 0
    try:
        result = subprocess.run(
            ["mmcli", "-L"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                m = re.search(r"/Modem/(\d+)\s+\[.*?\]\s+(.+)", line)
                if m and "QUECTEL" in m.group(2).upper():
                    idx = int(m.group(1))
                    logger.info("Modem Quectel auto-detectado: indice %s", idx)
                    return idx
            logger.warning(
                "No se encontro modem Quectel via mmcli -L. Usando fallback 0.\n%s",
                result.stdout,
            )
        else:
            logger.warning("mmcli -L fallo (rc=%s). Usando fallback 0.", result.returncode)
    except FileNotFoundError:
        logger.warning("mmcli no encontrado. Usando fallback 0.")
    except subprocess.TimeoutExpired:
        logger.warning("mmcli -L timed out. Usando fallback 0.")
    except OSError as exc:
        logger.warning("Error ejecutando mmcli -L: %s. Usando fallback 0.", exc)
    return 0

@asynccontextmanager
async def lifespan(app: FastAPI):
    (
        app.state.config,
        app.state.session,
        app.state.scale_config,
        app.state.backup_config,
        app.state.sms_config,
        app.state.agent_config,
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

    # Configurar logging
    logging.basicConfig(level=logging.INFO, force=True)
    logging.getLogger("src.agent_orchestrator").setLevel(logging.INFO)
    logging.getLogger("src.sms_send_queue").setLevel(logging.INFO)

    # Inicializar SMSService
    sms_config: SmsConfig = app.state.sms_config
    modem_index = _find_quectel_modem()
    app.state.sms_service = SMSService(sms_config, modem_index, dev_mode=dev_mode)

    # Inicializar SmsPersistenceService (F27)
    app.state.sms_persistence = SmsPersistenceService(
        db_session_factory=_db.SessionLocal,
    )
    # Inyectar persistencia en sms_service
    app.state.sms_service.set_persistence_service(app.state.sms_persistence)

    # Inicializar SmsSendQueue (F27) ΓÇö cola de envio asincrona
    app.state.sms_send_queue = SmsSendQueue(
        persistence=app.state.sms_persistence,
        sms_service=app.state.sms_service,
        modem_index=modem_index,
        timeout_seconds=20,
        poll_interval=2.0,
        min_send_interval=60,
    )
    app.state.sms_send_queue.start()
    app.state.sms_service.set_send_queue(app.state.sms_send_queue)

    # Inicializar ReportTemplateService
    from src.report_templates import ReportTemplateService
    app.state.report_template_service = ReportTemplateService(
        db_session_factory=_db.SessionLocal
    )

    # Inicializar SMSService con report_template_service (se pasa referencia)
    app.state.sms_service.set_template_service(app.state.report_template_service)
    app.state.sms_service.start_scheduler()

    # Inicializar IncomingSmsDispatcherV2 (F27) ΓÇö reemplaza v1
    app.state.sms_dispatcher = IncomingSmsDispatcherV2(
        modem_index=modem_index, dev_mode=dev_mode,
        persistence=app.state.sms_persistence,
    )

    # Inicializar EmergencyModeService (F27: con persistencia inyectada)
    app.state.emergency_service = EmergencyModeService(
        db_session_factory=_db.SessionLocal,
        sms_service=app.state.sms_service,
        modem_index=modem_index,
        dev_mode=dev_mode,
        sms_persistence=app.state.sms_persistence,
    )
    # Restaurar estado desde BD
    app.state.emergency_service.restore_from_db()
    # Iniciar tarea de expiry checker
    await app.state.emergency_service.start()

    # Inicializar PasswordResetService (F27: con persistencia inyectada)
    app.state.password_reset_service = PasswordResetService(
        db_session_factory=_db.SessionLocal,
        sms_service=app.state.sms_service,
        sms_persistence=app.state.sms_persistence,
    )

    # Inicializar clientes LLM dual (local + remote DeepSeek)
    agent_config: AgentConfig = app.state.agent_config
    from src.llm_client import LlamaClient, DualBackendClient

    # Cliente local (llama.cpp)
    local_client = LlamaClient(
        base_url=agent_config.llm_url,
        model=agent_config.llm_model,
        timeout=agent_config.llm_timeout,
        dev_mode=dev_mode,
    )

    # Cliente remoto (DeepSeek)
    deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    deepseek_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
    remote_client = LlamaClient(
        base_url=deepseek_url,
        model=deepseek_model,
        timeout=20,
        dev_mode=False,
        api_key=deepseek_api_key,
    )

    # DualBackendClient con circuit breaker
    ai_primary_backend = os.getenv("AI_PRIMARY_BACKEND", "local")
    if ai_primary_backend == "remote":
        app.state.llm_client = DualBackendClient(
            primary=remote_client,
            secondary=local_client,
            cooldown=30,
        )
    else:
        app.state.llm_client = DualBackendClient(
            primary=local_client,
            secondary=remote_client,
            cooldown=30,
        )

    # Inicializar SqlTools
    from src.sql_tools import SqlTools
    app.state.sql_tools = SqlTools(db_session_factory=_db.SessionLocal)

    # Inicializar AnomalyDetector
    from src.anomaly_detector import AnomalyDetector
    app.state.anomaly_detector = AnomalyDetector(
        db_session_factory=_db.SessionLocal,
        config=agent_config,
    )

    # Inicializar AgentOrchestrator
    from src.agent_orchestrator import AgentOrchestrator
    app.state.agent_orchestrator = AgentOrchestrator(
        llm_client=app.state.llm_client,
        sql_tools=app.state.sql_tools,
        sms_service=app.state.sms_service,
        db_session_factory=_db.SessionLocal,
    )

    # Registrar handlers en dispatcher v2 (F27: orden importa)
    # 1. Emergency ΓÇö workflow_type='emergency'
    app.state.sms_dispatcher.register_handler(
        app.state.emergency_service.process_incoming_sms,
        workflow_type="emergency",
    )
    # 2. Password reset ΓÇö workflow_type='password_reset'
    app.state.sms_dispatcher.register_handler(
        app.state.password_reset_service.handle_incoming_sms,
        workflow_type="password_reset",
    )
    # 3. AI query ΓÇö retorna False si falla, no es catch-all
    app.state.sms_dispatcher.register_handler(
        lambda phone, text, message_id=None, conversation_id=None: app.state.agent_orchestrator.handle_sms_query(phone, text),
        workflow_type="ai_query",
    )
    # Iniciar dispatcher v2 de SMS entrantes (el v1 NO se inicia)
    await app.state.sms_dispatcher.start()

    # --- Watchdog heartbeat para systemd sd_notify ---
    async def _watchdog_heartbeat():
        """Envia WATCHDOG=1 cada 25s para evitar que systemd mate el proceso."""
        while True:
            try:
                await asyncio.sleep(25)
                sd_notify()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Watchdog heartbeat error")

    watchdog_task = asyncio.create_task(_watchdog_heartbeat())
    # -------------------------------------------------

    yield

    watchdog_task.cancel()
    try:
        await watchdog_task
    except asyncio.CancelledError:
        pass

    await app.state.sms_dispatcher.stop()
    app.state.sms_send_queue.stop()
    await app.state.emergency_service.stop()
    app.state.sms_service.stop_scheduler()
    app.state.llm_client.close()
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
app.include_router(emergency_router)
app.include_router(password_reset_router)

backup_router = APIRouter(prefix="/api/backup", tags=["backup"])


class BackupLogResponse(BaseModel):
    """Response schema for a single backup log entry."""
    id: int
    filename: str
    file_size: int
    local_checksum: str
    usb_copied: bool
    usb_checksum: str | None = None
    error_message: str | None = None
    created_at: str  # ISO format

    class Config:
        from_attributes = True


def _backup_log_to_response(log: BackupLog) -> BackupLogResponse:
    return BackupLogResponse(
        id=log.id,
        filename=log.filename,
        file_size=log.file_size,
        local_checksum=log.local_checksum,
        usb_copied=log.usb_copied,
        usb_checksum=log.usb_checksum,
        error_message=log.error_message,
        created_at=log.created_at.isoformat(),
    )


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
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


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

# ------------------------------------------------------------------
# Agent Router ΓÇö POST /api/agent/query (T21)
# ------------------------------------------------------------------

agent_router = APIRouter(prefix="/api/agent", tags=["agent"])


class AgentQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)


class AgentQueryResponse(BaseModel):
    response: str
    dev_mode: bool


@agent_router.post("/query")
async def agent_query(
    body: AgentQueryRequest,
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_role("admin")),
):
    """Envia una consulta directa al agente inteligente (para pruebas)."""
    orchestrator = app.state.agent_orchestrator
    sql_tools = app.state.sql_tools
    llm_client = app.state.llm_client

    messages = [
        {
            "role": "system",
            "content": (
                "Eres un asistente de analisis de datos de pesaje agricola (SIP-Edge). "
                "Responde consultas usando exclusivamente las herramientas SQL disponibles. "
                "NUNCA inventes numeros. Responde en espanol."
            ),
        },
        {"role": "user", "content": body.query},
    ]

    from src.sql_tools import TOOL_DEFINITIONS

    try:
        response = llm_client.chat_completion(messages, tools=TOOL_DEFINITIONS)
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"detail": f"LLM error: {str(e)}"},
        )

    choices = response.get("choices", [])
    if not choices:
        return AgentQueryResponse(response="No se pudo procesar la consulta.", dev_mode=os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes"))

    msg = choices[0].get("message", {})
    tool_calls = msg.get("tool_calls", [])

    if tool_calls:
        # Ejecutar tools
        for tc in tool_calls:
            func_info = tc.get("function", {})
            tool_name = func_info.get("name", "")
            try:
                arguments = json.loads(func_info.get("arguments", "{}"))
            except json.JSONDecodeError:
                arguments = {}
            try:
                result = sql_tools.execute_tool(tool_name, arguments)
            except Exception as e:
                result = {"error": str(e)}
            messages.append({
                "role": "assistant",
                "content": msg.get("content"),
                "tool_calls": [tc],
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })
        # Segunda vuelta: NO forzar tool_calls, permitir que el LLM parafrasee
        try:
            response2 = llm_client.chat_completion(messages, tools=None)
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={"detail": f"LLM error on second pass: {str(e)}"},
            )
        choices2 = response2.get("choices", [])
        if choices2:
            final_text = choices2[0].get("message", {}).get("content", "")
            return AgentQueryResponse(response=final_text or "Sin respuesta.", dev_mode=os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes"))
        return AgentQueryResponse(response="No se pudo generar respuesta.", dev_mode=os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes"))

    direct_content = msg.get("content", "")
    return AgentQueryResponse(response=direct_content or "Sin respuesta.", dev_mode=os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes"))


app.include_router(agent_router)

# ------------------------------------------------------------------
# Report Templates Router ΓÇö CRUD (T22)
# ------------------------------------------------------------------

reports_router = APIRouter(prefix="/api/reports", tags=["reports"])


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    schedule: list[str] = Field(default_factory=list)
    user_ids: list[int] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    is_active: bool = True


class TemplateUpdate(BaseModel):
    name: str | None = None
    schedule: list[str] | None = None
    user_ids: list[int] | None = None
    metrics: list[str] | None = None
    is_active: bool | None = None


@reports_router.get("/templates")
async def list_templates(
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_role("admin")),
):
    svc = app.state.report_template_service
    templates = svc.get_all()
    return templates


@reports_router.post("/templates", status_code=201)
async def create_template(
    body: TemplateCreate,
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_role("admin")),
):
    svc = app.state.report_template_service
    try:
        template = svc.create(body.model_dump())
        return svc.get_one(template.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@reports_router.put("/templates/{template_id}")
async def update_template(
    template_id: int,
    body: TemplateUpdate,
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_role("admin")),
):
    svc = app.state.report_template_service
    try:
        data = {k: v for k, v in body.model_dump().items() if v is not None}
        svc.update(template_id, data)
        return svc.get_one(template_id)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@reports_router.delete("/templates/{template_id}", status_code=204)
async def delete_template(
    template_id: int,
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_role("admin")),
):
    svc = app.state.report_template_service
    try:
        svc.delete(template_id)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


app.include_router(reports_router)

# ------------------------------------------------------------------
# Anomaly Router ΓÇö GET /api/anomalies (T23)
# ------------------------------------------------------------------

anomaly_router = APIRouter(prefix="/api/anomalies", tags=["anomalies"])


@anomaly_router.get("")
async def detect_anomalies_on_demand(
    window: int = 120,
    threshold: float = 3.0,
    tipo_cosecha: str | None = Query(None),
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


class AnomalyLogResponse(BaseModel):
    """Response schema for a single anomaly log entry."""
    id: int
    record_id: int
    layer: str
    z_score: float | None = None
    metric_value: float
    threshold: float
    llm_report: str | None = None
    sent_sms: bool
    created_at: str | None = None  # ISO format

    class Config:
        from_attributes = True


def _anomaly_log_to_response(log) -> AnomalyLogResponse:
    """Convert AnomalyLog ORM object to AnomalyLogResponse."""
    return AnomalyLogResponse(
        id=log.id,
        record_id=log.record_id,
        layer=log.layer,
        z_score=float(log.z_score) if log.z_score is not None else None,
        metric_value=float(log.metric_value),
        threshold=float(log.threshold),
        llm_report=log.llm_report,
        sent_sms=log.sent_sms,
        created_at=log.created_at.isoformat() if log.created_at else None,
    )


@anomaly_router.get("/history", response_model=PaginatedResponse[AnomalyLogResponse])
async def get_anomaly_history(
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    limit: int | None = Query(None, description="Deprecado: usar page_size"),
):
    # Backward compatibility: limit deprecated, use page_size instead
    if limit is not None and page_size == 20:
        page_size = min(max(limit, 1), 100)
    from src.models import AnomalyLog as AL
    query = db.query(AL).order_by(AL.created_at.desc())
    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size
    logs = query.offset(offset).limit(page_size).all()
    items = [_anomaly_log_to_response(log) for log in logs]
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


app.include_router(anomaly_router)

# ------------------------------------------------------------------
# Static files mount ΓÇö serve SPA from src/static/
# ------------------------------------------------------------------
_static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Serve SPA index.html at root, fallback to JSON if not built."""
    index_path = os.path.join(_static_dir, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
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
    response = asdict(config)
    # Include session and scale timeouts
    if hasattr(app.state, "session") and app.state.session:
        response["session_timeout_minutes"] = app.state.session.session_timeout_minutes
    if hasattr(app.state, "scale_config") and app.state.scale_config:
        response["scale_timeout_seconds"] = app.state.scale_config.timeout_seconds
    return JSONResponse(content=response)


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
                ["mmcli", "-m", str(_find_quectel_modem())],
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


# ------------------------------------------------------------------
# Catch-all route ΓÇö serve SPA index.html for non-API/WS/login/health
# MUST be registered AFTER all other routes.
# ------------------------------------------------------------------
@app.api_route("/{full_path:path}", methods=["GET"])
async def serve_spa(full_path: str):
    """Serve the SPA for any route not matching API/WS/login/health."""
    if full_path.startswith(("api/", "ws/", "login", "health")):
        return JSONResponse({"detail": "Not found"}, status_code=404)
    index_path = os.path.join(_static_dir, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return JSONResponse(
        {"detail": "SPA index.html not found. Run frontend build."},
        status_code=503,
    )
