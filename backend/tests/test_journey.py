"""
End-to-end user journey (QA) — exercises the full happy path across modules,
all offline/mock: register -> preferences -> plan trip -> chat -> verify
document -> notifications -> usage tracking.
"""
from __future__ import annotations

from datetime import date, timedelta


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_full_user_journey(client):
    # 1. Register
    reg = await client.post("/api/v1/auth/register", json={
        "email": "journey@example.com", "password": "Journey123!", "full_name": "Journey User"})
    assert reg.status_code == 201
    token = reg.json()["tokens"]["access_token"]
    h = auth_header(token)

    # 2. Default subscription is Free
    sub = await client.get("/api/v1/billing/subscription", headers=h)
    assert sub.json()["plan_code"] == "free"

    # 3. Set notification preferences (opt into WhatsApp)
    prefs = await client.patch("/api/v1/notifications/preferences",
                               json={"phone_number": "+971500000001", "whatsapp_opt_in": True}, headers=h)
    assert prefs.status_code == 200 and prefs.json()["whatsapp_opt_in"] is True

    # 4. Plan a trip Lahore -> Dubai
    dubai = next(c["id"] for c in (await client.get("/api/v1/locations/cities?country=AE")).json() if c["name"] == "Dubai")
    lahore = next(c["id"] for c in (await client.get("/api/v1/locations/cities?country=PK")).json() if c["name"] == "Lahore")
    start = (date.today() + timedelta(days=20)).isoformat()
    end = (date.today() + timedelta(days=25)).isoformat()
    trip = await client.post("/api/v1/trips", headers=h, json={
        "destination_city_id": dubai, "origin_city_id": lahore,
        "start_date": start, "end_date": end, "budget_tier": "medium", "travelers": 2})
    assert trip.status_code == 201
    detail = await client.get(f"/api/v1/trips/{trip.json()['id']}", headers=h)
    assert detail.json()["visa"]["requirement"] == "visa_required"
    assert len(detail.json()["suggested_flights"]) >= 1

    # 5. Ask the AI assistant
    chat = await client.post("/api/v1/chat/", headers=h,
                             json={"message": "Do I need a visa for Dubai from Pakistan?"})
    assert chat.status_code == 200 and chat.json()["intent"] == "visa"
    assert "visa required" in chat.json()["reply"]["content"].lower()

    # 6. Verify a document (mock OCR)
    import io
    from PIL import Image
    buf = io.BytesIO(); Image.new("RGB", (60, 40), (230, 230, 230)).save(buf, "PNG")
    doc = await client.post("/api/v1/documents", headers=h,
                            files={"file": ("passport.png", buf.getvalue(), "image/png")},
                            data={"doc_type": "passport", "consent": "true"})
    assert doc.status_code == 201 and doc.json()["status"] == "analyzed"

    # 7. Notifications were recorded across channels/events
    notifs = await client.get("/api/v1/notifications", headers=h)
    events = {(n["channel"], n["event"]) for n in notifs.json()}
    assert ("email", "welcome") in events
    assert ("whatsapp", "trip_created") in events
    assert any(e == "document_verified" for _, e in events)

    # 8. Usage tracked against the Free plan
    sub2 = await client.get("/api/v1/billing/subscription", headers=h)
    usage = {u["feature"]: u["used"] for u in sub2.json()["usage"]}
    assert usage.get("chatbot_messages", 0) >= 1
    assert usage.get("ocr_documents", 0) >= 1
