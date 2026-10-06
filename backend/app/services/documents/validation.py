"""
Rule-based verification of extracted document fields.

Detects: missing required fields, invalid/misformatted dates, expired or
soon-to-expire documents, future dates of birth, names containing digits
(likely OCR errors), malformed document numbers, and nationality/issuing-country
mismatches. Produces findings (with severity + suggestion) and per-field issues.
"""
from __future__ import annotations

import re
from datetime import date, datetime

REQUIRED = {
    "passport": ["full_name", "document_number", "date_of_birth", "expiry_date", "nationality", "issuing_country"],
    "id": ["full_name", "document_number", "date_of_birth"],
    "visa": ["full_name", "document_number", "expiry_date"],
    "ticket": ["full_name"],
    "other": ["full_name"],
}

_DOC_NUM_RE = re.compile(r"^[A-Za-z0-9]{5,15}$")
_LABELS = {
    "document_type": "Document type", "full_name": "Full name",
    "document_number": "Document number", "nationality": "Nationality",
    "date_of_birth": "Date of birth", "expiry_date": "Expiry date",
    "issuing_country": "Issuing country",
}


def _parse_date(v):
    try:
        return datetime.strptime(str(v), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def validate(doc_type: str, fields: dict) -> tuple[list[dict], dict]:
    """Return (findings, per_field_issues) where per_field_issues[name]=(issue, suggestion)."""
    findings: list[dict] = []
    issues: dict[str, tuple[str, str]] = {}

    def add(field, code, severity, message, suggestion=""):
        findings.append({"field": field, "code": code, "severity": severity,
                         "message": message, "suggestion": suggestion})
        if field:
            issues[field] = (message, suggestion)

    required = REQUIRED.get(doc_type, REQUIRED["other"])
    for f in required:
        if not fields.get(f):
            add(f, "missing_field", "error",
                f"{_LABELS.get(f, f)} is missing or could not be read.",
                f"Add the {_LABELS.get(f, f).lower()} to the document or re-scan more clearly.")

    today = date.today()

    # Dates
    for df in ("date_of_birth", "expiry_date"):
        val = fields.get(df)
        if val:
            parsed = _parse_date(val)
            if parsed is None:
                add(df, "format", "error",
                    f"{_LABELS[df]} '{val}' is not a valid date.", "Use the format YYYY-MM-DD.")
            elif df == "date_of_birth" and parsed > today:
                add(df, "invalid", "error", "Date of birth is in the future.", "Check the date.")
            elif df == "expiry_date":
                if parsed < today:
                    add(df, "expired", "error",
                        f"Document expired on {parsed.isoformat()}.",
                        "Renew the document before travelling.")
                elif (parsed - today).days <= 180:
                    add(df, "expires_soon", "warning",
                        f"Document expires soon ({parsed.isoformat()}).",
                        "Many countries require 6 months validity — consider renewing.")

    # Name sanity
    name = fields.get("full_name")
    if name and re.search(r"\d", str(name)):
        add("full_name", "format", "warning",
            "Name contains digits, which is unusual.", "Verify the name was read correctly.")

    # Document number pattern
    num = fields.get("document_number")
    if num and not _DOC_NUM_RE.match(str(num).replace(" ", "")):
        add("document_number", "format", "warning",
            "Document number format looks unusual.", "Verify the document number.")

    # Nationality vs issuing country (informational)
    nat, iss = fields.get("nationality"), fields.get("issuing_country")
    if nat and iss and str(nat)[:2].upper() != str(iss)[:2].upper():
        add("nationality", "mismatch", "info",
            "Nationality appears to differ from the issuing country.",
            "This can be normal (e.g. residency) — verify if unexpected.")

    return findings, issues


def summarize(findings: list[dict]) -> str:
    errors = sum(1 for f in findings if f["severity"] == "error")
    warnings = sum(1 for f in findings if f["severity"] == "warning")
    if not findings:
        return "No issues detected. The document looks complete."
    parts = []
    if errors:
        parts.append(f"{errors} error{'s' if errors != 1 else ''}")
    if warnings:
        parts.append(f"{warnings} warning{'s' if warnings != 1 else ''}")
    if not parts:
        parts.append(f"{len(findings)} note{'s' if len(findings) != 1 else ''}")
    return "Found " + " and ".join(parts) + " to review before you travel."
