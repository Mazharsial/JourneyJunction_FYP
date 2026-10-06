"""
Celery application for async/background work (OCR, AI calls, webhooks, scheduled
usage resets). Tasks are registered per phase.
"""
from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "voynixai",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone=settings.default_timezone,
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(name="health.ping")
def ping() -> str:
    """Trivial task to verify the worker/broker wiring."""
    return "pong"
