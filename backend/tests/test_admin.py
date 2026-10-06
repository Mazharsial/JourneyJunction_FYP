"""Integration tests for Phase 10 — admin panel (access control + management)."""
from __future__ import annotations

from sqlalchemy import select

from app.core.rbac import Roles
from app.models.user import Role, User


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _register(client, email: str) -> str:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "AdminPass123!", "full_name": "User"},
    )
    return r.json()["tokens"]["access_token"]


async def _elevate(session_factory, email: str, role_name: str) -> None:
    async with session_factory() as s:
        u = await s.scalar(select(User).where(User.email == email))
        role = await s.scalar(select(Role).where(Role.name == role_name))
        u.roles = [*u.roles, role]
        await s.commit()


async def _admin(client, session_factory, email="admin@example.com") -> str:
    token = await _register(client, email)
    await _elevate(session_factory, email, Roles.ADMIN)
    return token


async def test_admin_area_requires_permission(client, session_factory):
    traveler = await _register(client, "trav@example.com")
    assert (await client.get("/api/v1/admin/stats")).status_code == 401
    assert (await client.get("/api/v1/admin/stats", headers=auth_header(traveler))).status_code == 403


async def test_admin_stats_and_health(client, session_factory):
    token = await _admin(client, session_factory)
    stats = await client.get("/api/v1/admin/stats", headers=auth_header(token))
    assert stats.status_code == 200
    assert stats.json()["users_total"] >= 1
    health = await client.get("/api/v1/admin/health", headers=auth_header(token))
    assert health.json()["database"] == "ok"
    assert health.json()["stripe"] == "disabled"  # no key in tests


async def test_admin_lists_and_searches_users(client, session_factory):
    token = await _admin(client, session_factory, "admin2@example.com")
    await _register(client, "findme@example.com")
    res = await client.get("/api/v1/admin/users?q=findme", headers=auth_header(token))
    assert res.status_code == 200
    emails = [u["email"] for u in res.json()["items"]]
    assert "findme@example.com" in emails


async def test_admin_updates_user_and_audits(client, session_factory):
    token = await _admin(client, session_factory, "admin3@example.com")
    await _register(client, "target@example.com")
    async with session_factory() as s:
        target = await s.scalar(select(User).where(User.email == "target@example.com"))
        target_id = str(target.id)

    upd = await client.patch(f"/api/v1/admin/users/{target_id}",
                             json={"is_active": False, "roles": ["traveler", "staff"]},
                             headers=auth_header(token))
    assert upd.status_code == 200
    assert upd.json()["is_active"] is False
    assert set(upd.json()["roles"]) == {"traveler", "staff"}

    logs = await client.get("/api/v1/admin/audit-logs", headers=auth_header(token))
    assert any(l["action"] == "user.update" for l in logs.json()["items"])


async def test_admin_cannot_deactivate_self(client, session_factory):
    token = await _admin(client, session_factory, "admin4@example.com")
    async with session_factory() as s:
        me = await s.scalar(select(User).where(User.email == "admin4@example.com"))
        my_id = str(me.id)
    r = await client.patch(f"/api/v1/admin/users/{my_id}", json={"is_active": False},
                           headers=auth_header(token))
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "self_deactivate"


async def test_only_super_admin_grants_super_admin(client, session_factory):
    admin_token = await _admin(client, session_factory, "admin5@example.com")
    await _register(client, "victim@example.com")
    async with session_factory() as s:
        victim = await s.scalar(select(User).where(User.email == "victim@example.com"))
        vid = str(victim.id)
    r = await client.patch(f"/api/v1/admin/users/{vid}",
                           json={"roles": ["traveler", "super_admin"]}, headers=auth_header(admin_token))
    assert r.status_code == 403


async def test_admin_visa_rule_crud(client, session_factory):
    token = await _admin(client, session_factory, "admin6@example.com")
    put = await client.put("/api/v1/admin/visa-rules",
                           json={"origin": "DE", "destination": "AE", "requirement": "visa_on_arrival",
                                 "allowed_stay_days": 90, "notes": "test"},
                           headers=auth_header(token))
    assert put.status_code == 200
    rule_id = put.json()["id"]
    lst = await client.get("/api/v1/admin/visa-rules", headers=auth_header(token))
    assert any(r["origin_iso2"] == "DE" and r["destination_iso2"] == "AE" for r in lst.json())
    deleted = await client.delete(f"/api/v1/admin/visa-rules/{rule_id}", headers=auth_header(token))
    assert deleted.status_code == 204


async def test_admin_updates_plan_feature(client, session_factory):
    token = await _admin(client, session_factory, "admin7@example.com")
    r = await client.patch("/api/v1/admin/plans/free/features",
                           json={"feature_key": "ocr_documents", "limit_value": 10},
                           headers=auth_header(token))
    assert r.status_code == 200
    ocr = next(f for f in r.json()["features"] if f["feature_key"] == "ocr_documents")
    assert ocr["limit_value"] == 10
