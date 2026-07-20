"""Haciendas and Suertes CRUD endpoints and schemas."""

import math
from datetime import datetime
from typing import Any, Generic, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from src.auth import check_inactivity, require_any_role, require_role
from src.database import get_db
from src.models import Hacienda, Suerte
from src.schemas import PaginatedResponse


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
    created_by: Optional[int] = None
    created_by_username: Optional[str] = None

    class Config:
        from_attributes = True


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
    created_by: Optional[int] = None
    created_by_username: Optional[str] = None

    class Config:
        from_attributes = True


def _hacienda_to_response(h: Hacienda) -> HaciendaResponse:
    return HaciendaResponse(
        id=h.id,
        codigo=h.codigo,
        nombre=h.nombre,
        created_at=h.created_at,
        updated_at=h.updated_at,
        created_by=h.created_by,
        created_by_username=h.creator.username if h.creator else None,
    )


def _suerte_to_response(s: Suerte) -> SuerteResponse:
    return SuerteResponse(
        id=s.id,
        hacienda_id=s.hacienda_id,
        codigo_suerte=s.codigo_suerte,
        created_at=s.created_at,
        updated_at=s.updated_at,
        created_by=s.created_by,
        created_by_username=s.creator.username if s.creator else None,
    )


# ---- Haciendas CRUD ----

def list_haciendas(db: Session) -> List[HaciendaResponse]:
    haciendas = db.query(Hacienda).filter(Hacienda.deleted_at.is_(None)).all()
    return [_hacienda_to_response(h) for h in haciendas]


def get_hacienda(db: Session, hacienda_id: int) -> HaciendaResponse:
    h = db.query(Hacienda).filter(
        Hacienda.id == hacienda_id, Hacienda.deleted_at.is_(None)
    ).first()
    if h is None:
        raise HTTPException(status_code=404, detail="Hacienda not found")
    return _hacienda_to_response(h)


def create_hacienda(db: Session, data: HaciendaCreate, user_id: int) -> HaciendaResponse:
    existing = db.query(Hacienda).filter(
        Hacienda.codigo == data.codigo, Hacienda.deleted_at.is_(None)
    ).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Ya existe una hacienda con este codigo. Cambielo para poder guardarla.")
    h = Hacienda(codigo=data.codigo, nombre=data.nombre, created_by=user_id)
    db.add(h)
    db.commit()
    db.refresh(h)
    return _hacienda_to_response(h)


def update_hacienda(db: Session, hacienda_id: int, data: HaciendaUpdate) -> HaciendaResponse:
    h = db.query(Hacienda).filter(
        Hacienda.id == hacienda_id, Hacienda.deleted_at.is_(None)
    ).first()
    if h is None:
        raise HTTPException(status_code=404, detail="Hacienda not found")
    update_fields = {}
    if data.codigo is not None:
        # check uniqueness if codigo changed
        conflict = db.query(Hacienda).filter(
            Hacienda.codigo == data.codigo,
            Hacienda.id != hacienda_id,
            Hacienda.deleted_at.is_(None),
        ).first()
        if conflict is not None:
            raise HTTPException(status_code=409, detail="Ya existe una hacienda con este codigo. Cambielo para poder guardarla.")
        update_fields["codigo"] = data.codigo
    if data.nombre is not None:
        update_fields["nombre"] = data.nombre
    if update_fields:
        for key, value in update_fields.items():
            setattr(h, key, value)
        db.commit()
        db.refresh(h)
    return _hacienda_to_response(h)


def soft_delete_hacienda(db: Session, hacienda_id: int) -> HaciendaResponse:
    h = db.query(Hacienda).filter(
        Hacienda.id == hacienda_id, Hacienda.deleted_at.is_(None)
    ).first()
    if h is None:
        raise HTTPException(status_code=404, detail="Hacienda not found")
    h.deleted_at = datetime.utcnow()
    db.commit()
    db.refresh(h)
    return _hacienda_to_response(h)


# ---- Suertes CRUD ----

def list_suertes(db: Session, hacienda_id: Optional[int] = None) -> List[SuerteResponse]:
    q = db.query(Suerte).filter(Suerte.deleted_at.is_(None))
    if hacienda_id is not None:
        q = q.filter(Suerte.hacienda_id == hacienda_id)
    suertes = q.all()
    return [_suerte_to_response(s) for s in suertes]


def get_suerte(db: Session, suerte_id: int) -> SuerteResponse:
    s = db.query(Suerte).filter(
        Suerte.id == suerte_id, Suerte.deleted_at.is_(None)
    ).first()
    if s is None:
        raise HTTPException(status_code=404, detail="Suerte not found")
    return _suerte_to_response(s)


def create_suerte(db: Session, data: SuerteCreate, user_id: int) -> SuerteResponse:
    # verify hacienda exists and is active
    hacienda = db.query(Hacienda).filter(
        Hacienda.id == data.hacienda_id, Hacienda.deleted_at.is_(None)
    ).first()
    if hacienda is None:
        raise HTTPException(status_code=404, detail="Hacienda not found")
    # check unique constraint (hacienda_id, codigo_suerte)
    existing = db.query(Suerte).filter(
        Suerte.hacienda_id == data.hacienda_id,
        Suerte.codigo_suerte == data.codigo_suerte,
        Suerte.deleted_at.is_(None),
    ).first()
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Ya existe una suerte con este codigo en esta hacienda. Cambielo para poder guardarla.",
        )
    s = Suerte(hacienda_id=data.hacienda_id, codigo_suerte=data.codigo_suerte, created_by=user_id)
    db.add(s)
    db.commit()
    db.refresh(s)
    return _suerte_to_response(s)


