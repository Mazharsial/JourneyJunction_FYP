"""pilgrimage support: trip purpose + purpose-keyed country requirements

Revision ID: 0009_pilgrimage_support
Revises: 0008_country_requirements
Create Date: 2026-10-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_pilgrimage_support"
down_revision: Union[str, None] = "0008_country_requirements"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "trips",
        sa.Column("purpose", sa.String(20), nullable=False, server_default="tourism"),
    )
    # country_requirements: add purpose and widen the unique key to (dest, purpose)
    with op.batch_alter_table("country_requirements") as batch:
        batch.add_column(
            sa.Column("purpose", sa.String(20), nullable=False, server_default="tourism")
        )
        batch.drop_constraint("uq_country_requirements_dest", type_="unique")
        batch.create_unique_constraint(
            "uq_country_req_dest_purpose", ["destination_iso2", "purpose"]
        )


def downgrade() -> None:
    with op.batch_alter_table("country_requirements") as batch:
        batch.drop_constraint("uq_country_req_dest_purpose", type_="unique")
        batch.create_unique_constraint(
            "uq_country_requirements_dest", ["destination_iso2"]
        )
        batch.drop_column("purpose")
    op.drop_column("trips", "purpose")
