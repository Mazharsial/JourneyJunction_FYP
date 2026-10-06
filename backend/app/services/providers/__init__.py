"""
Travel provider factory.

Prefers Travelpayouts (free: Aviasales flights + Hotellook hotels) when a token
is configured, then Amadeus if its credentials are set, otherwise a
deterministic mock so the app is fully functional without any API keys.
"""
from __future__ import annotations

from app.core.config import get_settings
from app.services.providers.base import FlightProvider, HotelProvider
from app.services.providers.mock import MockFlightProvider, MockHotelProvider


def _travelpayouts_configured() -> bool:
    return bool(get_settings().travelpayouts_token)


def _amadeus_configured() -> bool:
    s = get_settings()
    return bool(s.amadeus_client_id and s.amadeus_client_secret)


def get_flight_provider() -> FlightProvider:
    if _travelpayouts_configured():
        from app.services.providers.travelpayouts import TravelpayoutsFlightProvider

        return TravelpayoutsFlightProvider()
    if _amadeus_configured():
        from app.services.providers.amadeus import AmadeusFlightProvider

        return AmadeusFlightProvider()
    return MockFlightProvider()


def _geoapify_configured() -> bool:
    return bool(get_settings().geoapify_api_key)


def get_hotel_provider() -> HotelProvider:
    # Geoapify Places gives REAL hotel names/addresses/locations (prices and
    # ratings are estimated). Travelpayouts/Hotellook's free hotel-price endpoint
    # was retired and Amadeus self-service is gone, so those aren't used here.
    if _geoapify_configured():
        from app.services.providers.geoapify import GeoapifyHotelProvider

        return GeoapifyHotelProvider()
    if _amadeus_configured():
        from app.services.providers.amadeus import AmadeusHotelProvider

        return AmadeusHotelProvider()
    return MockHotelProvider()


def active_provider_name() -> str:
    if _travelpayouts_configured():
        return "travelpayouts"
    if _amadeus_configured():
        return "amadeus"
    return "mock"


def active_hotel_provider_name() -> str:
    if _geoapify_configured():
        return "geoapify"
    if _amadeus_configured():
        return "amadeus"
    return "mock"
