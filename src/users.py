"""User management CRUD endpoints and schemas."""

import math
from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.auth import check_inactivity, hash_password, require_role
from src.database import get_db
from src.models import User
from src.schemas import PaginatedResponse

HIDDEN_USER_IDS = {1, 2}


class UserCreate(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    full_name: str = Field(min_length=1)
    employee_code: str = Field(min_length=1)
    phone: str = Field(min_length=1)
    role: Literal["admin", "operator", "corresponsal"]


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    employee_code: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[Literal["admin", "operator", "corresponsal"]] = None
    is_active: Optional[bool] = None
    new_password: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    employee_code: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    force_password_change: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {"exclude": {"reset_pin", "reset_pin_expires_at"}}


def _user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        employee_code=user.employee_code,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        force_password_change=bool(user.force_password_change),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def list_users(db: Session) -> List[UserResponse]:
    users = db.query(User).all()
    return [_user_to_response(u) for u in users]


def get_user(db: Session, user_id: int) -> UserResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_response(user)


def create_user(db: Session, data: UserCreate) -> UserResponse:
    existing = db.query(User).filter(User.username == data.username).first()
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Ya existe un usuario con este nombre. Elija otro nombre para poder guardarlo.",
        )
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        employee_code=data.employee_code,
        role=data.role,
        is_active=True,
        phone=data.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _user_to_response(user)


def update_user(db: Session, user_id: int, data: UserUpdate) -> UserResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    update_fields = {}
    if data.full_name is not None:
        update_fields["full_name"] = data.full_name
    if data.employee_code is not None:
        update_fields["employee_code"] = data.employee_code
    if data.phone is not None:
        update_fields["phone"] = data.phone
    if data.role is not None:
        update_fields["role"] = data.role
    if data.is_active is not None:
        update_fields["is_active"] = data.is_active
    if data.new_password is not None:
        update_fields["password_hash"] = hash_password(data.new_password)
    if update_fields:
        for key, value in update_fields.items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return _user_to_response(user)


def deactivate_user(db: Session, user_id: int) -> UserResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return _user_to_response(user)


router = APIRouter(prefix="/api/users")


@router.get("", response_model=PaginatedResponse[UserResponse])
def get_users(
    _admin: dict = Depends(check_inactivity),
    __admin: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    query = db.query(User).filter(User.id.notin_(HIDDEN_USER_IDS))
    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size
    records = query.offset(offset).limit(page_size).all()
    items = [_user_to_response(u) for u in records]
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    _admin: dict = Depends(check_inactivity),
    __admin: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return get_user(db, user_id)


@router.post("", response_model=UserResponse, status_code=201)
def create_new_user(
    body: UserCreate,
    _admin: dict = Depends(check_inactivity),
    __admin: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return create_user(db, body)


@router.put("/{user_id}", response_model=UserResponse)
def update_existing_user(
    user_id: int,
    body: UserUpdate,
    _admin: dict = Depends(check_inactivity),
    __admin: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return update_user(db, user_id, body)


@router.delete("/{user_id}", response_model=UserResponse)
def deactivate_existing_user(
    user_id: int,
    _admin: dict = Depends(check_inactivity),
    __admin: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return deactivate_user(db, user_id)
