"""country travel requirements

Revision ID: 0008_country_requirements
Revises: 0007_notifications
Create Date: 2026-10-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.db.types import GUID

revision: str = "0008_country_requirements"
down_revision: Union[str, None] = "0007_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NOW = sa.text("now()")


def upgrade() -> None:
    op.create_table(
        "country_requirements",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("destination_iso2", sa.String(2), nullable=False),
        sa.Column("passport_validity_months", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("required_documents", sa.JSON(), nullable=True),
        sa.Column("health", sa.JSON(), nullable=True),
        sa.Column("currency_notes", sa.String(400), nullable=False, server_default=""),
        sa.Column("customs_notes", sa.String(400), nullable=False, server_default=""),
        sa.Column("entry_notes", sa.String(400), nullable=False, server_default=""),
        sa.Column("emergency_number", sa.String(60), nullable=False, server_default=""),
        sa.Column("official_source", sa.String(200), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.UniqueConstraint("destination_iso2", name="uq_country_requirements_dest"),
    )
    op.create_index(
        "ix_country_requirements_destination_iso2",
        "country_requirements",
        ["destination_iso2"],
    )


def downgrade() -> None:
    op.drop_table("country_requirements")
