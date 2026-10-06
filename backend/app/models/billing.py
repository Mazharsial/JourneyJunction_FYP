"""Billing models: plans, feature entitlements, subscriptions, usage, payments."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import GUID


class Plan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "plans"

    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)  # free|pro|business
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="")
    price_cents: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    interval: Mapped[str] = mapped_column(String(10), default="month")
    stripe_product_id: Mapped[str] = mapped_column(String(80), default="")
    stripe_price_id: Mapped[str] = mapped_column(String(80), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    features: Mapped[list["PlanFeature"]] = relationship(
        back_populates="plan", lazy="selectin", cascade="all, delete-orphan"
    )


class PlanFeature(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "plan_features"
    __table_args__ = (UniqueConstraint("plan_id", "feature_key", name="uq_plan_feature"),)

    plan_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    feature_key: Mapped[str] = mapped_column(String(50), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    limit_value: Mapped[int] = mapped_column(Integer, default=-1)  # -1 = unlimited; 0 = disabled

    plan: Mapped[Plan] = relationship(back_populates="features")


class Subscription(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    plan_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("plans.id", ondelete="SET NULL"), nullable=True
    )
    stripe_customer_id: Mapped[str] = mapped_column(String(80), default="", index=True)
    stripe_subscription_id: Mapped[str] = mapped_column(String(80), default="", index=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active|past_due|canceled|incomplete
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    plan: Mapped[Plan | None] = relationship(lazy="selectin")


class UsageCounter(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "usage_counters"
    __table_args__ = (UniqueConstraint("user_id", "feature_key", "period", name="uq_usage"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    feature_key: Mapped[str] = mapped_column(String(50), nullable=False)
    period: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    count: Mapped[int] = mapped_column(Integer, default=0)


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payments"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    stripe_invoice_id: Mapped[str] = mapped_column(String(80), default="", index=True)
    amount_cents: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[str] = mapped_column(String(20), default="")  # paid|failed
