"""chat & AI usage schema

Revision ID: 0003_chat_ai
Revises: 0002_locations_travel
Create Date: 2026-10-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.db.types import GUID

revision: str = "0003_chat_ai"
down_revision: Union[str, None] = "0002_locations_travel"
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
        "chat_conversations",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(160), nullable=False, server_default="New conversation"),
        *_ts(),
    )
    op.create_index("ix_chat_conversations_user_id", "chat_conversations", ["user_id"])

    op.create_table(
        "chat_messages",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("conversation_id", GUID(), sa.ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(12), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("meta", sa.JSON(), nullable=True),
        *_ts(),
    )
    op.create_index("ix_chat_messages_conversation_id", "chat_messages", ["conversation_id"])

    op.create_table(
        "ai_requests",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("kind", sa.String(30), nullable=False, server_default="chat"),
        sa.Column("provider", sa.String(20), nullable=False, server_default="gemini"),
        sa.Column("model", sa.String(60), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="ok"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("prompt_chars", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("response_chars", sa.Integer(), nullable=False, server_default="0"),
        *_ts(),
    )
    op.create_index("ix_ai_requests_user_id", "ai_requests", ["user_id"])


def downgrade() -> None:
    for name in ("ai_requests", "chat_messages", "chat_conversations"):
        op.drop_table(name)
