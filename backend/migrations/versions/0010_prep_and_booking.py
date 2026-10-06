"""country requirement preparation steps

Revision ID: 0010_prep_and_booking
Revises: 0009_pilgrimage_support
Create Date: 2026-10-06

Booking URLs on flight/hotel offers are response-only (not persisted), so this
migration only adds the preparation-guide column.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010_prep_and_booking"
down_revision: Union[str, None] = "0009_pilgrimage_support"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("country_requirements", sa.Column("preparation", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("country_requirements", "preparation")
