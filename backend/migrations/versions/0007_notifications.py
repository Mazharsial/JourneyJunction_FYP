"""notifications + user notification profile

Revision ID: 0007_notifications
Revises: 0006_audit_logs
Create Date: 2026-10-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.db.types import GUID

revision: str = "0007_notifications"
down_revision: Union[str, None] = "0006_audit_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone_number", sa.String(32), nullable=False, server_default=""))
    op.add_column("users", sa.Column("whatsapp_opt_in", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("email_opt_in", sa.Boolean(), nullable=False, server_default=sa.text("true")))

    op.create_table(
        "notifications",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("channel", sa.String(12), nullable=False),
        sa.Column("event", sa.String(50), nullable=False, server_default=""),
        sa.Column("recipient", sa.String(120), nullable=False, server_default=""),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("provider", sa.String(20), nullable=False, server_default=""),
        sa.Column("status", sa.String(12), nullable=False, server_default=""),
        sa.Column("error", sa.String(300), nullable=False, server_default=""),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_column("users", "email_opt_in")
    op.drop_column("users", "whatsapp_opt_in")
    op.drop_column("users", "phone_number")
