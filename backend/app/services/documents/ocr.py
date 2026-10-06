"""
Document OCR / field extraction.

Primary engine: Gemini Vision (multimodal) extracts structured fields. When no
API key is set (or on error), a deterministic mock returns sample fields so the
pipeline is testable offline. The mock is clearly labelled with low confidence.
"""
from __future__ import annotations

import json

from app.core.logging import get_logger
from app.services.ai import gemini_client

logger = get_logger("ocr")

FIELDS = [
    "document_type", "full_name", "document_number", "nationality",
    "date_of_birth", "expiry_date", "issuing_country",
]

_PROMPT = (
    "You are extracting data from a travel document image/PDF. Return ONLY a JSON object "
    "with these keys (use null if not present): "
    + ", ".join(FIELDS)
    + ". Dates must be ISO format YYYY-MM-DD. Names and numbers exactly as printed. "
    "Do not include any text outside the JSON."
)


def _parse_json(text: str) -> dict:
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:]
    start, end = t.find("{"), t.rfind("}")
    if start != -1 and end != -1:
        t = t[start : end + 1]
    return json.loads(t)


def _mock_fields() -> dict:
    # Intentionally contains issues (expired passport, missing nationality) so the
    # validation layer has something to detect in offline/CI runs.
    return {
        "document_type": "passport",
        "full_name": "JOHN DOE",
        "document_number": "P1234567",
        "nationality": None,
        "date_of_birth": "1990-05-14",
        "expiry_date": "2021-03-01",
        "issuing_country": "PK",
    }


async def extract(file_bytes: bytes, mime: str, doc_type: str) -> tuple[dict, float, str]:
    """Return (fields, overall_confidence, engine)."""
    if gemini_client.is_configured():
        try:
            raw = await gemini_client.generate_vision(
                prompt=f"{_PROMPT}\nThe user says this is a {doc_type}.",
                file_bytes=file_bytes, mime=mime,
            )
            fields = _parse_json(raw)
            fields = {k: fields.get(k) for k in FIELDS}
            present = sum(1 for v in fields.values() if v)
            confidence = round(present / len(FIELDS), 2)
            return fields, confidence, "gemini-vision"
        except Exception as exc:  # noqa: BLE001 - fall back on any extraction failure
            logger.warning("ocr_fallback", error=str(exc))
    return _mock_fields(), 0.4, "mock"
