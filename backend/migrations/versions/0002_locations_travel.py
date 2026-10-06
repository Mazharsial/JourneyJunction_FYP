"""locations & travel schema

Revision ID: 0002_locations_travel
Revises: 0001_initial_auth
Create Date: 2026-10-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.db.types import GUID

revision: str = "0002_locations_travel"
down_revision: Union[str, None] = "0001_initial_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NOW = sa.text("now()")


def _ts() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "currencies",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("code", sa.String(3), nullable=False),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("symbol", sa.String(8), nullable=False, server_default=""),
        *_ts(),
        sa.UniqueConstraint("code", name="uq_currencies_code"),
    )
    op.create_index("ix_currencies_code", "currencies", ["code"])

    op.create_table(
        "countries",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("iso2", sa.String(2), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default=""),
        sa.Column("phone_code", sa.String(8), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_ts(),
        sa.UniqueConstraint("iso2", name="uq_countries_iso2"),
    )
    op.create_index("ix_countries_iso2", "countries", ["iso2"])

    op.create_table(
        "cities",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("country_iso2", sa.String(2), sa.ForeignKey("countries.iso2", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("iata_code", sa.String(4), nullable=False, server_default=""),
        sa.Column("timezone", sa.String(60), nullable=False, server_default=""),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_ts(),
        sa.UniqueConstraint("country_iso2", "name", name="uq_city_country_name"),
    )
    op.create_index("ix_cities_country_iso2", "cities", ["country_iso2"])
    op.create_index("ix_cities_name", "cities", ["name"])
    op.create_index("ix_cities_iata_code", "cities", ["iata_code"])

    op.create_table(
        "visa_rules",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("origin_iso2", sa.String(2), nullable=False),
        sa.Column("destination_iso2", sa.String(2), nullable=False),
        sa.Column("requirement", sa.String(30), nullable=False),
        sa.Column("allowed_stay_days", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(500), nullable=False, server_default=""),
        sa.Column("source", sa.String(200), nullable=False, server_default=""),
        *_ts(),
        sa.UniqueConstraint("origin_iso2", "destination_iso2", name="uq_visa_origin_dest"),
    )
    op.create_index("ix_visa_rules_origin_iso2", "visa_rules", ["origin_iso2"])
    op.create_index("ix_visa_rules_destination_iso2", "visa_rules", ["destination_iso2"])

    op.create_table(
        "app_config",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.JSON(), nullable=True),
        *_ts(),
        sa.UniqueConstraint("key", name="uq_app_config_key"),
    )
    op.create_index("ix_app_config_key", "app_config", ["key"])

    op.create_table(
        "trips",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("user_id", GUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("origin_city_id", GUID(), sa.ForeignKey("cities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("destination_city_id", GUID(), sa.ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("budget_tier", sa.String(10), nullable=False, server_default="medium"),
        sa.Column("travelers", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("title", sa.String(160), nullable=False, server_default=""),
        *_ts(),
    )
    op.create_index("ix_trips_user_id", "trips", ["user_id"])

    op.create_table(
        "trip_items",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("trip_id", GUID(), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_type", sa.String(10), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False, server_default="mock"),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column("price_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("price_currency", sa.String(3), nullable=False, server_default="AED"),
        sa.Column("selected", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_ts(),
    )
    op.create_index("ix_trip_items_trip_id", "trip_items", ["trip_id"])


def downgrade() -> None:
    for name in ("trip_items", "trips", "app_config", "visa_rules", "cities", "countries", "currencies"):
        op.drop_table(name)
