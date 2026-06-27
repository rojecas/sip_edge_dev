"""Weighings CRUD endpoints and schemas."""

import logging
import math
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Generic, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from src.auth import check_inactivity, require_any_role
from src.database import get_db
from src.models import Hacienda, Suerte, Weighing
from src.schemas import PaginatedResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/weighings")

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
    manual_entry: bool
    tipo_cosecha: str

    class Config:
        from_attributes = True


class ResetResponse(BaseModel):
    mensaje: str = "Formulario reiniciado"


def _build_frame_data(record: Weighing, hacienda: Hacienda, suerte: Suerte) -> dict:
    return {
        "fecha": record.fecha.isoformat(),
        "hora": record.hora.isoformat(),
        "tractomula": record.tractomula,
        "vagon": record.vagon,
        "numero_guia": record.numero_guia,
        "hacienda": {"id": hacienda.id, "codigo": hacienda.codigo, "nombre": hacienda.nombre},
        "suerte": {"id": suerte.id, "codigo_suerte": suerte.codigo_suerte},
        "pesos": {
            "muestra": float(record.peso_muestra),
            "mineral": float(record.peso_mineral),
            "vegetal_extrano": float(record.peso_vegetal_extrano),
        },
        "tipo_cosecha": record.tipo_cosecha,
    }


def _send_rs232_frame(frame_data: dict, record: Weighing) -> None:
    try:
        from src.rs232 import send_frame
        frame_data["id"] = record.id
        send_frame(frame_data, format="csv")
        record.enviado_pc = True
    except ImportError:
        pass
    except Exception as e:
        logger.error("RS232 send failed: %s", e)


@router.post("", response_model=WeighingResponse, status_code=201)
def create_weighing(
    body: WeighingCreate,
    current_user: dict = Depends(check_inactivity),
    _: dict = Depends(require_any_role("admin", "operator")),
    db: Session = Depends(get_db),
):
    hacienda = db.query(Hacienda).filter(
        Hacienda.id == body.hacienda_id, Hacienda.deleted_at.is_(None)
    ).first()
    if hacienda is None:
        raise HTTPException(status_code=404, detail="Hacienda not found")
    suerte = db.query(Suerte).filter(
        Suerte.id == body.suerte_id,
        Suerte.hacienda_id == body.hacienda_id,
        Suerte.deleted_at.is_(None),
    ).first()
    if suerte is None:
        raise HTTPException(status_code=404, detail="Suerte not found")
    now = datetime.now()
    record = Weighing(
        fecha=now.date(),
        hora=now.time(),
        tractomula=body.tractomula,
        vagon=body.vagon,
        numero_guia=body.numero_guia,
        hacienda_id=body.hacienda_id,
        suerte_id=body.suerte_id,
        peso_muestra=body.peso_muestra,
        peso_mineral=body.peso_mineral,
        peso_vegetal_extrano=body.peso_vegetal_extrano,
        usuario_id=current_user["user_id"],
        manual_entry=body.manual_entry,
        tipo_cosecha=body.tipo_cosecha,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    frame_data = _build_frame_data(record, hacienda, suerte)
    _send_rs232_frame(frame_data, record)
    db.commit()
    db.refresh(record)

    # Hook: Deteccion de anomalias tras pesaje exitoso (T24)
    _run_anomaly_detection(record)

    return record


def _run_anomaly_detection(record: Weighing) -> None:
    """Ejecuta deteccion de anomalias post-pesaje.

    Si se detectan anomalias, invoca al AgentOrchestrator para generar
    reporte narrativo y enviar SMS.
    """
    import asyncio

    from fastapi import FastAPI as _F

    try:
        # Acceder al app state via la dependencia de FastAPI
        import src.main as main_mod
        app = main_mod.app
        if not hasattr(app.state, "anomaly_detector") or app.state.anomaly_detector is None:
            logger.debug("AnomalyDetector no inicializado, omitiendo deteccion")
            return
        if not hasattr(app.state, "agent_orchestrator") or app.state.agent_orchestrator is None:
            logger.debug("AgentOrchestrator no inicializado, omitiendo deteccion")
            return

        detector = app.state.anomaly_detector
        orchestrator = app.state.agent_orchestrator

        anomalies = detector.run(record)
        if not anomalies:
            logger.debug("No se detectaron anomalias para el pesaje %d", record.id)
            return

        logger.info("Detectadas %d anomalias para el pesaje %d", len(anomalies), record.id)

        # Construir contexto estadistico para el LLM
        context = {
            "record_id": record.id,
            "fecha": record.fecha.isoformat(),
            "hora": record.hora.isoformat(),
            "peso_muestra": float(record.peso_muestra),
            "peso_mineral": float(record.peso_mineral),
            "peso_vegetal": float(record.peso_vegetal_extrano),
            "peso_total": float(record.peso_muestra + record.peso_mineral + record.peso_vegetal_extrano),
            "total_anomalies": len(anomalies),
        }

        orchestrator.handle_anomaly(anomalies, context)

    except Exception:
        logger.exception("Error en deteccion de anomalias post-pesaje")


@router.get("", response_model=PaginatedResponse[WeighingResponse])
def list_weighings(
    current_user: dict = Depends(check_inactivity),
    _: dict = Depends(require_any_role("admin", "operator")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    sort_by: str = Query("fecha", description="Column to sort by"),
    sort_order: str = Query("desc", description="asc or desc"),
):
    # Base query with role filtering
    query = db.query(Weighing)
    if current_user["role"] == "operator":
        query = query.filter(Weighing.usuario_id == current_user["user_id"])

    # Date range filter
    if start_date:
        try:
            sd = date.fromisoformat(start_date)
            query = query.filter(Weighing.fecha >= sd)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format (use YYYY-MM-DD)")

    if end_date:
        try:
            ed = date.fromisoformat(end_date)
            query = query.filter(Weighing.fecha <= ed)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format (use YYYY-MM-DD)")

    # Sort
    sort_columns: dict[str, Any] = {
        "fecha": Weighing.fecha,
        "hora": Weighing.hora,
        "created_at": Weighing.created_at,
        "id": Weighing.id,
    }
    sort_col = sort_columns.get(sort_by, Weighing.fecha)
    if sort_order == "asc":
        query = query.order_by(asc(sort_col))
    else:
        query = query.order_by(desc(sort_col))

    # Pagination
    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size
    records = query.offset(offset).limit(page_size).all()

    # Build response items
    items: list[WeighingResponse] = []
    for w in records:
        items.append(WeighingResponse(
            id=w.id,
            fecha=w.fecha,
            hora=w.hora,
            tractomula=w.tractomula,
            vagon=w.vagon,
            numero_guia=w.numero_guia,
            hacienda_id=w.hacienda_id,
            suerte_id=w.suerte_id,
            peso_muestra=w.peso_muestra,
            peso_mineral=w.peso_mineral,
            peso_vegetal_extrano=w.peso_vegetal_extrano,
            usuario_id=w.usuario_id,
            created_at=w.created_at,
            enviado_pc=w.enviado_pc,
            manual_entry=w.manual_entry,
            tipo_cosecha=w.tipo_cosecha,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


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


@router.post("/reset", response_model=ResetResponse)
def reset_weighing_form(
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_any_role("admin", "operator")),
):
    return ResetResponse()
