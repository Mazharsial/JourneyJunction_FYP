"""Notification history, preferences, test-send, and the WhatsApp webhook."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import (
    NotificationOut,
    PreferencesOut,
    PreferencesUpdate,
    TestSendRequest,
)
from app.services.notifications import email_provider, notification_service, whatsapp_client

logger = get_logger("notifications")
router = APIRouter()


def _prefs_out(user: User) -> PreferencesOut:
    return PreferencesOut(
        full_name=user.full_name, phone_number=user.phone_number,
        whatsapp_opt_in=user.whatsapp_opt_in, email_opt_in=user.email_opt_in,
        whatsapp_enabled=whatsapp_client.is_configured(),
        email_enabled=email_provider.is_configured(),
    )


@router.get("", response_model=list[NotificationOut])
async def list_notifications(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (await db.scalars(
        select(Notification).where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc()).limit(50)
    )).all()
    return list(rows)


@router.get("/preferences", response_model=PreferencesOut)
async def get_preferences(user: User = Depends(get_current_user)):
    return _prefs_out(user)


@router.patch("/preferences", response_model=PreferencesOut)
async def update_preferences(
    payload: PreferencesUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.phone_number is not None:
        user.phone_number = payload.phone_number.strip()
    if payload.whatsapp_opt_in is not None:
        user.whatsapp_opt_in = payload.whatsapp_opt_in
    if payload.email_opt_in is not None:
        user.email_opt_in = payload.email_opt_in
    await db.flush()
    return _prefs_out(user)


@router.post("/test")
async def test_send(
    payload: TestSendRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if payload.channel == "whatsapp" and not user.phone_number:
        from app.core.exceptions import AppError
        raise AppError("Add a phone number in your preferences first.", code="no_phone", status_code=400)
    return await notification_service.send_test(db, user, payload.channel, payload.message)


# ---- WhatsApp inbound webhook (ready for when a public URL/tunnel is set up) ----
@router.get("/whatsapp/webhook")
async def whatsapp_verify(request: Request):
    settings = get_settings()
    params = request.query_params
    if (params.get("hub.mode") == "subscribe"
            and params.get("hub.verify_token") == settings.whatsapp_verify_token
            and settings.whatsapp_verify_token):
        return PlainTextResponse(params.get("hub.challenge", ""))
    return Response(status_code=status.HTTP_403_FORBIDDEN)


@router.post("/whatsapp/webhook")
async def whatsapp_receive(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    # Record inbound text messages (best-effort). Signature verification with the
    # app secret can be added when the public endpoint is configured.
    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                for msg in (change.get("value", {}).get("messages", []) or []):
                    body = (msg.get("text") or {}).get("body", "")
                    db.add(Notification(
                        channel="whatsapp", event="inbound", recipient=msg.get("from", ""),
                        body=body, provider="whatsapp", status="received",
                    ))
        await db.flush()
    except Exception as exc:  # noqa: BLE001
        logger.warning("whatsapp_inbound_parse_failed", error=str(exc))
    return {"received": True}
