"""Travel business logic: search, trips, itinerary."""
from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.models.document import Document
from app.models.location import City, Country
from app.models.travel import Trip
from app.schemas.travel import (
    CityRef,
    FlightOffer,
    HotelOffer,
    ItineraryDay,
    RequiredDocument,
    TravelRequirements,
    TripCreate,
    TripItemOut,
    TripOut,
    VisaInfo,
)
from app.services import location_service
from app.services.providers import get_flight_provider, get_hotel_provider
from app.services.providers.mock import MockFlightProvider, MockHotelProvider

logger = get_logger("travel")
_VALID_TIERS = {"low", "medium", "luxury"}
_VALID_PURPOSES = {"tourism", "umrah", "hajj"}
_PURPOSE_LABEL = {"tourism": "Trip", "umrah": "Umrah", "hajj": "Hajj"}


async def _currency_for_city(session: AsyncSession, city: City) -> str:
    country = await session.scalar(select(Country).where(Country.iso2 == city.country_iso2))
    if country and country.currency_code:
        return country.currency_code
    return get_settings().default_currency


# ---- search ----
async def search_flights(*, origin_iata, destination_iata, depart_date, budget_tier,
                         travelers, currency) -> list[FlightOffer]:
    provider = get_flight_provider()
    try:
        return await provider.search_flights(
            origin_iata=origin_iata, destination_iata=destination_iata,
            depart_date=depart_date, budget_tier=budget_tier, travelers=travelers,
            currency=currency,
        )
    except Exception as exc:  # live provider failure -> graceful mock fallback
        logger.warning("flight_provider_fallback", provider=provider.name, error=str(exc))
        return await MockFlightProvider().search_flights(
            origin_iata=origin_iata, destination_iata=destination_iata,
            depart_date=depart_date, budget_tier=budget_tier, travelers=travelers,
            currency=currency,
        )


async def search_hotels(*, city_name, city_iata, checkin, checkout, budget_tier,
                        travelers, currency) -> list[HotelOffer]:
    provider = get_hotel_provider()
    try:
        return await provider.search_hotels(
            city_name=city_name, city_iata=city_iata, checkin=checkin, checkout=checkout,
            budget_tier=budget_tier, travelers=travelers, currency=currency,
        )
    except Exception as exc:
        logger.warning("hotel_provider_fallback", provider=provider.name, error=str(exc))
        return await MockHotelProvider().search_hotels(
            city_name=city_name, city_iata=city_iata, checkin=checkin, checkout=checkout,
            budget_tier=budget_tier, travelers=travelers, currency=currency,
        )


# ---- trips ----
def _validate(data: TripCreate) -> None:
    if data.budget_tier not in _VALID_TIERS:
        raise AppError("Invalid budget tier.", code="invalid_budget", status_code=422)
    if data.purpose not in _VALID_PURPOSES:
        raise AppError("Invalid trip purpose.", code="invalid_purpose", status_code=422)
    if data.end_date < data.start_date:
        raise AppError("End date must be on or after the start date.", code="invalid_dates", status_code=422)
    if data.start_date < date.today():
        raise AppError("Start date cannot be in the past.", code="invalid_dates", status_code=422)
    if data.origin_city_id and data.origin_city_id == data.destination_city_id:
        raise AppError("Origin and destination must differ.", code="invalid_route", status_code=422)


async def create_trip(session: AsyncSession, user_id: uuid.UUID, data: TripCreate) -> Trip:
    _validate(data)
    dest = await location_service.get_city(session, data.destination_city_id)
    if not dest:
        raise AppError("Destination city not found.", code="city_not_found", status_code=404)
    if data.origin_city_id and not await location_service.get_city(session, data.origin_city_id):
        raise AppError("Origin city not found.", code="city_not_found", status_code=404)
    # Umrah / Hajj are only valid for Saudi destinations.
    if data.purpose in ("umrah", "hajj") and dest.country_iso2 != "SA":
        raise AppError(
            "Umrah and Hajj trips must have a destination in Saudi Arabia "
            "(e.g. Makkah, Madinah or Jeddah).",
            code="invalid_pilgrimage_destination", status_code=422,
        )

    default_title = (
        f"{_PURPOSE_LABEL[data.purpose]} to {dest.name}"
        if data.purpose != "tourism" else f"Trip to {dest.name}"
    )
    trip = Trip(
        user_id=user_id,
        destination_city_id=data.destination_city_id,
        origin_city_id=data.origin_city_id,
        start_date=data.start_date,
        end_date=data.end_date,
        budget_tier=data.budget_tier,
        purpose=data.purpose,
        travelers=data.travelers,
        title=data.title or default_title,
        status="draft",
        items=[],  # initialise collection so async access needs no lazy load
    )
    session.add(trip)
    await session.flush()
    return trip


async def list_trips(session: AsyncSession, user_id: uuid.UUID) -> list[Trip]:
    return list(
        (await session.scalars(
            select(Trip).where(Trip.user_id == user_id).order_by(Trip.created_at.desc())
        )).all()
    )


async def get_owned_trip(session: AsyncSession, user_id: uuid.UUID, trip_id: uuid.UUID) -> Trip | None:
    # Ownership enforced in the query (IDOR-safe); non-owners get None -> 404.
    return await session.scalar(
        select(Trip).where(Trip.id == trip_id, Trip.user_id == user_id)
    )


