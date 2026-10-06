"""Document verification schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ExtractedFieldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    field_name: str
    raw_value: str
    normalized_value: str
    issue: str
    suggestion: str
    confidence: float


class AnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    engine: str
    status: str
    overall_confidence: float
    summary: str
    findings: list[dict]
    compliance: dict
    fields: list[ExtractedFieldOut]
    created_at: datetime


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    doc_type: str
    status: str
    display_name: str
    retention_until: datetime
    created_at: datetime


class DocumentDetail(DocumentOut):
    analyses: list[AnalysisOut]
