"""JWT authentication, password hashing, and FastAPI auth dependencies."""

import os
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from src.config import DEFAULT_SESSION_TIMEOUT_MINUTES

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])

JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class SessionTimeoutRequest(BaseModel):
    session_timeout_minutes: int = Field(gt=0)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int, role: str, session_timeout_minutes: int = 30) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": int(time.time()),
        "session_timeout_minutes": session_timeout_minutes,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)


def create_reset_token(user_id: int) -> str:
    """Crea un JWT con expiracion de 5 minutos para reset de contrasena."""
    import datetime as _dt
    payload = {
        "sub": str(user_id),
        "purpose": "password_reset",
        "iat": int(time.time()),
        "exp": int(time.time()) + 300,  # 5 minutes
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)


def decode_reset_token(token: str) -> dict:
    """Decodifica y valida un reset_token JWT.

    Raises:
        JWTError: Si el token es invalido o ha expirado.
    """
    payload = jwt.decode(
        token, JWT_SECRET_KEY, algorithms=[ALGORITHM],
        options={"require_exp": True},
    )
    if payload.get("purpose") != "password_reset":
        raise JWTError("Invalid token purpose")
    return payload


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
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
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] != required_role:
            raise HTTPException(
                status_code=403, detail="Insufficient permissions"
            )
        return current_user

    return role_checker


def require_any_role(*roles: str):
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in roles:
            raise HTTPException(
                status_code=403, detail="Insufficient permissions"
            )
        return current_user

    return role_checker


def check_inactivity(
    current_user: dict = Depends(get_current_user),
    request: Request = None,
) -> dict:
    session_config = getattr(request.app.state, "session", None)
    timeout = DEFAULT_SESSION_TIMEOUT_MINUTES
    if session_config is not None:
        timeout = session_config.session_timeout_minutes
    now = time.time()
    last = getattr(request.app.state, "last_activity", current_user["iat"])
    elapsed_minutes = (now - last) / 60.0
    if elapsed_minutes > timeout:
        raise HTTPException(
            status_code=401, detail="Session expired due to inactivity"
        )
    return current_user


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


@auth_router.post("/refresh")
async def refresh_token(
    current_user: dict = Depends(get_current_user),
    request: Request = None,
) -> RefreshResponse:
    """Emitir un nuevo JWT con iat fresco para refresh de sesion."""
    session_config = getattr(request.app.state, "session", None)
    timeout = DEFAULT_SESSION_TIMEOUT_MINUTES
    if session_config is not None:
        timeout = session_config.session_timeout_minutes
    new_token = create_access_token(
        current_user["user_id"],
        current_user["role"],
        session_timeout_minutes=timeout,
    )
    return RefreshResponse(
        access_token=new_token,
        token_type="bearer",
        role=current_user["role"],
    )


# ---- Session status check ----
class SessionStatusResponse(BaseModel):
    valid: bool

@auth_router.get("/status", response_model=SessionStatusResponse)
async def check_session_status(
    current_user: dict = Depends(get_current_user),
    request: Request = None,
):
    timeout = DEFAULT_SESSION_TIMEOUT_MINUTES
    session_config = getattr(request.app.state, "session", None)
    if session_config is not None:
        timeout = session_config.session_timeout_minutes
    last = getattr(request.app.state, "last_activity", time.time())
    elapsed = (time.time() - last) / 60.0
    return SessionStatusResponse(valid=elapsed <= timeout)
