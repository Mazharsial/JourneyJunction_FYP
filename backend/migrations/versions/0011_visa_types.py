"""country requirement visa types

Revision ID: 0011_visa_types
Revises: 0010_prep_and_booking
Create Date: 2026-10-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011_visa_types"
down_revision: Union[str, None] = "0010_prep_and_booking"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("country_requirements", sa.Column("visa_types", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("country_requirements", "visa_types")
