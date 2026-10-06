"""Document, file, analysis and extracted-field models (sensitive PII)."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import GUID


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    doc_type: Mapped[str] = mapped_column(String(20), default="passport")  # passport|visa|ticket|id|other
    status: Mapped[str] = mapped_column(String(20), default="uploaded")  # uploaded|analyzed|failed
    display_name: Mapped[str] = mapped_column(String(160), default="")
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    retention_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    file: Mapped["DocumentFile"] = relationship(
        back_populates="document", lazy="selectin", cascade="all, delete-orphan", uselist=False
    )
    analyses: Mapped[list["DocumentAnalysis"]] = relationship(
        back_populates="document", lazy="selectin", cascade="all, delete-orphan",
        order_by="DocumentAnalysis.created_at",
    )


class DocumentFile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_files"

    document_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    storage_path: Mapped[str] = mapped_column(String(300), nullable=False)  # relative, encrypted blob
    mime: Mapped[str] = mapped_column(String(60), default="")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    sha256: Mapped[str] = mapped_column(String(64), default="")  # of plaintext
    encrypted: Mapped[bool] = mapped_column(Boolean, default=True)

    document: Mapped[Document] = relationship(back_populates="file")


class DocumentAnalysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_analyses"

    document_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    engine: Mapped[str] = mapped_column(String(30), default="")  # gemini-vision | mock
    status: Mapped[str] = mapped_column(String(20), default="ok")  # ok | error
    overall_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    summary: Mapped[str] = mapped_column(Text, default="")
    findings: Mapped[list] = mapped_column(JSON, default=list)       # [{field,code,severity,message,suggestion}]
    compliance: Mapped[dict] = mapped_column(JSON, default=dict)     # {requirement,notes,...}

    document: Mapped[Document] = relationship(back_populates="analyses")
    fields: Mapped[list["ExtractedField"]] = relationship(
        back_populates="analysis", lazy="selectin", cascade="all, delete-orphan"
    )


class ExtractedField(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "extracted_fields"

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("document_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_name: Mapped[str] = mapped_column(String(60), nullable=False)
    raw_value: Mapped[str] = mapped_column(String(300), default="")
    normalized_value: Mapped[str] = mapped_column(String(300), default="")
    issue: Mapped[str] = mapped_column(String(200), default="")
    suggestion: Mapped[str] = mapped_column(String(300), default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    analysis: Mapped[DocumentAnalysis] = relationship(back_populates="fields")
