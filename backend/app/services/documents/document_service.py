"""Document verification orchestration."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.document import (
    Document,
    DocumentAnalysis,
    DocumentFile,
    ExtractedField,
)
from app.services import location_service
from app.services.documents import ocr, storage, upload_security, validation

logger = get_logger("documents")

_VALID_TYPES = {"passport", "visa", "ticket", "id", "other"}

_NAT_TO_ISO2 = {
    "PAK": "PK", "PK": "PK", "PAKISTANI": "PK", "PAKISTAN": "PK",
    "GBR": "GB", "GB": "GB", "BRITISH": "GB", "UK": "GB",
    "USA": "US", "US": "US", "AMERICAN": "US",
    "ARE": "AE", "AE": "AE", "EMIRATI": "AE",
    "SAU": "SA", "SA": "SA", "SAUDI": "SA",
    "TUR": "TR", "TR": "TR", "TURKISH": "TR",
    "FRA": "FR", "FR": "FR", "FRENCH": "FR",
}


def _nat_to_iso2(nationality: str | None) -> str | None:
    if not nationality:
        return None
    return _NAT_TO_ISO2.get(str(nationality).strip().upper())


def _sanitize_display_name(filename: str) -> str:
    base = (filename or "document").replace("\\", "/").split("/")[-1]
    return base[:160] or "document"


async def upload_and_analyze(
    session: AsyncSession, *, user_id: uuid.UUID, data: bytes, filename: str,
    content_type: str, doc_type: str, consent: bool,
) -> Document:
    from app.core.exceptions import AppError

    if not consent:
        raise AppError(
            "Consent is required to process your document.", code="consent_required", status_code=422
        )
    if doc_type not in _VALID_TYPES:
        doc_type = "other"

    mime = upload_security.validate_upload(filename, content_type, data)

    # Server-side entitlement enforcement (monthly OCR document limit by plan).
    from app.core.entitlements import Features
    from app.services.billing import entitlement_service
    await entitlement_service.consume(session, user_id, Features.OCR_DOCUMENTS)

    rel_path, sha = storage.save_encrypted(data)

    settings = get_settings()
    now = datetime.now(timezone.utc)
    document = Document(
        user_id=user_id, doc_type=doc_type, status="uploaded",
        display_name=_sanitize_display_name(filename), consent_at=now,
        retention_until=now + timedelta(days=settings.document_retention_days),
        analyses=[],
    )
    document.file = DocumentFile(
        storage_path=rel_path, mime=mime, size_bytes=len(data), sha256=sha, encrypted=True
    )
    session.add(document)
    await session.flush()

    # ---- analyze ----
    fields, confidence, engine = await ocr.extract(data, mime, doc_type)
    findings, issues = validation.validate(doc_type, fields)
    compliance = await _compliance(session, fields)

    analysis = DocumentAnalysis(
        document_id=document.id, engine=engine, status="ok",
        overall_confidence=confidence, summary=validation.summarize(findings),
        findings=findings, compliance=compliance, fields=[],
    )
    for name in ocr.FIELDS:
        raw = fields.get(name)
        issue, suggestion = issues.get(name, ("", ""))
        analysis.fields.append(ExtractedField(
            field_name=name, raw_value="" if raw is None else str(raw)[:300],
            normalized_value="" if raw is None else str(raw)[:300],
            issue=issue[:200], suggestion=suggestion[:300], confidence=confidence,
        ))
    document.analyses.append(analysis)
    document.status = "analyzed"
    await session.flush()
    logger.info("document_analyzed", document_id=str(document.id), engine=engine,
                findings=len(findings))
    return document


async def _compliance(session: AsyncSession, fields: dict) -> dict:
    nat_iso2 = _nat_to_iso2(fields.get("nationality"))
    market = await location_service.get_default_market(session)
    dest = (market or {}).get("country") or get_settings().default_country
    if not nat_iso2 or nat_iso2 == dest:
        return {}
    rule = await location_service.get_visa_rule(session, nat_iso2, dest)
    if not rule:
        return {}
    return {
        "origin": nat_iso2, "destination": dest,
        "requirement": rule.requirement, "allowed_stay_days": rule.allowed_stay_days,
        "notes": rule.notes,
        "disclaimer": "Informational only — confirm with the official embassy/government source.",
    }


async def list_documents(session: AsyncSession, user_id: uuid.UUID) -> list[Document]:
    return list(
        (await session.scalars(
            select(Document).where(Document.user_id == user_id).order_by(Document.created_at.desc())
        )).all()
    )


async def get_owned_document(session: AsyncSession, user_id: uuid.UUID, doc_id: uuid.UUID) -> Document | None:
    return await session.scalar(
        select(Document).where(Document.id == doc_id, Document.user_id == user_id)
    )


async def delete_document(session: AsyncSession, document: Document) -> None:
    if document.file:
        storage.delete_file(document.file.storage_path)
    await session.delete(document)
    await session.flush()
