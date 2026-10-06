"""Foundation smoke tests — no external services required."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def test_root_banner():
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["service"].endswith("API")
    assert "version" in body


def test_health_liveness():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["app"]  # brand name present
    assert body["environment"]


def test_security_headers_present():
    resp = client.get("/api/v1/health")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert "Content-Security-Policy" in resp.headers


def test_correlation_id_echoed():
    resp = client.get("/api/v1/health")
    assert resp.headers.get("X-Request-ID")


def test_openapi_available():
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert resp.json()["info"]["title"].endswith("API")
