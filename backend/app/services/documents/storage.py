"""
Encrypted file storage for sensitive documents.

Files are encrypted at rest with Fernet (AES-128-CBC + HMAC), keyed from
SECRET_KEY, and stored under STORAGE_DIR with a UUID filename (outside the web
root; never served statically). Plaintext exists only transiently in memory
during OCR.
"""
from __future__ import annotations

import base64
import hashlib
import uuid
from pathlib import Path

from cryptography.fernet import Fernet

from app.core.config import get_settings


def _fernet() -> Fernet:
    secret = get_settings().secret_key.encode("utf-8")
    key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return Fernet(key)


def _base_dir() -> Path:
    d = Path(get_settings().storage_dir) / "documents"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_encrypted(data: bytes) -> tuple[str, str]:
    """Encrypt and store `data`. Returns (relative_storage_path, sha256_of_plaintext)."""
    sha = hashlib.sha256(data).hexdigest()
    token = _fernet().encrypt(data)
    name = f"{uuid.uuid4().hex}.enc"
    path = _base_dir() / name
    path.write_bytes(token)
    return f"documents/{name}", sha


def load_decrypted(relative_path: str) -> bytes:
    path = Path(get_settings().storage_dir) / relative_path
    return _fernet().decrypt(path.read_bytes())


def delete_file(relative_path: str) -> None:
    path = Path(get_settings().storage_dir) / relative_path
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
