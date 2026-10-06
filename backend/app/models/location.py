"""Geographic & configuration models (Dubai-first, fully data-driven)."""
from __future__ import annotations

from sqlalchemy import JSON, Boolean, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Currency(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "currencies"

    code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    symbol: Mapped[str] = mapped_column(String(8), default="")


class Country(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "countries"

    iso2: Mapped[str] = mapped_column(String(2), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), default="")
    phone_code: Mapped[str] = mapped_column(String(8), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class City(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cities"
    __table_args__ = (UniqueConstraint("country_iso2", "name", name="uq_city_country_name"),)

    country_iso2: Mapped[str] = mapped_column(
        String(2), ForeignKey("countries.iso2", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    iata_code: Mapped[str] = mapped_column(String(4), default="", index=True)  # primary airport
    timezone: Mapped[str] = mapped_column(String(60), default="")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class VisaRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Informational visa guidance (NOT legal advice). origin/destination = ISO2."""

    __tablename__ = "visa_rules"
    __table_args__ = (
        UniqueConstraint("origin_iso2", "destination_iso2", name="uq_visa_origin_dest"),
    )

    origin_iso2: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    destination_iso2: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    # visa_free | visa_on_arrival | e_visa | visa_required
    requirement: Mapped[str] = mapped_column(String(30), nullable=False)
    allowed_stay_days: Mapped[int | None] = mapped_column(nullable=True)
    notes: Mapped[str] = mapped_column(String(500), default="")
    source: Mapped[str] = mapped_column(String(200), default="")


class CountryRequirement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Destination entry / travel requirements (informational, data-driven).

    Powers the "Travel requirements for <country>" section and the document
    compliance check. destination_iso2 = ISO2 of the country being entered.
    """

    __tablename__ = "country_requirements"
    __table_args__ = (
        UniqueConstraint("destination_iso2", "purpose", name="uq_country_req_dest_purpose"),
    )

    destination_iso2: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    # tourism | umrah | hajj — lets one country carry pilgrimage-specific rules
    purpose: Mapped[str] = mapped_column(String(20), default="tourism", nullable=False)
    passport_validity_months: Mapped[int] = mapped_column(default=6)
    # list[str] — each entry is a required document the traveller must carry
    required_documents: Mapped[list] = mapped_column(JSON, default=list)
    health: Mapped[list] = mapped_column(JSON, default=list)        # list[str]
    currency_notes: Mapped[str] = mapped_column(String(400), default="")
    customs_notes: Mapped[str] = mapped_column(String(400), default="")
    entry_notes: Mapped[str] = mapped_column(String(400), default="")
    emergency_number: Mapped[str] = mapped_column(String(60), default="")
    official_source: Mapped[str] = mapped_column(String(200), default="")


class AppConfig(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Runtime-tunable key/value configuration."""

    __tablename__ = "app_config"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)
