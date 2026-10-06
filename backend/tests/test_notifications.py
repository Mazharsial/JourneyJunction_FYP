"""Integration tests for Phase 8 — WhatsApp + Klaviyo (mock mode, offline)."""
from __future__ import annotations


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _token(client, email="notify@example.com") -> str:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "NotifyPass123!", "full_name": "Notify"},
    )
    return r.json()["tokens"]["access_token"]


async def test_welcome_notification_recorded_on_register(client):
    token = await _token(client)
    # email_opt_in defaults True -> a welcome email event is recorded (mock provider).
    notifs = await client.get("/api/v1/notifications", headers=auth_header(token))
    assert notifs.status_code == 200
    events = [(n["channel"], n["event"], n["status"]) for n in notifs.json()]
    assert ("email", "welcome", "mock") in events


async def test_preferences_defaults_and_update(client):
    token = await _token(client)
    prefs = await client.get("/api/v1/notifications/preferences", headers=auth_header(token))
    assert prefs.status_code == 200
    body = prefs.json()
    assert body["email_opt_in"] is True
    assert body["whatsapp_opt_in"] is False
    assert body["whatsapp_enabled"] is False  # no WhatsApp key in tests
    assert body["email_enabled"] is False     # no Klaviyo key in tests

    upd = await client.patch(
        "/api/v1/notifications/preferences",
        json={"phone_number": "+971500000000", "whatsapp_opt_in": True},
        headers=auth_header(token),
    )
    assert upd.status_code == 200
    assert upd.json()["phone_number"] == "+971500000000"
    assert upd.json()["whatsapp_opt_in"] is True


async def test_trip_creation_sends_whatsapp_when_opted_in(client):
    token = await _token(client)
    await client.patch("/api/v1/notifications/preferences",
                       json={"phone_number": "+971500000000", "whatsapp_opt_in": True},
                       headers=auth_header(token))
    cities = (await client.get("/api/v1/locations/cities?country=AE")).json()
    dubai = next(c["id"] for c in cities if c["name"] == "Dubai")
    from datetime import date, timedelta
    start = (date.today() + timedelta(days=10)).isoformat()
    end = (date.today() + timedelta(days=12)).isoformat()
    await client.post("/api/v1/trips",
                      json={"destination_city_id": dubai, "start_date": start, "end_date": end},
                      headers=auth_header(token))
    notifs = await client.get("/api/v1/notifications", headers=auth_header(token))
    whatsapp = [n for n in notifs.json() if n["channel"] == "whatsapp" and n["event"] == "trip_created"]
    assert len(whatsapp) == 1
    assert whatsapp[0]["status"] == "mock"  # no WhatsApp key -> mock, but recorded


async def test_test_send_requires_phone_for_whatsapp(client):
    token = await _token(client)
    r = await client.post("/api/v1/notifications/test",
                          json={"channel": "whatsapp", "message": "hi"}, headers=auth_header(token))
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "no_phone"


async def test_whatsapp_webhook_verification(client):
    # verify token not configured in tests -> 403
    r = await client.get("/api/v1/notifications/whatsapp/webhook",
                         params={"hub.mode": "subscribe", "hub.verify_token": "x", "hub.challenge": "123"})
    assert r.status_code == 403


async def test_whatsapp_inbound_webhook_records_message(client):
    payload = {"entry": [{"changes": [{"value": {"messages": [
        {"from": "15551234567", "text": {"body": "Hello"}}
    ]}}]}]}
    r = await client.post("/api/v1/notifications/whatsapp/webhook", json=payload)
    assert r.status_code == 200
    assert r.json()["received"] is True
