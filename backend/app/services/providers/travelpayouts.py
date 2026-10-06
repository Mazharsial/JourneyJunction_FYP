"""
Travelpayouts provider (flights via Aviasales, hotels via Hotellook).

Active when TRAVELPAYOUTS_TOKEN is configured. The flight data is cached
pricing from recent real searches (free tier), so some routes/dates may return
nothing — the travel service falls back to the mock provider when a live
provider yields no results, so the UI always has offers to show.

Docs:
- Flights:  https://api.travelpayouts.com/aviasales/v3/prices_for_dates
- Hotels:   https://engine.hotellook.com/api/v2/cache.json
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.travel import FlightOffer, HotelOffer

logger = get_logger("travelpayouts")

_FLIGHTS_URL = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
_HOTELS_URL = "https://engine.hotellook.com/api/v2/cache.json"


def _add_minutes(iso: str, minutes: int) -> str:
    try:
        return (datetime.fromisoformat(iso) + timedelta(minutes=minutes)).isoformat()
    except Exception:
        return iso


class TravelpayoutsFlightProvider:
    name = "travelpayouts"

    async def search_flights(self, *, origin_iata, destination_iata, depart_date,
                             budget_tier, travelers, currency) -> list[FlightOffer]:
        token = get_settings().travelpayouts_token
        params = {
            "origin": origin_iata,
            "destination": destination_iata,
            "departure_at": depart_date.isoformat(),
            "currency": (currency or "usd").lower(),
            "one_way": "true",
            "sorting": "price",
            "direct": "false",
            "limit": 8,
            "page": 1,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                _FLIGHTS_URL, params=params, headers={"X-Access-Token": token}
            )
            resp.raise_for_status()
            payload = resp.json()
        data = payload.get("data", []) if isinstance(payload, dict) else []

        offers: list[FlightOffer] = []
        for o in data:
            airline = o.get("airline", "") or ""
            num = str(o.get("flight_number", "") or "")
            duration = int(o.get("duration") or 0)
            depart = o.get("departure_at", "") or ""
            # Travelpayouts only exposes economy cached fares.
            price = float(o.get("price") or 0)
            if price <= 0:
                continue
            offers.append(FlightOffer(
                provider=self.name,
                airline=airline or "—",
                flight_number=f"{airline}{num}".strip() or "—",
                origin_iata=o.get("origin_airport") or o.get("origin") or origin_iata,
                destination_iata=o.get("destination_airport") or o.get("destination") or destination_iata,
                depart_time=depart,
                arrive_time=_add_minutes(depart, duration),
                duration_minutes=duration,
                stops=int(o.get("transfers") or 0),
                cabin="Economy",
                price_amount=price,
                price_currency=(o.get("currency") or currency).upper(),
            ))
        offers.sort(key=lambda x: x.price_amount)
        return offers


class TravelpayoutsHotelProvider:
    name = "travelpayouts"

    async def search_hotels(self, *, city_name, city_iata, checkin, checkout,
                            budget_tier, travelers, currency) -> list[HotelOffer]:
        nights = max((checkout - checkin).days, 1)
        params = {
            "location": city_name,
            "currency": (currency or "usd").lower(),
            "checkIn": checkin.isoformat(),
            "checkOut": checkout.isoformat(),
            "limit": 10,
            "token": get_settings().travelpayouts_token,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(_HOTELS_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
        if not isinstance(data, list):
            return []

        offers: list[HotelOffer] = []
        for h in data:
            total = float(h.get("priceAvg") or h.get("priceFrom") or 0)
            if total <= 0:
                continue
            loc = h.get("location") or {}
            offers.append(HotelOffer(
                provider=self.name,
                name=h.get("hotelName", "Hotel"),
                rating=float(h.get("stars") or 0),
                address=(loc.get("name") if isinstance(loc, dict) else None) or city_name,
                amenities=[],  # Hotellook cache does not expose amenities
                nights=nights,
                price_per_night=round(total / nights, 2),
                total_amount=round(total, 2),
                price_currency=(currency or "USD").upper(),
            ))
        offers.sort(key=lambda x: x.price_per_night)
        return offers
