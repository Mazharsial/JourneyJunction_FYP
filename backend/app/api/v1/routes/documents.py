"""Document verification endpoints (sensitive PII — consent + ownership enforced)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permissions
from app.core.exceptions import AppError
from app.core.rate_limit import RateLimiter
from app.core.rbac import Perms
from app.db.session import get_db
from app.models.user import User
from app.schemas.document import DocumentDetail, DocumentOut
from app.services.documents import document_service

router = APIRouter()
_upload_limit = RateLimiter(max_requests=15, window_seconds=60, scope="upload")


@router.post("", response_model=DocumentDetail, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(_upload_limit)])
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form("passport"),
    consent: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Perms.DOCUMENT_MANAGE)),
):
    data = await file.read()
    document = await document_service.upload_and_analyze(
        db, user_id=user.id, data=data, filename=file.filename or "document",
        content_type=file.content_type or "", doc_type=doc_type, consent=consent,
    )
    return document


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Perms.DOCUMENT_MANAGE)),
):
    return await document_service.list_documents(db, user.id)


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Perms.DOCUMENT_MANAGE)),
):
    document = await document_service.get_owned_document(db, user.id, document_id)
    if not document:
        raise AppError("Document not found.", code="document_not_found", status_code=404)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Perms.DOCUMENT_MANAGE)),
):
    document = await document_service.get_owned_document(db, user.id, document_id)
    if not document:
        raise AppError("Document not found.", code="document_not_found", status_code=404)
    await document_service.delete_document(db, document)
