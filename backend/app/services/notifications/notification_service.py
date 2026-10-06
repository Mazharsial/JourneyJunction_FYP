"""
Notification orchestration.

notify() builds a message for an event and dispatches it over the user's opted-in
channels (email via the provider abstraction, WhatsApp via the Cloud API),
recording each attempt. It is best-effort: a messaging failure never breaks the
originating request.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.notification import Notification
from app.models.user import User
from app.services.notifications import email_provider, whatsapp_client

logger = get_logger("notify")


def _render(event: str, ctx: dict) -> str:
    brand = "VoynixAI"
    if event == "welcome":
        return f"Welcome to {brand}! Start planning smarter trips and verify your travel documents with AI."
    if event == "trip_created":
        return (f"Your trip to {ctx.get('destination')} "
                f"({ctx.get('start_date')} to {ctx.get('end_date')}) is planned on {brand}.")
    if event == "document_verified":
        return f"Your {ctx.get('doc_type', 'document')} was analyzed by {brand}: {ctx.get('summary', 'done')}."
    if event == "subscription_updated":
        return f"Your {brand} subscription is now on the {ctx.get('plan', 'Free')} plan."
    return ctx.get("message", f"{brand} notification.")


async def notify(session: AsyncSession, user: User, event: str, context: dict | None = None) -> list[dict]:
    context = context or {}
    body = _render(event, context)
    results: list[dict] = []

    # ---- Email (Klaviyo event, or mock) ----
    if user.email_opt_in and user.email:
        try:
            provider = email_provider.get_provider()
            await provider.upsert_contact(user.email, {"full_name": user.full_name})
            res = await provider.track_event(user.email, event, {**context, "body": body})
        except Exception as exc:  # noqa: BLE001
            res = {"status": "failed", "provider": "email", "error": str(exc)[:300]}
        session.add(Notification(
            user_id=user.id, channel="email", event=event, recipient=user.email, body=body,
            provider=res.get("provider", "email"), status=res.get("status", "failed"),
            error=res.get("error", ""), meta=context,
        ))
        results.append({"channel": "email", **res})

    # ---- WhatsApp ----
    if user.whatsapp_opt_in and user.phone_number:
        res = await whatsapp_client.send_text(user.phone_number, body)
        session.add(Notification(
            user_id=user.id, channel="whatsapp", event=event, recipient=user.phone_number, body=body,
            provider=res.get("provider", "whatsapp"), status=res.get("status", "failed"),
            error=res.get("error", ""), meta=context,
        ))
        results.append({"channel": "whatsapp", **res})

    await session.flush()
    return results


async def send_test(session: AsyncSession, user: User, channel: str, message: str) -> dict:
    """Admin/debug helper: send a one-off message on a single channel."""
    if channel == "whatsapp":
        res = await whatsapp_client.send_text(user.phone_number, message)
        recipient = user.phone_number
    else:
        provider = email_provider.get_provider()
        res = await provider.track_event(user.email, "test_message", {"body": message})
        recipient = user.email
    session.add(Notification(
        user_id=user.id, channel=channel, event="test", recipient=recipient, body=message,
        provider=res.get("provider", channel), status=res.get("status", "failed"),
        error=res.get("error", ""),
    ))
    await session.flush()
    return res
