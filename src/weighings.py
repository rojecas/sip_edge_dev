"""Weighings CRUD endpoints and schemas."""

import logging
from datetime import date, datetime, time
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.auth import check_inactivity, require_any_role
from src.database import get_db
from src.models import Hacienda, Suerte, Weighing

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/weighings")


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
    }


def _send_rs232_frame(frame_data: dict, record: Weighing) -> None:
    try:
        from src.rs232 import send_frame
        send_frame(frame_data, format="json")
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
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    frame_data = _build_frame_data(record, hacienda, suerte)
    _send_rs232_frame(frame_data, record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=List[WeighingResponse])
def list_weighings(
    current_user: dict = Depends(check_inactivity),
    _: dict = Depends(require_any_role("admin", "operator")),
    db: Session = Depends(get_db),
):
    if current_user["role"] == "admin":
        return db.query(Weighing).all()
    return db.query(Weighing).filter(
        Weighing.usuario_id == current_user["user_id"]
    ).all()


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
