"""Health check — public, no DB."""

from datetime import UTC, datetime

from fastapi import APIRouter

from app.schemas.common import APIModel

router = APIRouter(tags=["health"])


class HealthResponse(APIModel):
    ok: bool
    service: str
    time: datetime


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health() -> HealthResponse:
    """Public 端点,不连 DB。docker compose healthcheck 用。"""
    return HealthResponse(
        ok=True,
        service="dingwei-crm-backend",
        time=datetime.now(UTC),
    )
