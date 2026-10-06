"""
Minimal async Google Gemini client (REST).

Uses httpx directly against the Generative Language API to avoid SDK churn.
`is_configured()` reports whether a key is set; the chat service falls back to a
grounded response when it is not (or on any API error).
"""
from __future__ import annotations

import base64

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("gemini")
_BASE = "https://generativelanguage.googleapis.com/v1beta"


def is_configured() -> bool:
    return bool(get_settings().gemini_api_key)


class GeminiError(Exception):
    pass


async def generate(
    *, system_instruction: str, history: list[dict], user_message: str,
    temperature: float = 0.3, max_output_tokens: int = 700,
) -> str:
    """
    history: list of {"role": "user"|"assistant", "content": str}.
    Returns the model's text. Raises GeminiError on failure.
    """
    settings = get_settings()
    if not settings.gemini_api_key:
        raise GeminiError("Gemini API key not configured")

    contents = []
    for m in history:
        role = "user" if m["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    body = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": contents,
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_output_tokens},
    }
    url = f"{_BASE}/models/{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"

    try:
        async with httpx.AsyncClient(timeout=25) as client:
            resp = await client.post(url, json=body)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        raise GeminiError(f"Gemini request failed: {exc}") from exc

    try:
        candidate = data["candidates"][0]
        parts = candidate["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts).strip()
    except (KeyError, IndexError) as exc:
        raise GeminiError(f"Unexpected Gemini response shape: {exc}") from exc

    if not text:
        raise GeminiError("Empty response from Gemini")
    return text


async def generate_vision(*, prompt: str, file_bytes: bytes, mime: str,
                          temperature: float = 0.1, max_output_tokens: int = 800) -> str:
    """Send an image/PDF + prompt to Gemini (multimodal). Returns the text reply."""
    settings = get_settings()
    if not settings.gemini_api_key:
        raise GeminiError("Gemini API key not configured")

    body = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime, "data": base64.b64encode(file_bytes).decode()}},
            ],
        }],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_output_tokens},
    }
    url = f"{_BASE}/models/{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
    try:
        async with httpx.AsyncClient(timeout=40) as client:
            resp = await client.post(url, json=body)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        raise GeminiError(f"Gemini vision request failed: {exc}") from exc
    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts).strip()
    except (KeyError, IndexError) as exc:
        raise GeminiError(f"Unexpected Gemini vision response: {exc}") from exc
