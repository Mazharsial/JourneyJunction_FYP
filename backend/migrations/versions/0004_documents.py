"""document verification schema

Revision ID: 0004_documents
Revises: 0003_chat_ai
Create Date: 2026-10-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.db.types import GUID

revision: str = "0004_documents"
down_revision: Union[str, None] = "0003_chat_ai"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NOW = sa.text("now()")


def _ts():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("doc_type", sa.String(20), nullable=False, server_default="passport"),
        sa.Column("status", sa.String(20), nullable=False, server_default="uploaded"),
        sa.Column("display_name", sa.String(160), nullable=False, server_default=""),
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retention_until", sa.DateTime(timezone=True), nullable=False),
        *_ts(),
    )
    op.create_index("ix_documents_user_id", "documents", ["user_id"])

    op.create_table(
        "document_files",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("document_id", GUID(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("storage_path", sa.String(300), nullable=False),
        sa.Column("mime", sa.String(60), nullable=False, server_default=""),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sha256", sa.String(64), nullable=False, server_default=""),
        sa.Column("encrypted", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_ts(),
    )
    op.create_index("ix_document_files_document_id", "document_files", ["document_id"])

    op.create_table(
        "document_analyses",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("document_id", GUID(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("engine", sa.String(30), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="ok"),
        sa.Column("overall_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("findings", sa.JSON(), nullable=True),
        sa.Column("compliance", sa.JSON(), nullable=True),
        *_ts(),
    )
    op.create_index("ix_document_analyses_document_id", "document_analyses", ["document_id"])

    op.create_table(
        "extracted_fields",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("analysis_id", GUID(), sa.ForeignKey("document_analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field_name", sa.String(60), nullable=False),
        sa.Column("raw_value", sa.String(300), nullable=False, server_default=""),
        sa.Column("normalized_value", sa.String(300), nullable=False, server_default=""),
        sa.Column("issue", sa.String(200), nullable=False, server_default=""),
        sa.Column("suggestion", sa.String(300), nullable=False, server_default=""),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        *_ts(),
    )
    op.create_index("ix_extracted_fields_analysis_id", "extracted_fields", ["analysis_id"])


def downgrade() -> None:
    for name in ("extracted_fields", "document_analyses", "document_files", "documents"):
        op.drop_table(name)
