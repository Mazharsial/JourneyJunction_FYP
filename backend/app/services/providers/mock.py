"""
Deterministic mock travel provider.

Generates plausible, stable results from the query (seeded RNG) so the product
works end-to-end without external API keys and tests are reproducible.
"""
from __future__ import annotations

import hashlib
import random
from datetime import date, datetime, timedelta

from app.schemas.travel import FlightOffer, HotelOffer
from app.services.providers.booking_links import aviasales_search_url, hotel_booking_url

_AIRLINES = [
    ("Emirates", "EK"),
    ("flydubai", "FZ"),
    ("Qatar Airways", "QR"),
    ("Etihad Airways", "EY"),
    ("Turkish Airlines", "TK"),
]
_HOTELS = ["Marina Bay Hotel", "Downtown Suites", "Desert Pearl Resort", "City Centre Inn",
           "Palm Grand Hotel", "Skyline Residences"]
_AMENITIES = ["Free WiFi", "Breakfast", "Pool", "Gym", "Airport shuttle", "Spa", "Parking"]

# tier -> (flight base multiplier, cabin, hotel nightly base, min rating)
_TIER = {
    "low": (1.0, "Economy", 220.0, 3.0),
    "medium": (1.6, "Economy", 420.0, 3.8),
    "luxury": (3.2, "Business", 950.0, 4.5),
}


def _rng(*parts) -> random.Random:
    seed = hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()
    return random.Random(int(seed[:12], 16))


class MockFlightProvider:
    name = "mock"

    async def search_flights(self, *, origin_iata, destination_iata, depart_date,
                             budget_tier, travelers, currency) -> list[FlightOffer]:
        mult, cabin, _, _ = _TIER.get(budget_tier, _TIER["medium"])
        rng = _rng("flight", origin_iata, destination_iata, depart_date, budget_tier)
        base = 350 + rng.randint(0, 400)
        offers: list[FlightOffer] = []
        for _ in range(4):
            airline, iata = rng.choice(_AIRLINES)
            dep_hour = rng.randint(0, 22)
            dur = rng.randint(120, 540)
            stops = 0 if rng.random() < 0.6 else 1
            dep = datetime.combine(depart_date, datetime.min.time()) + timedelta(hours=dep_hour)
            arr = dep + timedelta(minutes=dur + (stops * 90))
            price = round((base + rng.randint(-80, 160)) * mult * travelers, 2)
            offers.append(FlightOffer(
                provider=self.name, airline=airline, flight_number=f"{iata}{rng.randint(100, 999)}",
                origin_iata=origin_iata, destination_iata=destination_iata,
                depart_time=dep.isoformat(), arrive_time=arr.isoformat(),
                duration_minutes=dur + stops * 90, stops=stops, cabin=cabin,
                price_amount=price, price_currency=currency,
                booking_url=aviasales_search_url(origin_iata, destination_iata, depart_date, travelers),
            ))
        offers.sort(key=lambda o: o.price_amount)
        return offers


class MockHotelProvider:
    name = "mock"

    async def search_hotels(self, *, city_name, city_iata, checkin, checkout,
                            budget_tier, travelers, currency,
                            latitude=None, longitude=None) -> list[HotelOffer]:
        _, _, nightly_base, min_rating = _TIER.get(budget_tier, _TIER["medium"])
        nights = max((checkout - checkin).days, 1)
        rng = _rng("hotel", city_name, checkin, checkout, budget_tier)
        offers: list[HotelOffer] = []
        for name in rng.sample(_HOTELS, k=4):
            rating = round(min(5.0, min_rating + rng.random() * (5.0 - min_rating)), 1)
            nightly = round(nightly_base + rng.randint(-60, 180), 2)
            amenities = rng.sample(_AMENITIES, k=rng.randint(3, 5))
            offers.append(HotelOffer(
                provider=self.name, name=f"{name} {city_name}", rating=rating,
                address=f"{rng.randint(1, 200)} Main Road, {city_name}",
                amenities=amenities, nights=nights, price_per_night=nightly,
                total_amount=round(nightly * nights, 2), price_currency=currency,
                booking_url=hotel_booking_url(f"{name} {city_name}", city_name),
            ))
        offers.sort(key=lambda o: o.price_per_night)
        return offers
