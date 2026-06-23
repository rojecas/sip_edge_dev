"""User management CRUD endpoints and schemas."""

from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.auth import check_inactivity, hash_password, require_role
from src.database import get_db
from src.models import User


class UserCreate(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    full_name: str = Field(min_length=1)
    document: str = ""
    role: Literal["admin", "operator", "corresponsal"]


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    document: Optional[str] = None
    role: Optional[Literal["admin", "operator", "corresponsal"]] = None
    is_active: Optional[bool] = None
    new_password: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    document: str
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
        document=user.document,
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
        raise HTTPException(status_code=409, detail="Ya existe un usuario con este nombre. Elija otro nombre para poder guardarlo.")
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        document=data.document,
        role=data.role,
        is_active=True,
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
    if data.document is not None:
        update_fields["document"] = data.document
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


@router.get("", response_model=List[UserResponse])
def get_users(
    _admin: dict = Depends(check_inactivity),
    __admin: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return list_users(db)


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
