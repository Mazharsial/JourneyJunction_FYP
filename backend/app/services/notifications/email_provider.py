"""
Email/marketing provider abstraction (swappable).

Klaviyo is event-driven: we upsert a contact profile and track events; Klaviyo
Flows (configured in the Klaviyo UI) turn those events into emails. The
abstraction lets the provider be replaced without touching callers. A Mock
provider is used when no key is configured.
"""
from __future__ import annotations

from typing import Protocol

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("email")
_KLAVIYO_REVISION = "2024-10-15"


class EmailProvider(Protocol):
    name: str

    async def upsert_contact(self, email: str, properties: dict) -> dict: ...
    async def track_event(self, email: str, event: str, properties: dict) -> dict: ...


class MockEmailProvider:
    name = "mock"

    async def upsert_contact(self, email: str, properties: dict) -> dict:
        logger.info("email_mock_contact", email=email)
        return {"status": "mock", "provider": "mock"}

    async def track_event(self, email: str, event: str, properties: dict) -> dict:
        logger.info("email_mock_event", email=email, metric=event)
        return {"status": "mock", "provider": "mock"}


class KlaviyoProvider:
    name = "klaviyo"
    _base = "https://a.klaviyo.com/api"

    def _headers(self) -> dict:
        key = get_settings().klaviyo_api_key
        return {
            "Authorization": f"Klaviyo-API-Key {key}",
            "accept": "application/json",
            "content-type": "application/json",
            "revision": _KLAVIYO_REVISION,
        }

    async def upsert_contact(self, email: str, properties: dict) -> dict:
        body = {"data": {"type": "profile", "attributes": {"email": email, "properties": properties}}}
        return await self._post("/profiles/", body)

    async def track_event(self, email: str, event: str, properties: dict) -> dict:
        body = {"data": {"type": "event", "attributes": {
            "metric": {"data": {"type": "metric", "attributes": {"name": event}}},
            "profile": {"data": {"type": "profile", "attributes": {"email": email}}},
            "properties": properties,
        }}}
        return await self._post("/events/", body)

    async def _post(self, path: str, body: dict) -> dict:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(f"{self._base}{path}", json=body, headers=self._headers())
            if resp.status_code >= 400:
                logger.warning("klaviyo_error", status=resp.status_code, detail=resp.text[:200])
                return {"status": "failed", "provider": "klaviyo", "error": resp.text[:300]}
            return {"status": "sent", "provider": "klaviyo"}
        except httpx.HTTPError as exc:
            logger.warning("klaviyo_request_failed", error=str(exc))
            return {"status": "failed", "provider": "klaviyo", "error": str(exc)[:300]}


def is_configured() -> bool:
    return bool(get_settings().klaviyo_api_key)


def get_provider() -> EmailProvider:
    return KlaviyoProvider() if is_configured() else MockEmailProvider()
