"""
Journey Junction API — application factory.

Boots cleanly without external services; dependency health is reported via
`/api/v1/health/ready` rather than failing startup.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import CorrelationIdMiddleware, SecurityHeadersMiddleware

configure_logging()
logger = get_logger("startup")


_WEAK_SECRETS = {"change-me-dev-only", "change-me-dev-only-not-a-real-secret", ""}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    # Production guard: refuse to boot with a weak/default signing key.
    if settings.is_production and (
        settings.secret_key in _WEAK_SECRETS or len(settings.secret_key) < 32
    ):
        raise RuntimeError(
            "SECRET_KEY is weak/default — set a strong SECRET_KEY before running in production."
        )
    logger.info(
        "application_start",
        brand=settings.brand_name,
        env=settings.app_env,
        version=__version__,
    )
    yield
    logger.info("application_stop")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=f"{settings.brand_name} API",
        version=__version__,
        description="AI-powered smart travel planning & document verification platform.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Middleware (executed bottom-up; correlation id outermost).
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    # CORS — import locally to keep the factory lightweight.
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/", tags=["root"], summary="Service banner")
    async def root() -> dict:
        return {
            "service": f"{settings.brand_name} API",
            "version": __version__,
            "docs": "/docs",
            "health": f"{settings.api_v1_prefix}/health",
        }

    return app


app = create_app()
