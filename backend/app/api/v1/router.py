"""Aggregates all v1 API routers. New feature routers are registered here."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import (
    admin,
    auth,
    billing,
    chat,
    documents,
    health,
    locations,
    travel,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(travel.router)
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
