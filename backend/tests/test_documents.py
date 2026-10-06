"""Integration tests for Phase 7 — document verification (keyless mock OCR)."""
from __future__ import annotations

import io

from PIL import Image

from app.services.documents import evaluation, storage


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _token(client, email="doc@example.com") -> str:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "DocPass123!", "full_name": "Doc"},
    )
    return r.json()["tokens"]["access_token"]


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (80, 50), (210, 210, 210)).save(buf, "PNG")
    return buf.getvalue()


def _upload(png=True, consent=True, name=None, ctype=None, data=None):
    content = data if data is not None else (_png() if png else b"plain text not an image")
    fname = name or ("passport.png" if png else "note.txt")
    ct = ctype or ("image/png" if png else "text/plain")
    return {"files": {"file": (fname, content, ct)}, "data": {"doc_type": "passport", "consent": str(consent).lower()}}


async def test_upload_requires_auth(client):
    u = _upload()
    r = await client.post("/api/v1/documents", files=u["files"], data=u["data"])
    assert r.status_code == 401


async def test_upload_success_and_analysis(client):
    token = await _token(client)
    u = _upload()
    r = await client.post("/api/v1/documents", files=u["files"], data=u["data"], headers=auth_header(token))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "analyzed"
    analysis = body["analyses"][0]
    assert analysis["engine"] == "mock"  # no Gemini key in tests
    assert len(analysis["fields"]) == 7
    codes = {f["code"] for f in analysis["findings"]}
    assert "expired" in codes          # mock expiry is 2021
    assert "missing_field" in codes    # mock nationality is null
    assert analysis["summary"]


async def test_upload_requires_consent(client):
    token = await _token(client)
    u = _upload(consent=False)
    r = await client.post("/api/v1/documents", files=u["files"], data=u["data"], headers=auth_header(token))
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "consent_required"


async def test_upload_rejects_unsupported_extension(client):
    token = await _token(client)
    u = _upload(png=False)  # .txt / text/plain
    r = await client.post("/api/v1/documents", files=u["files"], data=u["data"], headers=auth_header(token))
    assert r.status_code == 415


async def test_upload_rejects_content_magic_mismatch(client):
    token = await _token(client)
    # .png extension + image/png content-type but the bytes are NOT a PNG
    u = _upload(name="fake.png", ctype="image/png", data=b"this is definitely not a png")
    r = await client.post("/api/v1/documents", files=u["files"], data=u["data"], headers=auth_header(token))
    assert r.status_code == 415
    assert r.json()["error"]["code"] in ("content_mismatch", "mime_mismatch")


async def test_upload_rejects_too_large(client):
    token = await _token(client)
    big = b"\xff\xd8\xff" + b"\x00" * (2 * 1024 * 1024 + 50)  # > 2 MB test limit, jpeg magic
    u = _upload(name="big.jpg", ctype="image/jpeg", data=big)
    r = await client.post("/api/v1/documents", files=u["files"], data=u["data"], headers=auth_header(token))
    assert r.status_code == 413


async def test_documents_list_get_and_idor(client):
    a = await _token(client, "owner@example.com")
    u = _upload()
    created = await client.post("/api/v1/documents", files=u["files"], data=u["data"], headers=auth_header(a))
    doc_id = created.json()["id"]

    listed = await client.get("/api/v1/documents", headers=auth_header(a))
    assert any(d["id"] == doc_id for d in listed.json())

    b = await _token(client, "intruder@example.com")
    stolen = await client.get(f"/api/v1/documents/{doc_id}", headers=auth_header(b))
    assert stolen.status_code == 404  # IDOR-safe


async def test_document_delete(client):
    token = await _token(client)
    u = _upload()
    created = await client.post("/api/v1/documents", files=u["files"], data=u["data"], headers=auth_header(token))
    doc_id = created.json()["id"]
    deleted = await client.delete(f"/api/v1/documents/{doc_id}", headers=auth_header(token))
    assert deleted.status_code == 204
    gone = await client.get(f"/api/v1/documents/{doc_id}", headers=auth_header(token))
    assert gone.status_code == 404


def test_storage_encrypts_and_round_trips():
    data = b"super secret passport bytes"
    path, sha = storage.save_encrypted(data)
    try:
        # ciphertext on disk must differ from plaintext
        from pathlib import Path
        from app.core.config import get_settings
        blob = Path(get_settings().storage_dir, path).read_bytes()
        assert data not in blob
        assert storage.load_decrypted(path) == data
    finally:
        storage.delete_file(path)


def test_validation_accuracy_meets_target():
    result = evaluation.evaluate_validation()
    assert result["accuracy"] >= 0.90, f"validation accuracy {result['accuracy']:.1%}; misses={result['failures']}"
