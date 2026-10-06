"""Provider interfaces for flight & hotel search."""
from __future__ import annotations

from datetime import date
from typing import Protocol

from app.schemas.travel import FlightOffer, HotelOffer


class FlightProvider(Protocol):
    name: str

    async def search_flights(
        self,
        *,
        origin_iata: str,
        destination_iata: str,
        depart_date: date,
        budget_tier: str,
        travelers: int,
        currency: str,
    ) -> list[FlightOffer]: ...


class HotelProvider(Protocol):
    name: str

    async def search_hotels(
        self,
        *,
        city_name: str,
        city_iata: str,
        checkin: date,
        checkout: date,
        budget_tier: str,
        travelers: int,
        currency: str,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> list[HotelOffer]: ...
