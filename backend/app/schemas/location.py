"""Location & configuration schemas."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class CurrencyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    code: str
    name: str
    symbol: str


class CountryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    iso2: str
    name: str
    currency_code: str
    phone_code: str


class CityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    country_iso2: str
    name: str
    iata_code: str
    timezone: str


class VisaRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    origin_iso2: str
    destination_iso2: str
    requirement: str
    allowed_stay_days: int | None
    notes: str
    source: str


class VisaResponse(BaseModel):
    found: bool
    rule: VisaRuleOut | None = None
    disclaimer: str = (
        "Visa guidance is informational only and may change. Always confirm with "
        "the official embassy or government source before travelling."
    )
