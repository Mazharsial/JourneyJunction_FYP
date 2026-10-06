"""
File-upload hardening for document uploads (untrusted input).

Checks: size limit, extension allow-list, declared MIME allow-list, and real
content sniffing via magic bytes (defends against a spoofed Content-Type). The
stored filename is a UUID — the user's filename is never used on disk, so path
traversal is impossible.
"""
from __future__ import annotations

from app.core.config import get_settings
from app.core.exceptions import AppError

# extension -> allowed declared MIME types
ALLOWED = {
    "jpg": {"image/jpeg"},
    "jpeg": {"image/jpeg"},
    "png": {"image/png"},
    "pdf": {"application/pdf"},
}

# magic-byte signatures
_MAGIC = [
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"%PDF-", "application/pdf"),
]


def _sniff(data: bytes) -> str | None:
    for sig, mime in _MAGIC:
        if data.startswith(sig):
            return mime
    return None


def validate_upload(filename: str, content_type: str, data: bytes) -> str:
    """Validate an upload and return the verified MIME type, or raise AppError."""
    settings = get_settings()
    max_bytes = settings.max_upload_mb * 1024 * 1024

    if not data:
        raise AppError("Empty file.", code="empty_file", status_code=422)
    if len(data) > max_bytes:
        raise AppError(
            f"File too large (max {settings.max_upload_mb} MB).",
            code="file_too_large", status_code=413,
        )

    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
    if ext not in ALLOWED:
        raise AppError(
            "Unsupported file type. Allowed: JPG, PNG, PDF.",
            code="unsupported_type", status_code=415,
        )

    declared = (content_type or "").split(";")[0].strip().lower()
    if declared not in ALLOWED[ext]:
        raise AppError(
            "File content type does not match its extension.",
            code="mime_mismatch", status_code=415,
        )

    sniffed = _sniff(data)
    if sniffed is None or sniffed not in ALLOWED[ext]:
        raise AppError(
            "File contents do not match a supported image/PDF format.",
            code="content_mismatch", status_code=415,
        )
    return sniffed
