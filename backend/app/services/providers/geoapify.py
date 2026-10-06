"""
Geoapify Places hotel provider.

Returns REAL hotels (name, address, location) near a destination's coordinates
from the free Geoapify Places API. Geoapify does not expose live room prices or
guest ratings, so those are ESTIMATED deterministically from the budget tier and
a stable hash of the hotel name — the trip page labels them as estimates. Real
hotel names/addresses are live; prices/ratings are indicative.

Docs: https://apidocs.geoapify.com/docs/places/
"""
from __future__ import annotations

import hashlib
from datetime import date

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.travel import HotelOffer

logger = get_logger("geoapify")

_URL = "https://api.geoapify.com/v2/places"

# Indicative nightly base price per currency and budget tier (whole units).
_BASE: dict[str, dict[str, float]] = {
    "AED": {"low": 260, "medium": 540, "luxury": 1150},
    "SAR": {"low": 280, "medium": 560, "luxury": 1200},
    "PKR": {"low": 12000, "medium": 28000, "luxury": 65000},
    "USD": {"low": 70, "medium": 150, "luxury": 330},
}
_TIER_MIN_RATING = {"low": 3.6, "medium": 4.0, "luxury": 4.5}


def _hash_unit(text: str) -> float:
    """Stable value in [0, 1) derived from the hotel name."""
    h = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
    return (h % 1000) / 1000.0


def _estimate_rating(name: str, raw_stars, budget_tier: str) -> float:
    if raw_stars:
        try:
            return max(1.0, min(5.0, float(raw_stars)))
        except (TypeError, ValueError):
            pass
    floor = _TIER_MIN_RATING.get(budget_tier, 4.0)
    return round(floor + _hash_unit(name) * (4.9 - floor), 1)


def _estimate_price(name: str, currency: str, budget_tier: str) -> float:
    table = _BASE.get(currency.upper(), _BASE["USD"])
    base = table.get(budget_tier, table["medium"])
    # +/-25% deterministic spread so hotels differ but stay stable per name.
    factor = 0.75 + _hash_unit(name + currency) * 0.5
    return round(base * factor, 2)


class GeoapifyHotelProvider:
    name = "geoapify"

    async def search_hotels(self, *, city_name, city_iata, checkin, checkout,
                            budget_tier, travelers, currency,
                            latitude=None, longitude=None) -> list[HotelOffer]:
        if latitude is None or longitude is None:
            return []  # no coordinates -> let the caller fall back to the mock
        nights = max((checkout - checkin).days, 1)
        params = {
            "categories": "accommodation.hotel",
            "filter": f"circle:{longitude},{latitude},15000",
            "bias": f"proximity:{longitude},{latitude}",
            "limit": 20,
            "apiKey": get_settings().geoapify_api_key,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(_URL, params=params)
            resp.raise_for_status()
            feats = resp.json().get("features", [])

        offers: list[HotelOffer] = []
        seen: set[str] = set()
        for f in feats:
            p = f.get("properties", {}) or {}
            name = p.get("name")
            if not name or name in seen:
                continue
            seen.add(name)
            raw = (p.get("datasource", {}) or {}).get("raw", {}) or {}
            rating = _estimate_rating(name, raw.get("stars"), budget_tier)
            if rating < _TIER_MIN_RATING.get(budget_tier, 0):
                continue
            nightly = _estimate_price(name, currency, budget_tier)
            address = p.get("address_line2") or p.get("formatted") or city_name
            amenities: list[str] = []
            if raw.get("internet_access") not in (None, "no"):
                amenities.append("Free WiFi")
            if raw.get("air_conditioning") == "yes":
                amenities.append("Air conditioning")
            if raw.get("swimming_pool") == "yes" or raw.get("leisure") == "swimming_pool":
                amenities.append("Pool")
            offers.append(HotelOffer(
                provider=self.name, name=name, rating=rating,
                address=address, amenities=amenities, nights=nights,
                price_per_night=nightly,
                total_amount=round(nightly * nights, 2),
                price_currency=currency.upper(),
            ))
            if len(offers) >= 8:
                break
        offers.sort(key=lambda x: x.price_per_night)
        return offers
