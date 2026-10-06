"""
WhatsApp Cloud API client (Meta Graph API).

send_text() posts a message via the configured phone number. When no access
token is set it returns a 'mock' result so the app works without credentials.
Never exposes the token to clients.
"""
from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("whatsapp")


def is_configured() -> bool:
    s = get_settings()
    return bool(s.whatsapp_access_token and s.whatsapp_phone_number_id)


def _normalize(number: str) -> str:
    # Meta expects digits only, with country code, no '+' or spaces.
    return "".join(ch for ch in (number or "") if ch.isdigit())


def _endpoint() -> str:
    s = get_settings()
    return f"https://graph.facebook.com/{s.whatsapp_api_version}/{s.whatsapp_phone_number_id}/messages"


# WhatsApp error codes meaning "outside the 24h customer-service window — a
# template is required for a business-initiated message".
_REENGAGEMENT_CODES = {131047, 131051, 131026, 470}
# Pre-approved template available on every WhatsApp test number. Custom
# templates (carrying the real notification text) must be created and approved
# in Meta Business Manager; once approved, swap this out per event.
_FALLBACK_TEMPLATE = "hello_world"
_FALLBACK_LANG = "en_US"


async def _post(payload: dict) -> httpx.Response:
    s = get_settings()
    async with httpx.AsyncClient(timeout=20) as client:
        return await client.post(
            _endpoint(), json=payload,
            headers={"Authorization": f"Bearer {s.whatsapp_access_token}"},
        )


async def send_template(to: str, name: str = _FALLBACK_TEMPLATE,
                        lang: str = _FALLBACK_LANG, components: list | None = None) -> dict:
    """Send an approved template message (works for business-initiated sends)."""
    to = _normalize(to)
    if not to:
        return {"status": "skipped", "provider": "whatsapp", "error": "no recipient number"}
    if not is_configured():
        return {"status": "mock", "provider": "whatsapp"}
    template: dict = {"name": name, "language": {"code": lang}}
    if components:
        template["components"] = components
    payload = {"messaging_product": "whatsapp", "to": to, "type": "template", "template": template}
    try:
        resp = await _post(payload)
        resp.raise_for_status()
        msg_id = (resp.json().get("messages") or [{}])[0].get("id", "")
        return {"status": "sent", "provider": "whatsapp", "id": msg_id, "kind": "template"}
    except httpx.HTTPError as exc:
        detail = exc.response.text[:200] if isinstance(exc, httpx.HTTPStatusError) else str(exc)
        logger.warning("whatsapp_template_failed", detail=detail)
        return {"status": "failed", "provider": "whatsapp", "error": detail[:300]}


async def send_text(to: str, body: str) -> dict:
    """Send free-form text. Business-initiated messages only deliver inside the
    24h window; otherwise WhatsApp requires a template, so we fall back to the
    approved template to still reach the recipient. Never raises."""
    to = _normalize(to)
    if not to:
        return {"status": "skipped", "provider": "whatsapp", "error": "no recipient number"}
    if not is_configured():
        logger.info("whatsapp_mock_send", to=to[-4:])
        return {"status": "mock", "provider": "whatsapp"}

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": body[:4096]},
    }
    try:
        resp = await _post(payload)
        resp.raise_for_status()
        msg_id = (resp.json().get("messages") or [{}])[0].get("id", "")
        return {"status": "sent", "provider": "whatsapp", "id": msg_id, "kind": "text"}
    except httpx.HTTPError as exc:
        detail = ""
        code = None
        if isinstance(exc, httpx.HTTPStatusError):
            detail = exc.response.text[:300]
            try:
                code = (exc.response.json().get("error") or {}).get("code")
            except Exception:
                code = None
        # Outside the 24h window -> deliver an approved template instead.
        if code in _REENGAGEMENT_CODES:
            logger.info("whatsapp_text_window_closed_fallback_template", to=to[-4:])
            return await send_template(to)
        logger.warning("whatsapp_send_failed", error=str(exc), detail=detail)
        return {"status": "failed", "provider": "whatsapp", "error": (detail or str(exc))[:300]}
