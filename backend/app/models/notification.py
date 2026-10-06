"""Notification delivery log (WhatsApp / email)."""
from __future__ import annotations

import uuid

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import GUID


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    channel: Mapped[str] = mapped_column(String(12), nullable=False)   # whatsapp | email
    event: Mapped[str] = mapped_column(String(50), default="")
    recipient: Mapped[str] = mapped_column(String(120), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    provider: Mapped[str] = mapped_column(String(20), default="")      # whatsapp | klaviyo | mock
    status: Mapped[str] = mapped_column(String(12), default="")        # sent | failed | mock | skipped
    error: Mapped[str] = mapped_column(String(300), default="")
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
