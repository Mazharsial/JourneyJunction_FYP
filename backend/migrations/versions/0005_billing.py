"""billing: plans, features, subscriptions, usage, payments

Revision ID: 0005_billing
Revises: 0004_documents
Create Date: 2026-10-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.db.types import GUID

revision: str = "0005_billing"
down_revision: Union[str, None] = "0004_documents"
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
        "plans",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("description", sa.String(255), nullable=False, server_default=""),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("interval", sa.String(10), nullable=False, server_default="month"),
        sa.Column("stripe_product_id", sa.String(80), nullable=False, server_default=""),
        sa.Column("stripe_price_id", sa.String(80), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        *_ts(),
        sa.UniqueConstraint("code", name="uq_plans_code"),
    )
    op.create_index("ix_plans_code", "plans", ["code"])

    op.create_table(
        "plan_features",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("plan_id", GUID(), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("feature_key", sa.String(50), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("limit_value", sa.Integer(), nullable=False, server_default="-1"),
        *_ts(),
        sa.UniqueConstraint("plan_id", "feature_key", name="uq_plan_feature"),
    )
    op.create_index("ix_plan_features_plan_id", "plan_features", ["plan_id"])

    op.create_table(
        "subscriptions",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", GUID(), sa.ForeignKey("plans.id", ondelete="SET NULL"), nullable=True),
        sa.Column("stripe_customer_id", sa.String(80), nullable=False, server_default=""),
        sa.Column("stripe_subscription_id", sa.String(80), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        *_ts(),
        sa.UniqueConstraint("user_id", name="uq_subscriptions_user"),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_index("ix_subscriptions_stripe_customer_id", "subscriptions", ["stripe_customer_id"])
    op.create_index("ix_subscriptions_stripe_subscription_id", "subscriptions", ["stripe_subscription_id"])

    op.create_table(
        "usage_counters",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("feature_key", sa.String(50), nullable=False),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
        *_ts(),
        sa.UniqueConstraint("user_id", "feature_key", "period", name="uq_usage"),
    )
    op.create_index("ix_usage_counters_user_id", "usage_counters", ["user_id"])

    op.create_table(
        "payments",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("stripe_invoice_id", sa.String(80), nullable=False, server_default=""),
        sa.Column("amount_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(20), nullable=False, server_default=""),
        *_ts(),
    )
    op.create_index("ix_payments_user_id", "payments", ["user_id"])
    op.create_index("ix_payments_stripe_invoice_id", "payments", ["stripe_invoice_id"])


def downgrade() -> None:
    for name in ("payments", "usage_counters", "subscriptions", "plan_features", "plans"):
        op.drop_table(name)