def update_suerte(db: Session, suerte_id: int, data: SuerteUpdate) -> SuerteResponse:
    s = db.query(Suerte).filter(
        Suerte.id == suerte_id, Suerte.deleted_at.is_(None)
    ).first()
    if s is None:
        raise HTTPException(status_code=404, detail="Suerte not found")
    update_fields = {}
    if data.codigo_suerte is not None:
        # check uniqueness if codigo_suerte changed
        conflict = db.query(Suerte).filter(
            Suerte.hacienda_id == s.hacienda_id,
            Suerte.codigo_suerte == data.codigo_suerte,
            Suerte.id != suerte_id,
            Suerte.deleted_at.is_(None),
        ).first()
        if conflict is not None:
            raise HTTPException(
                status_code=409,
                detail="Ya existe una suerte con este codigo en esta hacienda. Cambielo para poder guardarla.",
            )
        update_fields["codigo_suerte"] = data.codigo_suerte
    if update_fields:
        for key, value in update_fields.items():
            setattr(s, key, value)
        db.commit()
        db.refresh(s)
    return _suerte_to_response(s)


def soft_delete_suerte(db: Session, suerte_id: int) -> SuerteResponse:
    s = db.query(Suerte).filter(
        Suerte.id == suerte_id, Suerte.deleted_at.is_(None)
    ).first()
    if s is None:
        raise HTTPException(status_code=404, detail="Suerte not found")
    s.deleted_at = datetime.utcnow()
    db.commit()
    db.refresh(s)
    return _suerte_to_response(s)


# ---- Routers ----

haciendas_router = APIRouter(prefix="/api/haciendas")
suertes_router = APIRouter(prefix="/api/suertes")


@haciendas_router.get("", response_model=PaginatedResponse[HaciendaResponse])
def get_haciendas(
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_any_role("admin", "operator")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    sort_by: str = Query("nombre", description="Column to sort by"),
    sort_order: str = Query("asc", description="asc or desc"),
):
    query = db.query(Hacienda).filter(Hacienda.deleted_at.is_(None))

    # Sort
    sort_columns: dict[str, Any] = {
        "nombre": Hacienda.nombre,
        "codigo": Hacienda.codigo,
        "created_at": Hacienda.created_at,
        "id": Hacienda.id,
    }
    sort_col = sort_columns.get(sort_by, Hacienda.nombre)
    if sort_order == "asc":
        query = query.order_by(asc(sort_col))
    else:
        query = query.order_by(desc(sort_col))

    # Pagination
    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size
    records = query.offset(offset).limit(page_size).all()

    items = [_hacienda_to_response(h) for h in records]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@haciendas_router.post("", response_model=HaciendaResponse, status_code=201)
def create_new_hacienda(
    body: HaciendaCreate,
    current_user: dict = Depends(check_inactivity),
    __: dict = Depends(require_any_role("admin", "operator")),
    db: Session = Depends(get_db),
):
    return create_hacienda(db, body, current_user["user_id"])


@haciendas_router.get("/{hacienda_id}", response_model=HaciendaResponse)
def get_hacienda_by_id(
    hacienda_id: int,
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_any_role("admin", "operator")),
    db: Session = Depends(get_db),
):
    return get_hacienda(db, hacienda_id)


@haciendas_router.put("/{hacienda_id}", response_model=HaciendaResponse)
def update_existing_hacienda(
    hacienda_id: int,
    body: HaciendaUpdate,
    _admin: dict = Depends(check_inactivity),
    __operator: dict = Depends(require_any_role("admin", "operator")),
    db: Session = Depends(get_db),
):
    return update_hacienda(db, hacienda_id, body)


@haciendas_router.delete("/{hacienda_id}", response_model=HaciendaResponse)
def delete_hacienda(
    hacienda_id: int,
    _admin: dict = Depends(check_inactivity),
    __admin: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return soft_delete_hacienda(db, hacienda_id)


@suertes_router.get("", response_model=List[SuerteResponse])
def get_suertes(
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_any_role("admin", "operator")),
    db: Session = Depends(get_db),
    hacienda_id: Optional[int] = Query(None),
):
    return list_suertes(db, hacienda_id)


@suertes_router.post("", response_model=SuerteResponse, status_code=201)
def create_new_suerte(
    body: SuerteCreate,
    current_user: dict = Depends(check_inactivity),
    __: dict = Depends(require_any_role("admin", "operator")),
    db: Session = Depends(get_db),
):
    return create_suerte(db, body, current_user["user_id"])


@suertes_router.get("/{suerte_id}", response_model=SuerteResponse)
def get_suerte_by_id(
    suerte_id: int,
    _: dict = Depends(check_inactivity),
    __: dict = Depends(require_any_role("admin", "operator")),
    db: Session = Depends(get_db),
):
    return get_suerte(db, suerte_id)


@suertes_router.put("/{suerte_id}", response_model=SuerteResponse)
def update_existing_suerte(
    suerte_id: int,
    body: SuerteUpdate,
    _admin: dict = Depends(check_inactivity),
    __operator: dict = Depends(require_any_role("admin", "operator")),
    db: Session = Depends(get_db),
):
    return update_suerte(db, suerte_id, body)


@suertes_router.delete("/{suerte_id}", response_model=SuerteResponse)
def delete_suerte(
    suerte_id: int,
    _admin: dict = Depends(check_inactivity),
    __admin: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return soft_delete_suerte(db, suerte_id)
