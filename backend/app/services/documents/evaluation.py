"""
Document-verification (validation-layer) evaluation.

Measures how reliably the rule-based verifier flags the right issues on a
labelled dataset of field sets with known defects. Deterministic and offline
(no OCR), so it runs in CI and gates the >= 90% target. OCR field-extraction
accuracy is measured separately (live) by `ocr_benchmark.py`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from app.services.documents import validation


@dataclass
class Case:
    name: str
    doc_type: str
    fields: dict
    expected_codes: set = field(default_factory=set)


def _base() -> dict:
    return {
        "document_type": "passport", "full_name": "JOHN DOE",
        "document_number": "P1234567", "nationality": "GB",
        "date_of_birth": "1990-05-14", "expiry_date": "2035-01-01",
        "issuing_country": "GB",
    }


def _dataset() -> list[Case]:
    soon = (date.today() + timedelta(days=90)).isoformat()
    future_dob = (date.today() + timedelta(days=365)).isoformat()
    cases = [
        Case("valid passport", "passport", _base(), set()),
        Case("expired", "passport", {**_base(), "expiry_date": "2020-01-01"}, {"expired"}),
        Case("expires soon", "passport", {**_base(), "expiry_date": soon}, {"expires_soon"}),
        Case("missing nationality", "passport", {**_base(), "nationality": None}, {"missing_field"}),
        Case("bad dob format", "passport", {**_base(), "date_of_birth": "14/05/1990"}, {"format"}),
        Case("name with digits", "passport", {**_base(), "full_name": "JOHN D0E"}, {"format"}),
        Case("future dob", "passport", {**_base(), "date_of_birth": future_dob}, {"invalid"}),
        Case("nationality mismatch", "passport", {**_base(), "issuing_country": "FR"}, {"mismatch"}),
        Case("bad doc number", "passport", {**_base(), "document_number": "X"}, {"format"}),
        Case("visa missing expiry", "visa",
             {"full_name": "A B", "document_number": "V123456", "expiry_date": None}, {"missing_field"}),
        Case("valid ticket", "ticket", {"full_name": "A B"}, set()),
        Case("valid id", "id",
             {"full_name": "A B", "document_number": "ID123456", "date_of_birth": "1992-02-02"}, set()),
    ]
    return cases


def evaluate_validation() -> dict:
    cases = _dataset()
    failures = []
    for c in cases:
        findings, _ = validation.validate(c.doc_type, c.fields)
        codes = {f["code"] for f in findings}
        if codes != c.expected_codes:
            failures.append({"case": c.name, "expected": sorted(c.expected_codes), "got": sorted(codes)})
    total = len(cases)
    correct = total - len(failures)
    return {"total": total, "correct": correct, "accuracy": correct / total, "failures": failures}


if __name__ == "__main__":
    r = evaluate_validation()
    print("=== Document Verification (validation layer) ===")
    print(f"Accuracy: {r['correct']}/{r['total']} = {r['accuracy']:.1%}")
    for f in r["failures"]:
        print("  MISS:", f)
