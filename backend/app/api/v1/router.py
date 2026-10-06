"""Aggregates all v1 API routers. New feature routers are registered here."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import auth, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Future phases register here:
#   api_router.include_router(trips.router, prefix="/trips", tags=["travel"])
#   api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
#   ...
