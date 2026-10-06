"""
Builders for authentic booking / verification deep links.

Flights link to Aviasales (Travelpayouts affiliate, with the account marker so
the exact fare opens); hotels link to a Booking.com search for the specific
hotel so the user can verify details, reviews and live prices and book.
"""
from __future__ import annotations

from datetime import date
from urllib.parse import quote_plus

from app.core.config import get_settings

_AVIASALES = "https://www.aviasales.com"
_BOOKING = "https://www.booking.com/searchresults.html"


def _marker() -> str:
    return get_settings().travelpayouts_marker or ""


def aviasales_from_link(link_path: str) -> str:
    """Full Aviasales URL from the relative `link` returned by the data API."""
    if not link_path:
        return ""
    sep = "&" if "?" in link_path else "?"
    url = f"{_AVIASALES}{link_path}"
    m = _marker()
    return f"{url}{sep}marker={m}" if m else url


def aviasales_search_url(origin_iata: str, destination_iata: str, depart: date,
                         travelers: int = 1) -> str:
    """Aviasales search deep link: ORIGIN + DDMM + DEST + passenger count."""
    if not origin_iata or not destination_iata:
        return ""
    ddmm = f"{depart.day:02d}{depart.month:02d}"
    path = f"/search/{origin_iata}{ddmm}{destination_iata}{max(travelers, 1)}"
    m = _marker()
    return f"{_AVIASALES}{path}?marker={m}" if m else f"{_AVIASALES}{path}"


def hotel_booking_url(name: str, city: str) -> str:
    """Booking.com search for a specific hotel (verify details + book)."""
    query = ", ".join(part for part in (name, city) if part)
    if not query:
        return ""
    return f"{_BOOKING}?ss={quote_plus(query)}"