def build_itinerary(destination_name: str, start: date, end: date) -> list[ItineraryDay]:
    days = (end - start).days + 1
    out: list[ItineraryDay] = []
    for i in range(days):
        d = start + timedelta(days=i)
        if i == 0:
            title, notes = "Arrival & check-in", f"Arrive in {destination_name}, settle into your hotel and explore nearby."
        elif i == days - 1 and days > 1:
            title, notes = "Departure", "Check out and head to the airport."
        else:
            title, notes = f"Explore {destination_name}", "Sightseeing, local experiences and dining."
        out.append(ItineraryDay(day_number=i + 1, date=d, title=title, notes=notes))
    return out


def city_ref(city: City) -> CityRef:
    return CityRef(id=city.id, name=city.name, iata_code=city.iata_code, country_iso2=city.country_iso2)


async def to_trip_out(session: AsyncSession, trip: Trip) -> TripOut:
    dest = await location_service.get_city(session, trip.destination_city_id)
    origin = (
        await location_service.get_city(session, trip.origin_city_id)
        if trip.origin_city_id else None
    )
    return TripOut(
        id=trip.id,
        title=trip.title,
        destination=city_ref(dest),
        origin=city_ref(origin) if origin else None,
        start_date=trip.start_date,
        end_date=trip.end_date,
        budget_tier=trip.budget_tier,
        purpose=trip.purpose,
        travelers=trip.travelers,
        status=trip.status,
        created_at=trip.created_at,
        items=[TripItemOut.model_validate(i) for i in trip.items],
    )


def _doc_type_for(label: str) -> str | None:
    """Map a required-document label to a verifiable document type (or None)."""
    low = label.lower()
    if "passport" in low:
        return "passport"
    if "visa" in low or "nicop" in low or "poc" in low:
        return "visa"
    if "ticket" in low or "flight" in low:
        return "ticket"
    if "national id" in low or "id card" in low or "identity" in low:
        return "id"
    return None


async def _verified_doc_types(session: AsyncSession, user_id: uuid.UUID) -> set[str]:
    """Document types the user has uploaded that passed verification with no errors.

    A document is compliant when its latest analysis reports no error-severity
    findings (expiry, missing fields, bad format). Warnings don't disqualify it.
    """
    docs = (await session.scalars(
        select(Document).where(
            Document.user_id == user_id, Document.status == "analyzed"
        )
    )).all()
    verified: set[str] = set()
    for d in docs:
        if not d.analyses:
            continue
        latest = d.analyses[-1]
        has_error = any(
            (f or {}).get("severity") == "error" for f in (latest.findings or [])
        )
        if not has_error:
            verified.add(d.doc_type)
    return verified


async def build_requirements(
    session: AsyncSession, trip: Trip, dest: City | None, visa: VisaInfo | None
) -> TravelRequirements | None:
    """Assemble destination travel requirements + a document compliance check."""
    if not dest:
        return None
    req = await location_service.get_country_requirement(
        session, dest.country_iso2, trip.purpose
    )
    if not req:
        return None
    country = await location_service.get_country(session, dest.country_iso2)
    verified = await _verified_doc_types(session, trip.user_id)

    documents: list[RequiredDocument] = []
    ready = required = 0
    for label in req.required_documents:
        dtype = _doc_type_for(label)
        if dtype is None:
            documents.append(RequiredDocument(label=label, doc_type=None, status="informational"))
            continue
        required += 1
        is_ok = dtype in verified
        if is_ok:
            ready += 1
        documents.append(RequiredDocument(
            label=label, doc_type=dtype,
            status="verified" if is_ok else "not_verified",
        ))

    return TravelRequirements(
        destination_country=country.name if country else dest.country_iso2,
        destination_iso2=dest.country_iso2,
        purpose=trip.purpose,
        passport_validity_months=req.passport_validity_months,
        visa=visa,
        required_documents=documents,
        documents_ready=ready,
        documents_required=required,
        health=list(req.health or []),
        currency_notes=req.currency_notes,
        customs_notes=req.customs_notes,
        entry_notes=req.entry_notes,
        emergency_number=req.emergency_number,
        official_source=req.official_source,
    )


async def build_detail_parts(session: AsyncSession, trip: Trip):
    """Return (dest, origin, flights, hotels, visa, requirements)."""
    dest = await location_service.get_city(session, trip.destination_city_id)
    origin = (
        await location_service.get_city(session, trip.origin_city_id)
        if trip.origin_city_id else None
    )
    currency = await _currency_for_city(session, dest) if dest else get_settings().default_currency

    flights: list[FlightOffer] = []
    if origin and dest:
        flights = await search_flights(
            origin_iata=origin.iata_code, destination_iata=dest.iata_code,
            depart_date=trip.start_date, budget_tier=trip.budget_tier,
            travelers=trip.travelers, currency=currency,
        )

    hotels: list[HotelOffer] = []
    if dest:
        hotels = await search_hotels(
            city_name=dest.name, city_iata=dest.iata_code, checkin=trip.start_date,
            checkout=trip.end_date, budget_tier=trip.budget_tier,
            travelers=trip.travelers, currency=currency,
        )

    visa: VisaInfo | None = None
    if origin and dest and origin.country_iso2 != dest.country_iso2:
        rule = await location_service.get_visa_rule(session, origin.country_iso2, dest.country_iso2)
        if rule:
            visa = VisaInfo(
                requirement=rule.requirement,
                allowed_stay_days=rule.allowed_stay_days,
                notes=rule.notes,
            )

    requirements = await build_requirements(session, trip, dest, visa)
    return dest, origin, flights, hotels, visa, requirements
