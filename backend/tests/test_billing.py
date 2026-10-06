"""Integration tests for Phase 9 — subscriptions & entitlement enforcement (keyless)."""
from __future__ import annotations

import io

from PIL import Image

from app.core.entitlements import Features, Plans
from app.core.exceptions import AppError
from app.services.billing import entitlement_service


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _token(client, email="bill@example.com") -> str:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "BillPass123!", "full_name": "Bill"},
    )
    return r.json()["tokens"]["access_token"]


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (60, 40), (220, 220, 220)).save(buf, "PNG")
    return buf.getvalue()


async def test_plans_listing(client):
    r = await client.get("/api/v1/billing/plans")
    assert r.status_code == 200
    body = r.json()
    codes = {p["code"] for p in body["plans"]}
    assert {Plans.FREE, Plans.PRO, Plans.BUSINESS} <= codes
    assert body["billing_enabled"] is False  # no Stripe key in tests
    free = next(p for p in body["plans"] if p["code"] == "free")
    ocr = next(f for f in free["features"] if f["feature_key"] == Features.OCR_DOCUMENTS)
    assert ocr["limit_value"] == 3


async def test_default_subscription_is_free(client):
    token = await _token(client)
    r = await client.get("/api/v1/billing/subscription", headers=auth_header(token))
    assert r.status_code == 200
    assert r.json()["plan_code"] == "free"


async def test_ocr_limit_enforced_server_side(client):
    token = await _token(client)
    files = {"file": ("p.png", _png(), "image/png")}
    data = {"doc_type": "passport", "consent": "true"}
    # Free plan allows 3 OCR documents/month.
    for _ in range(3):
        ok = await client.post("/api/v1/documents", files={"file": ("p.png", _png(), "image/png")},
                               data=data, headers=auth_header(token))
        assert ok.status_code == 201
    # 4th is blocked by entitlement enforcement, not the UI.
    blocked = await client.post("/api/v1/documents", files=files, data=data, headers=auth_header(token))
    assert blocked.status_code == 402
    assert blocked.json()["error"]["code"] == "limit_reached"


async def test_checkout_requires_billing_configured(client):
    token = await _token(client)
    r = await client.post("/api/v1/billing/checkout", json={"plan_code": "pro"}, headers=auth_header(token))
    assert r.status_code == 503  # Stripe not configured in tests
    assert r.json()["error"]["code"] == "billing_unconfigured"


async def test_consume_unit_limit_and_unlimited(session_factory, client):
    # register a user via the API so a DB row exists
    token = await _token(client, "unit@example.com")
    # fetch the user id through /me
    me = await client.get("/api/v1/auth/me", headers=auth_header(token))
    import uuid
    user_id = uuid.UUID(me.json()["id"])

    async with session_factory() as s:
        # chatbot_messages free limit = 20
        for _ in range(20):
            await entitlement_service.consume(s, user_id, Features.CHATBOT_MESSAGES)
        raised = False
        try:
            await entitlement_service.consume(s, user_id, Features.CHATBOT_MESSAGES)
        except AppError as e:
            raised = e.status_code == 402
        assert raised
        # trip_planning is unlimited -> never raises
        for _ in range(5):
            res = await entitlement_service.consume(s, user_id, Features.TRIP_PLANNING)
        assert res.get("unlimited") is True
        # whatsapp disabled on free -> 403
        denied = False
        try:
            await entitlement_service.consume(s, user_id, Features.WHATSAPP)
        except AppError as e:
            denied = e.status_code == 403
        assert denied
