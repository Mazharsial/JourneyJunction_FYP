"""
Live OCR field-extraction benchmark (requires a Gemini key).

Generates synthetic passport images with known ground-truth fields, runs them
through the OCR extractor (Gemini Vision), and reports field-level accuracy.
Run:  python -m app.services.documents.ocr_benchmark
"""
from __future__ import annotations

import asyncio
import io
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

from app.services.documents import ocr

SAMPLES = [
    {"full_name": "JOHN DOE", "document_number": "P1234567", "nationality": "PAK",
     "date_of_birth": "1990-05-14", "expiry_date": "2030-03-01", "issuing_country": "PAK"},
    {"full_name": "MARIA GARCIA", "document_number": "X9988776", "nationality": "GBR",
     "date_of_birth": "1985-11-02", "expiry_date": "2029-07-20", "issuing_country": "GBR"},
    {"full_name": "AHMED HASSAN", "document_number": "A4567890", "nationality": "ARE",
     "date_of_birth": "1995-01-30", "expiry_date": "2031-12-15", "issuing_country": "ARE"},
    {"full_name": "LAURA MARTIN", "document_number": "F1122334", "nationality": "FRA",
     "date_of_birth": "1992-09-09", "expiry_date": "2028-04-05", "issuing_country": "FRA"},
]


def _font(size: int):
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _render(gt: dict) -> bytes:
    img = Image.new("RGB", (640, 360), (245, 245, 240))
    d = ImageDraw.Draw(img)
    title = _font(34)
    body = _font(26)
    d.text((30, 20), "PASSPORT", fill=(20, 20, 60), font=title)
    dob = datetime.fromisoformat(gt["date_of_birth"]).strftime("%d %b %Y").upper()
    exp = datetime.fromisoformat(gt["expiry_date"]).strftime("%d %b %Y").upper()
    lines = [
        f"Surname / Given names: {gt['full_name']}",
        f"Passport No.: {gt['document_number']}",
        f"Nationality: {gt['nationality']}",
        f"Date of birth: {dob}",
        f"Date of expiry: {exp}",
        f"Issuing country: {gt['issuing_country']}",
    ]
    for i, ln in enumerate(lines):
        d.text((30, 90 + i * 40), ln, fill=(10, 10, 10), font=body)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def _norm_date(v) -> str | None:
    for fmt in ("%Y-%m-%d", "%d %b %Y", "%d %B %Y", "%d/%m/%Y", "%Y/%m/%d", "%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(str(v).strip(), fmt).date().isoformat()
        except (ValueError, TypeError):
            continue
    return None


def _match(field: str, got, truth) -> bool:
    if got is None:
        return False
    g, t = str(got).strip().upper(), str(truth).strip().upper()
    if field in ("date_of_birth", "expiry_date"):
        return _norm_date(got) == truth
    if field == "document_number":
        return g.replace(" ", "") == t.replace(" ", "")
    if field in ("nationality", "issuing_country"):
        return g[:2] == t[:2] or g[:3] == t[:3]
    if field == "full_name":
        return set(g.replace(",", " ").split()) == set(t.split())
    return g == t


async def run() -> None:
    fields = ["full_name", "document_number", "nationality", "date_of_birth", "expiry_date", "issuing_country"]
    total = correct = 0
    per_field = {f: [0, 0] for f in fields}
    for gt in SAMPLES:
        png = _render(gt)
        extracted, conf, engine = await ocr.extract(png, "image/png", "passport")
        if engine != "gemini-vision":
            print("No Gemini key configured — set GEMINI_API_KEY to run the live OCR benchmark.")
            return
        if total == 0:
            print(f"  (sample raw dates -> dob={extracted.get('date_of_birth')!r} exp={extracted.get('expiry_date')!r})")
        for f in fields:
            ok = _match(f, extracted.get(f), gt[f])
            total += 1
            correct += ok
            per_field[f][0] += ok
            per_field[f][1] += 1
    print("=== OCR Field-Extraction Benchmark (Gemini Vision) ===")
    print(f"Samples: {len(SAMPLES)}  Engine: gemini-vision")
    for f in fields:
        c, n = per_field[f]
        print(f"  {f:18} {c}/{n} = {c / n:.0%}")
    print(f"OVERALL field accuracy: {correct}/{total} = {correct / total:.1%}")


if __name__ == "__main__":
    asyncio.run(run())
