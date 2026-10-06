"""Integration tests for Phase 4 — Authentication & RBAC."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.deps import require_permissions, require_roles
from app.core.rbac import Perms, Roles
from app.models.user import Role, User
from app.services import auth_service

REG = {"email": "alice@example.com", "password": "Sup3rSecret!", "full_name": "Alice A"}


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_register_returns_user_tokens_and_role(client):
    r = await client.post("/api/v1/auth/register", json=REG)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["user"]["email"] == "alice@example.com"
    assert body["user"]["is_verified"] is False
    assert Roles.TRAVELER in body["user"]["roles"]
    assert Perms.TRIP_MANAGE in body["user"]["permissions"]
    assert body["tokens"]["access_token"] and body["tokens"]["refresh_token"]
    assert body["verification_token"]  # dev convenience


async def test_me_reflects_authenticated_user(client):
    r = await client.post("/api/v1/auth/register", json=REG)
    token = r.json()["tokens"]["access_token"]
    me = await client.get("/api/v1/auth/me", headers=auth_header(token))
    assert me.status_code == 200
    assert me.json()["email"] == "alice@example.com"


async def test_register_duplicate_email_conflicts(client):
    await client.post("/api/v1/auth/register", json=REG)
    r = await client.post("/api/v1/auth/register", json=REG)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "email_taken"


async def test_register_weak_password_rejected(client):
    r = await client.post("/api/v1/auth/register", json={**REG, "password": "short"})
    assert r.status_code == 422


async def test_login_success_and_failures(client):
    await client.post("/api/v1/auth/register", json=REG)
    ok = await client.post("/api/v1/auth/login", json={"email": REG["email"], "password": REG["password"]})
    assert ok.status_code == 200 and ok.json()["access_token"]

    bad_pw = await client.post("/api/v1/auth/login", json={"email": REG["email"], "password": "wrongwrong"})
    assert bad_pw.status_code == 401 and bad_pw.json()["error"]["code"] == "invalid_credentials"

    unknown = await client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "whatever1"})
    assert unknown.status_code == 401


async def test_me_requires_valid_token(client):
    assert (await client.get("/api/v1/auth/me")).status_code == 401
    assert (await client.get("/api/v1/auth/me", headers=auth_header("garbage"))).status_code == 401


async def test_refresh_rotation_single_use(client):
    reg = (await client.post("/api/v1/auth/register", json=REG)).json()
    old_refresh = reg["tokens"]["refresh_token"]

    first = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert first.status_code == 200
    new_refresh = first.json()["refresh_token"]
    assert new_refresh != old_refresh

    # Re-using the rotated (old) refresh token must fail.
    reuse = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert reuse.status_code == 401
    # The new one still works.
    assert (await client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})).status_code == 200


async def test_logout_revokes_refresh_token(client):
    reg = (await client.post("/api/v1/auth/register", json=REG)).json()
    refresh = reg["tokens"]["refresh_token"]
    assert (await client.post("/api/v1/auth/logout", json={"refresh_token": refresh})).status_code == 200
    assert (await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})).status_code == 401


async def test_email_verification_flow(client):
    reg = (await client.post("/api/v1/auth/register", json=REG)).json()
    token = reg["verification_token"]
    access = reg["tokens"]["access_token"]
    assert (await client.post("/api/v1/auth/verify-email", json={"token": token})).status_code == 200
    me = await client.get("/api/v1/auth/me", headers=auth_header(access))
    assert me.json()["is_verified"] is True
    # Token is single-use.
    assert (await client.post("/api/v1/auth/verify-email", json={"token": token})).status_code == 400


async def test_password_reset_flow(client, session_factory):
    await client.post("/api/v1/auth/register", json=REG)
    async with session_factory() as s:
        raw = await auth_service.create_password_reset(s, REG["email"])
        await s.commit()
    assert raw

    confirm = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw, "new_password": "BrandNewPass9!"},
    )
    assert confirm.status_code == 200

    old = await client.post("/api/v1/auth/login", json={"email": REG["email"], "password": REG["password"]})
    assert old.status_code == 401
    new = await client.post("/api/v1/auth/login", json={"email": REG["email"], "password": "BrandNewPass9!"})
    assert new.status_code == 200


async def test_password_reset_request_is_non_enumerating(client):
    # Unknown email returns the same generic 200 message.
    r = await client.post("/api/v1/auth/password-reset/request", json={"email": "ghost@example.com"})
    assert r.status_code == 200


async def test_rate_limit_triggers(client):
    last = None
    for _ in range(12):
        last = await client.post("/api/v1/auth/login", json={"email": "x@example.com", "password": "nope12345"})
    assert last.status_code == 429  # configured max is 10/60s


async def test_expired_access_token_rejected(client):
    from app.core.security import create_access_token

    await client.post("/api/v1/auth/register", json=REG)
    expired = create_access_token("00000000-0000-0000-0000-000000000000", expires_minutes=-1)
    r = await client.get("/api/v1/auth/me", headers=auth_header(expired))
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "token_expired"


async def test_rbac_role_and_permission_guards(app_instance, session_factory):
    r = APIRouter()

    @r.get("/_admin_only")
    async def _admin_only(user=Depends(require_roles(Roles.ADMIN))):
        return {"ok": True}

    @r.get("/_needs_user_manage")
    async def _needs_perm(user=Depends(require_permissions(Perms.USER_MANAGE))):
        return {"ok": True}

    app_instance.include_router(r, prefix="/api/v1")

    transport = ASGITransport(app=app_instance)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        trav = (await ac.post("/api/v1/auth/register", json=REG)).json()["tokens"]["access_token"]

        admin_reg = {"email": "admin@example.com", "password": "AdminPass99!", "full_name": "Admin"}
        await ac.post("/api/v1/auth/register", json=admin_reg)
        async with session_factory() as s:
            user = await s.scalar(select(User).where(User.email == "admin@example.com"))
            admin_role = await s.scalar(select(Role).where(Role.name == Roles.ADMIN))
            user.roles = [admin_role]
            await s.commit()
        admin = (await ac.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "AdminPass99!"})).json()["access_token"]

        assert (await ac.get("/api/v1/_admin_only", headers=auth_header(trav))).status_code == 403
        assert (await ac.get("/api/v1/_admin_only", headers=auth_header(admin))).status_code == 200
        assert (await ac.get("/api/v1/_needs_user_manage", headers=auth_header(trav))).status_code == 403
        assert (await ac.get("/api/v1/_needs_user_manage", headers=auth_header(admin))).status_code == 200
