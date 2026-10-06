"""
Amadeus Self-Service provider (flights & hotels).

Active only when AMADEUS_CLIENT_ID/SECRET are configured. Not exercised in the
test suite (needs live credentials); the travel service falls back to the mock
provider if any Amadeus call fails. Verify against the test environment once
credentials are supplied (Phase 5 live step).
"""
from __future__ import annotations

import time
from datetime import date, datetime

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.travel import FlightOffer, HotelOffer

logger = get_logger("amadeus")

_BASES = {"test": "https://test.api.amadeus.com", "production": "https://api.amadeus.com"}
_token: dict = {"value": None, "expires_at": 0.0}


def _base_url() -> str:
    return _BASES.get(get_settings().amadeus_env, _BASES["test"])


async def _get_token(client: httpx.AsyncClient) -> str:
    now = time.time()
    if _token["value"] and _token["expires_at"] - 30 > now:
        return _token["value"]
    s = get_settings()
    resp = await client.post(
        f"{_base_url()}/v1/security/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": s.amadeus_client_id,
            "client_secret": s.amadeus_client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp.raise_for_status()
    payload = resp.json()
    _token["value"] = payload["access_token"]
    _token["expires_at"] = now + payload.get("expires_in", 1799)
    return _token["value"]


def _dur_to_minutes(iso: str) -> int:
    # ISO-8601 duration like "PT7H15M"
    import re

    h = re.search(r"(\d+)H", iso)
    m = re.search(r"(\d+)M", iso)
    return (int(h.group(1)) if h else 0) * 60 + (int(m.group(1)) if m else 0)


class AmadeusFlightProvider:
    name = "amadeus"

    async def search_flights(self, *, origin_iata, destination_iata, depart_date,
                             budget_tier, travelers, currency) -> list[FlightOffer]:
        async with httpx.AsyncClient(timeout=15) as client:
            token = await _get_token(client)
            resp = await client.get(
                f"{_base_url()}/v2/shopping/flight-offers",
                params={
                    "originLocationCode": origin_iata,
                    "destinationLocationCode": destination_iata,
                    "departureDate": depart_date.isoformat(),
                    "adults": travelers,
                    "currencyCode": currency,
                    "max": 6,
                    "travelClass": "BUSINESS" if budget_tier == "luxury" else "ECONOMY",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])

        offers: list[FlightOffer] = []
        for o in data:
            itin = o["itineraries"][0]
            segs = itin["segments"]
            first, last = segs[0], segs[-1]
            carrier = first["carrierCode"]
            offers.append(FlightOffer(
                provider=self.name, airline=carrier,
                flight_number=f"{carrier}{first['number']}",
                origin_iata=first["departure"]["iataCode"],
                destination_iata=last["arrival"]["iataCode"],
                depart_time=first["departure"]["at"],
                arrive_time=last["arrival"]["at"],
                duration_minutes=_dur_to_minutes(itin.get("duration", "PT0M")),
                stops=max(len(segs) - 1, 0),
                cabin="Business" if budget_tier == "luxury" else "Economy",
                price_amount=float(o["price"]["grandTotal"]),
                price_currency=o["price"].get("currency", currency),
            ))
        offers.sort(key=lambda x: x.price_amount)
        return offers


class AmadeusHotelProvider:
    name = "amadeus"

    async def search_hotels(self, *, city_name, city_iata, checkin, checkout,
                            budget_tier, travelers, currency) -> list[HotelOffer]:
        nights = max((checkout - checkin).days, 1)
        async with httpx.AsyncClient(timeout=15) as client:
            token = await _get_token(client)
            headers = {"Authorization": f"Bearer {token}"}
            by_city = await client.get(
                f"{_base_url()}/v1/reference-data/locations/hotels/by-city",
                params={"cityCode": city_iata}, headers=headers,
            )
            by_city.raise_for_status()
            hotel_ids = [h["hotelId"] for h in by_city.json().get("data", [])[:15]]
            if not hotel_ids:
                return []
            resp = await client.get(
                f"{_base_url()}/v3/shopping/hotel-offers",
                params={
                    "hotelIds": ",".join(hotel_ids),
                    "adults": travelers,
                    "checkInDate": checkin.isoformat(),
                    "checkOutDate": checkout.isoformat(),
                    "currency": currency,
                    "bestRateOnly": "true",
                },
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])

        offers: list[HotelOffer] = []
        for h in data[:6]:
            hotel = h.get("hotel", {})
            offer = (h.get("offers") or [{}])[0]
            total = float(offer.get("price", {}).get("total", 0) or 0)
            offers.append(HotelOffer(
                provider=self.name, name=hotel.get("name", "Hotel"),
                rating=float(hotel.get("rating", 0) or 0),
                address=", ".join(hotel.get("address", {}).get("lines", []) or [city_name]),
                amenities=hotel.get("amenities", [])[:5],
                nights=nights,
                price_per_night=round(total / nights, 2) if total else 0.0,
                total_amount=total, price_currency=currency,
            ))
        offers.sort(key=lambda x: x.price_per_night)
        return offers
