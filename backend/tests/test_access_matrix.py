"""
Access-control matrix (QA + security audit): every protected endpoint must
reject anonymous access (401), and admin endpoints must reject non-admins (403).
"""
from __future__ import annotations

import pytest

PROTECTED = [
    ("GET", "/api/v1/auth/me"),
    ("GET", "/api/v1/trips"),
    ("POST", "/api/v1/trips"),
    ("GET", "/api/v1/flights/search?origin=LHE&destination=DXB&date=2027-01-01"),
    ("POST", "/api/v1/chat/"),
    ("GET", "/api/v1/chat/conversations"),
    ("GET", "/api/v1/documents"),
    ("GET", "/api/v1/billing/subscription"),
    ("POST", "/api/v1/billing/checkout"),
    ("GET", "/api/v1/notifications"),
    ("GET", "/api/v1/notifications/preferences"),
    ("GET", "/api/v1/admin/stats"),
    ("GET", "/api/v1/admin/users"),
    ("GET", "/api/v1/admin/audit-logs"),
]

ADMIN_ONLY = [
    ("GET", "/api/v1/admin/stats"),
    ("GET", "/api/v1/admin/users"),
    ("GET", "/api/v1/admin/health"),
    ("GET", "/api/v1/admin/audit-logs"),
    ("GET", "/api/v1/admin/visa-rules"),
    ("GET", "/api/v1/admin/plans"),
]


async def _call(client, method, path, headers=None):
    if method == "GET":
        return await client.get(path, headers=headers)
    return await client.post(path, json={}, headers=headers)


@pytest.mark.parametrize("method,path", PROTECTED)
async def test_requires_authentication(client, method, path):
    resp = await _call(client, method, path)
    assert resp.status_code == 401, f"{method} {path} returned {resp.status_code}, expected 401"


@pytest.mark.parametrize("method,path", ADMIN_ONLY)
async def test_admin_endpoints_reject_non_admin(client, method, path):
    reg = await client.post("/api/v1/auth/register",
                            json={"email": f"t{abs(hash(path)) % 10000}@example.com",
                                  "password": "Traveler123!", "full_name": "T"})
    token = reg.json()["tokens"]["access_token"]
    resp = await _call(client, method, path, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403, f"{method} {path} returned {resp.status_code}, expected 403"


async def test_public_endpoints_are_open(client):
    # Reference data + marketing surfaces are intentionally public.
    for path in ("/", "/api/v1/health", "/api/v1/locations/countries",
                 "/api/v1/billing/plans", "/openapi.json"):
        assert (await client.get(path)).status_code == 200
