"""Integration tests for Phase 6 — AI chatbot (grounded fallback path, keyless)."""
from __future__ import annotations

from app.services.ai import evaluation


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _token(client, email="chat@example.com") -> str:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "ChatPass123!", "full_name": "Chat"},
    )
    return r.json()["tokens"]["access_token"]


async def test_chat_requires_auth(client):
    r = await client.post("/api/v1/chat/", json={"message": "hi"})
    assert r.status_code == 401


async def test_chat_visa_grounded_answer(client):
    token = await _token(client)
    r = await client.post(
        "/api/v1/chat/",
        headers=auth_header(token),
        json={"message": "Do I need a visa for Dubai from Pakistan?"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["intent"] == "visa"
    assert body["status"] == "fallback"  # no Gemini key in tests
    text = body["reply"]["content"].lower()
    assert "visa required" in text
    assert "informational only" in text  # disclaimer present
    assert body["conversation_id"]


async def test_chat_keeps_conversation_history(client):
    token = await _token(client)
    first = await client.post(
        "/api/v1/chat/", headers=auth_header(token), json={"message": "Hello"}
    )
    cid = first.json()["conversation_id"]
    await client.post(
        "/api/v1/chat/",
        headers=auth_header(token),
        json={"message": "Suggest hotels in Dubai", "conversation_id": cid},
    )
    detail = await client.get(f"/api/v1/chat/conversations/{cid}", headers=auth_header(token))
    assert detail.status_code == 200
    msgs = detail.json()["messages"]
    # 2 user + 2 assistant
    assert len(msgs) == 4
    assert [m["role"] for m in msgs] == ["user", "assistant", "user", "assistant"]


async def test_chat_out_of_scope_is_declined(client):
    token = await _token(client)
    r = await client.post(
        "/api/v1/chat/", headers=auth_header(token), json={"message": "Write me a Python function"}
    )
    body = r.json()
    assert body["intent"] == "out_of_scope"
    assert "travel" in body["reply"]["content"].lower()


async def test_conversation_list_and_idor(client):
    a = await _token(client, "owner@example.com")
    created = await client.post("/api/v1/chat/", headers=auth_header(a), json={"message": "Hi"})
    cid = created.json()["conversation_id"]

    lst = await client.get("/api/v1/chat/conversations", headers=auth_header(a))
    assert any(c["id"] == cid for c in lst.json())

    b = await _token(client, "intruder@example.com")
    stolen = await client.get(f"/api/v1/chat/conversations/{cid}", headers=auth_header(b))
    assert stolen.status_code == 404


# ---- measured accuracy (the >=90% target, verified in CI) ----
def test_intent_accuracy_meets_target():
    result = evaluation.evaluate_intents()
    assert result["accuracy"] >= 0.90, f"intent accuracy {result['accuracy']:.1%}; misses={result['failures']}"


async def test_visa_grounding_accuracy_meets_target(session_factory):
    async with session_factory() as s:
        result = await evaluation.evaluate_grounding(s)
    assert result["accuracy"] >= 0.90, f"grounding accuracy {result['accuracy']:.1%}; misses={result['failures']}"
