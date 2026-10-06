"""Health & readiness probes."""
from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text

from app import __version__
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import get_engine

router = APIRouter(tags=["health"])
logger = get_logger("health")


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    environment: str


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app=settings.brand_name,
        version=__version__,
        environment=settings.app_env,
    )


@router.get("/health/ready", summary="Readiness probe (checks dependencies)")
async def readiness() -> JSONResponse:
    """Verify critical dependencies (DB). Returns 503 if any are unavailable."""
    checks: dict[str, str] = {}
    healthy = True

    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # pragma: no cover - exercised only when DB is down
        healthy = False
        checks["database"] = "unavailable"
        logger.warning("readiness_db_check_failed", error=str(exc))

    return JSONResponse(
        status_code=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "ready" if healthy else "degraded", "checks": checks},
    )
