"""
Phase 15 — adversarial audit tests (attempting to abuse the system).
Complements test_access_matrix.py (auth/role gating on every endpoint).
"""
from __future__ import annotations

from sqlalchemy import select

from app.models.user import User


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_disabled_user_token_is_rejected(client, session_factory):
    reg = await client.post("/api/v1/auth/register",
                            json={"email": "disabled@example.com", "password": "Disabled123!", "full_name": "D"})
    token = reg.json()["tokens"]["access_token"]
    assert (await client.get("/api/v1/auth/me", headers=auth_header(token))).status_code == 200

    async with session_factory() as s:
        u = await s.scalar(select(User).where(User.email == "disabled@example.com"))
        u.is_active = False
        await s.commit()

    # Existing access token must stop working once the account is disabled.
    assert (await client.get("/api/v1/auth/me", headers=auth_header(token))).status_code == 401


async def test_user_cannot_escalate_roles_via_preferences(client):
    reg = await client.post("/api/v1/auth/register",
                            json={"email": "escalate@example.com", "password": "Escalate123!", "full_name": "E"})
    token = reg.json()["tokens"]["access_token"]
    # Attempt to smuggle a 'roles' field into the preferences update (not in the schema).
    await client.patch("/api/v1/notifications/preferences",
                       json={"full_name": "E", "roles": ["admin", "super_admin"]},
                       headers=auth_header(token))
    me = await client.get("/api/v1/auth/me", headers=auth_header(token))
    assert me.json()["roles"] == ["traveler"]  # unchanged — mass-assignment prevented
    assert (await client.get("/api/v1/admin/stats", headers=auth_header(token))).status_code == 403


async def test_registration_cannot_self_assign_privileges(client):
    # Extra fields in the register body must not grant elevated access.
    r = await client.post("/api/v1/auth/register", json={
        "email": "sneaky@example.com", "password": "Sneaky123!", "full_name": "S",
        "is_verified": True, "roles": ["admin"], "is_active": True})
    body = r.json()["user"]
    assert body["is_verified"] is False
    assert body["roles"] == ["traveler"]


async def test_error_responses_do_not_leak_internals(client):
    # A 404 envelope should be generic, with no stack trace / SQL / paths.
    r = await client.get("/api/v1/trips/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 401  # auth first
    text = r.text.lower()
    assert "traceback" not in text and "select " not in text and "c:\\" not in text
