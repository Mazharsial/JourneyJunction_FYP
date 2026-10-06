"""
Travel provider factory.

Returns the Amadeus-backed provider when credentials are configured, otherwise
a deterministic mock provider so the app is fully functional without API keys.
"""
from __future__ import annotations

from app.core.config import get_settings
from app.services.providers.base import FlightProvider, HotelProvider
from app.services.providers.mock import MockFlightProvider, MockHotelProvider


def _amadeus_configured() -> bool:
    s = get_settings()
    return bool(s.amadeus_client_id and s.amadeus_client_secret)


def get_flight_provider() -> FlightProvider:
    if _amadeus_configured():
        from app.services.providers.amadeus import AmadeusFlightProvider

        return AmadeusFlightProvider()
    return MockFlightProvider()


def get_hotel_provider() -> HotelProvider:
    if _amadeus_configured():
        from app.services.providers.amadeus import AmadeusHotelProvider

        return AmadeusHotelProvider()
    return MockHotelProvider()


def active_provider_name() -> str:
    return "amadeus" if _amadeus_configured() else "mock"
