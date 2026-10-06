"""
Test fixtures: a fresh in-memory SQLite database per test (isolated), with RBAC
seeded, the get_db dependency overridden, and an httpx AsyncClient over the ASGI
app. Production uses PostgreSQL; the portable GUID type keeps models compatible.
"""
from __future__ import annotations

import os
import tempfile

# Force-disable external services in tests BEFORE app modules load settings, so
# the suite runs fully offline (never hitting the real Gemini/Stripe keys).
os.environ["GEMINI_API_KEY"] = ""
os.environ["STRIPE_SECRET_KEY"] = ""
os.environ["STRIPE_WEBHOOK_SECRET"] = ""
os.environ["WHATSAPP_ACCESS_TOKEN"] = ""
os.environ["WHATSAPP_VERIFY_TOKEN"] = ""
os.environ["KLAVIYO_API_KEY"] = ""
# Isolate uploaded (encrypted) files to a temp dir; keep upload limit small.
os.environ["STORAGE_DIR"] = tempfile.mkdtemp(prefix="voynix_test_storage_")
os.environ["MAX_UPLOAD_MB"] = "2"

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.rate_limit import reset_rate_limits
from app.db.seed import seed_rbac
from app.db.seed_billing import seed_billing
from app.db.seed_locations import seed_locations
from app.db.session import get_db
from app.main import create_app
from app.models import Base


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sm = async_sessionmaker(engine, expire_on_commit=False)
    async with sm() as s:
        await seed_rbac(s)
        await seed_locations(s)
        await seed_billing(s)
        await s.commit()
    try:
        yield engine, sm
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(db_engine):
    _, sm = db_engine
    return sm


@pytest_asyncio.fixture
async def app_instance(db_engine):
    _, sm = db_engine

    async def override_get_db():
        async with sm() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    reset_rate_limits()
    return app


@pytest_asyncio.fixture
async def client(app_instance):
    transport = ASGITransport(app=app_instance)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
