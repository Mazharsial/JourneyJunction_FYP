"""Travel (flights, hotels, trips, itinerary) schemas."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

BudgetTier = Literal["low", "medium", "luxury"]


class FlightOffer(BaseModel):
    provider: str
    airline: str
    flight_number: str
    origin_iata: str
    destination_iata: str
    depart_time: str
    arrive_time: str
    duration_minutes: int
    stops: int
    cabin: str
    price_amount: float
    price_currency: str


class HotelOffer(BaseModel):
    provider: str
    name: str
    rating: float
    address: str
    amenities: list[str]
    nights: int
    price_per_night: float
    total_amount: float
    price_currency: str


class FlightSearchResponse(BaseModel):
    origin: str
    destination: str
    date: date
    budget_tier: BudgetTier
    currency: str
    offers: list[FlightOffer]


class HotelSearchResponse(BaseModel):
    city: str
    checkin: date
    checkout: date
    nights: int
    budget_tier: BudgetTier
    currency: str
    offers: list[HotelOffer]


class TripCreate(BaseModel):
    destination_city_id: uuid.UUID
    origin_city_id: uuid.UUID | None = None
    start_date: date
    end_date: date
    budget_tier: BudgetTier = "medium"
    travelers: int = Field(default=1, ge=1, le=20)
    title: str = Field(default="", max_length=160)


class TripItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    item_type: str
    provider: str
    data: dict
    price_amount: float
    price_currency: str
    selected: bool


class CityRef(BaseModel):
    id: uuid.UUID
    name: str
    iata_code: str
    country_iso2: str


class TripOut(BaseModel):
    id: uuid.UUID
    title: str
    destination: CityRef
    origin: CityRef | None
    start_date: date
    end_date: date
    budget_tier: str
    travelers: int
    status: str
    created_at: datetime
    items: list[TripItemOut] = []


class ItineraryDay(BaseModel):
    day_number: int
    date: date
    title: str
    notes: str


class VisaInfo(BaseModel):
    requirement: str
    allowed_stay_days: int | None
    notes: str
    disclaimer: str = (
        "Visa guidance is informational only and may change. Confirm with the "
        "official embassy or government source before travelling."
    )


class RequiredDocument(BaseModel):
    """A document the traveller must carry, plus the compliance status derived
    from the user's own verified documents."""
    label: str
    doc_type: str | None = None  # passport|visa|ticket|id — None = informational
    # verified | not_verified | informational
    status: Literal["verified", "not_verified", "informational"] = "informational"


class TravelRequirements(BaseModel):
    destination_country: str
    destination_iso2: str
    passport_validity_months: int
    visa: VisaInfo | None = None
    required_documents: list[RequiredDocument] = []
    documents_ready: int = 0        # verified count among verifiable docs
    documents_required: int = 0     # total verifiable docs (passport/visa/ticket/id)
    health: list[str] = []
    currency_notes: str = ""
    customs_notes: str = ""
    entry_notes: str = ""
    emergency_number: str = ""
    official_source: str = ""
    disclaimer: str = (
        "Travel requirements are informational only and change frequently. "
        "Always confirm with the official embassy or government source before you travel."
    )


class TripDetail(BaseModel):
    trip: TripOut
    itinerary: list[ItineraryDay]
    suggested_flights: list[FlightOffer]
    suggested_hotels: list[HotelOffer]
    visa: VisaInfo | None = None
    requirements: TravelRequirements | None = None
