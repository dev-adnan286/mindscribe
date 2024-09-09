from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app import __version__
from app.core.config import get_settings
from app.core.deps import DbSession

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str
    ai_provider: str


@router.get("", response_model=HealthResponse, summary="Liveness + dependency check")
async def health(db: DbSession) -> HealthResponse:
    settings = get_settings()
    try:
        await db.execute(text("SELECT 1"))
        database = "ok"
    except Exception:  # pragma: no cover - only when DB is down
        database = "unavailable"
    return HealthResponse(
        status="ok" if database == "ok" else "degraded",
        version=__version__,
        environment=settings.environment,
        database=database,
        ai_provider=settings.ai_provider,
    )
