"""Travel endpoints: flight/hotel search and trips."""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permissions
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.rbac import Perms
from app.db.session import get_db
from app.models.user import User
from app.schemas.travel import (
    FlightSearchResponse,
    HotelSearchResponse,
    TripCreate,
    TripDetail,
    TripOut,
)
from app.services import travel_service

router = APIRouter()


@router.get("/flights/search", response_model=FlightSearchResponse, tags=["travel"])
async def search_flights(
    origin: str = Query(min_length=3, max_length=4, description="Origin IATA code"),
    destination: str = Query(min_length=3, max_length=4, description="Destination IATA code"),
    date_: date = Query(alias="date"),
    budget: str = Query(default="medium"),
    travelers: int = Query(default=1, ge=1, le=20),
    currency: str | None = Query(default=None, max_length=3),
    _: User = Depends(get_current_user),
):
    cur = (currency or get_settings().default_currency).upper()
    offers = await travel_service.search_flights(
        origin_iata=origin.upper(), destination_iata=destination.upper(),
        depart_date=date_, budget_tier=budget, travelers=travelers, currency=cur,
    )
    return FlightSearchResponse(
        origin=origin.upper(), destination=destination.upper(), date=date_,
        budget_tier=budget if budget in ("low", "medium", "luxury") else "medium",
        currency=cur, offers=offers,
    )


@router.get("/hotels/search", response_model=HotelSearchResponse, tags=["travel"])
async def search_hotels(
    city: str = Query(min_length=2, max_length=100),
    iata: str = Query(min_length=3, max_length=4),
    checkin: date = Query(),
    checkout: date = Query(),
    budget: str = Query(default="medium"),
    travelers: int = Query(default=1, ge=1, le=20),
    currency: str | None = Query(default=None, max_length=3),
    _: User = Depends(get_current_user),
):
    if checkout <= checkin:
        raise AppError("Check-out must be after check-in.", code="invalid_dates", status_code=422)
    cur = (currency or get_settings().default_currency).upper()
    offers = await travel_service.search_hotels(
        city_name=city, city_iata=iata.upper(), checkin=checkin, checkout=checkout,
        budget_tier=budget, travelers=travelers, currency=cur,
    )
    return HotelSearchResponse(
        city=city, checkin=checkin, checkout=checkout, nights=(checkout - checkin).days,
        budget_tier=budget if budget in ("low", "medium", "luxury") else "medium",
        currency=cur, offers=offers,
    )


@router.post("/trips", response_model=TripOut, status_code=status.HTTP_201_CREATED, tags=["travel"])
async def create_trip(
    payload: TripCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Perms.TRIP_MANAGE)),
):
    trip = await travel_service.create_trip(db, user.id, payload)
    return await travel_service.to_trip_out(db, trip)


@router.get("/trips", response_model=list[TripOut], tags=["travel"])
async def list_trips(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Perms.TRIP_MANAGE)),
):
    trips = await travel_service.list_trips(db, user.id)
    return [await travel_service.to_trip_out(db, t) for t in trips]


@router.get("/trips/{trip_id}", response_model=TripDetail, tags=["travel"])
async def get_trip(
    trip_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Perms.TRIP_MANAGE)),
):
    trip = await travel_service.get_owned_trip(db, user.id, trip_id)
    if not trip:
        raise AppError("Trip not found.", code="trip_not_found", status_code=404)

    dest, _origin, flights, hotels, visa = await travel_service.build_detail_parts(db, trip)
    itinerary = travel_service.build_itinerary(dest.name, trip.start_date, trip.end_date)
    return TripDetail(
        trip=await travel_service.to_trip_out(db, trip),
        itinerary=itinerary,
        suggested_flights=flights,
        suggested_hotels=hotels,
        visa=visa,
    )
