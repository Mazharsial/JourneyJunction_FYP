"""Trip & trip-item models."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import JSON, Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import GUID


class Trip(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trips"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    origin_city_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("cities.id", ondelete="SET NULL"), nullable=True
    )
    destination_city_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    budget_tier: Mapped[str] = mapped_column(String(10), default="medium")  # low|medium|luxury
    purpose: Mapped[str] = mapped_column(String(20), default="tourism")  # tourism|umrah|hajj
    travelers: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft|planned
    title: Mapped[str] = mapped_column(String(160), default="")

    items: Mapped[list["TripItem"]] = relationship(
        back_populates="trip", lazy="selectin", cascade="all, delete-orphan"
    )


class TripItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trip_items"

    trip_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_type: Mapped[str] = mapped_column(String(10), nullable=False)  # flight|hotel
    provider: Mapped[str] = mapped_column(String(30), default="mock")
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    price_amount: Mapped[float] = mapped_column(Float, default=0.0)
    price_currency: Mapped[str] = mapped_column(String(3), default="AED")
    selected: Mapped[bool] = mapped_column(Boolean, default=True)

    trip: Mapped[Trip] = relationship(back_populates="items")
