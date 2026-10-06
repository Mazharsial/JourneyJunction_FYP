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


async def send_text(to: str, body: str) -> dict:
    """Return {status, provider, id?, error?}. Never raises."""
    to = _normalize(to)
    if not to:
        return {"status": "skipped", "provider": "whatsapp", "error": "no recipient number"}
    if not is_configured():
        logger.info("whatsapp_mock_send", to=to[-4:])
        return {"status": "mock", "provider": "whatsapp"}

    s = get_settings()
    url = f"https://graph.facebook.com/{s.whatsapp_api_version}/{s.whatsapp_phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": body[:4096]},
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                url, json=payload,
                headers={"Authorization": f"Bearer {s.whatsapp_access_token}"},
            )
            resp.raise_for_status()
            data = resp.json()
        msg_id = (data.get("messages") or [{}])[0].get("id", "")
        return {"status": "sent", "provider": "whatsapp", "id": msg_id}
    except httpx.HTTPError as exc:
        detail = ""
        if isinstance(exc, httpx.HTTPStatusError):
            detail = exc.response.text[:200]
        logger.warning("whatsapp_send_failed", error=str(exc), detail=detail)
        return {"status": "failed", "provider": "whatsapp", "error": (detail or str(exc))[:300]}
