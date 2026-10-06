"""Chatbot conversation, message and AI-usage models."""
from __future__ import annotations

import uuid

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import GUID


class ChatConversation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(160), default="New conversation")

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="conversation", lazy="selectin",
        cascade="all, delete-orphan", order_by="ChatMessage.created_at",
    )


class ChatMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("chat_conversations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    role: Mapped[str] = mapped_column(String(12), nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)

    conversation: Mapped[ChatConversation] = relationship(back_populates="messages")


class AIRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """AI usage/cost tracking (no secrets, no raw content)."""

    __tablename__ = "ai_requests"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    kind: Mapped[str] = mapped_column(String(30), default="chat")
    provider: Mapped[str] = mapped_column(String(20), default="gemini")
    model: Mapped[str] = mapped_column(String(60), default="")
    status: Mapped[str] = mapped_column(String(20), default="ok")  # ok | fallback | error
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    prompt_chars: Mapped[int] = mapped_column(Integer, default=0)
    response_chars: Mapped[int] = mapped_column(Integer, default=0)
