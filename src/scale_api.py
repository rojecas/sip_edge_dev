"""API endpoint for scale commands (REXT, TARE, ZERO, CLEAR, TMAN)."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.scale import (
    ScaleConnectionError,
    ScaleProtocolError,
    ScaleService,
    ScaleTimeoutError,
)

router = APIRouter(prefix="/api/scale", tags=["scale"])


class ScaleCommandRequest(BaseModel):
    command: str  # REXT, TARE, ZERO, CLEAR, TMAN
    value: str | None = None


def get_scale_service(request: Request) -> ScaleService:
    """Dependency that resolves the ScaleService singleton from app state."""
    return request.app.state.scale_service


@router.post("/command")
async def scale_command(
    body: ScaleCommandRequest,
    scale: ScaleService = Depends(get_scale_service),
):
    """Send a command to the scale and return the result."""
    try:
        result = scale.send_command(body.command, body.value)
        return result
    except ScaleProtocolError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ScaleConnectionError, ScaleTimeoutError) as e:
        raise HTTPException(status_code=503, detail=str(e))
