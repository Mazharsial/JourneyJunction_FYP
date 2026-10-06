"""Idempotent seeding of currencies, countries, cities, visa rules and config.

Dubai (UAE) is the first supported market, seeded as data — not hardcoded in
application logic. Visa data is DEMO/informational only.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import AppConfig, City, Country, Currency, VisaRule

CURRENCIES = [
    ("AED", "UAE Dirham", "د.إ"),
    ("USD", "US Dollar", "$"),
    ("GBP", "Pound Sterling", "£"),
    ("EUR", "Euro", "€"),
    ("PKR", "Pakistani Rupee", "₨"),
    ("SAR", "Saudi Riyal", "﷼"),
    ("TRY", "Turkish Lira", "₺"),
]

COUNTRIES = [
    ("AE", "United Arab Emirates", "AED", "+971"),
    ("PK", "Pakistan", "PKR", "+92"),
    ("GB", "United Kingdom", "GBP", "+44"),
    ("US", "United States", "USD", "+1"),
    ("SA", "Saudi Arabia", "SAR", "+966"),
    ("TR", "Türkiye", "TRY", "+90"),
    ("FR", "France", "EUR", "+33"),
]

# (country_iso2, name, iata, timezone, lat, lon)
CITIES = [
    ("AE", "Dubai", "DXB", "Asia/Dubai", 25.2048, 55.2708),
    ("AE", "Abu Dhabi", "AUH", "Asia/Dubai", 24.4539, 54.3773),
    ("PK", "Lahore", "LHE", "Asia/Karachi", 31.5204, 74.3587),
    ("PK", "Karachi", "KHI", "Asia/Karachi", 24.8607, 67.0011),
    ("PK", "Islamabad", "ISB", "Asia/Karachi", 33.6844, 73.0479),
    ("GB", "London", "LHR", "Europe/London", 51.5074, -0.1278),
    ("US", "New York", "JFK", "America/New_York", 40.7128, -74.0060),
    ("SA", "Jeddah", "JED", "Asia/Riyadh", 21.4858, 39.1925),
    ("SA", "Riyadh", "RUH", "Asia/Riyadh", 24.7136, 46.6753),
    ("TR", "Istanbul", "IST", "Europe/Istanbul", 41.0082, 28.9784),
    ("FR", "Paris", "CDG", "Europe/Paris", 48.8566, 2.3522),
]

# (origin, destination, requirement, allowed_stay_days, notes)
_SRC = "Demo data — always verify with official government sources."
VISA_RULES = [
    ("PK", "AE", "visa_required", 30, "Apply for a UAE tourist visa before travelling."),
    ("GB", "AE", "visa_on_arrival", 30, "Visa on arrival for UK passport holders."),
    ("US", "AE", "visa_on_arrival", 30, "Visa on arrival for US passport holders."),
    ("SA", "AE", "visa_free", 90, "GCC national — no visa required."),
    ("TR", "AE", "visa_on_arrival", 30, "Visa on arrival for Turkish passport holders."),
    ("FR", "AE", "visa_on_arrival", 90, "Visa on arrival for French passport holders."),
]


async def seed_locations(session: AsyncSession) -> None:
    existing_cur = {c.code for c in (await session.scalars(select(Currency))).all()}
    for code, name, symbol in CURRENCIES:
        if code not in existing_cur:
            session.add(Currency(code=code, name=name, symbol=symbol))

    existing_country = {c.iso2 for c in (await session.scalars(select(Country))).all()}
    for iso2, name, cur, phone in COUNTRIES:
        if iso2 not in existing_country:
            session.add(Country(iso2=iso2, name=name, currency_code=cur, phone_code=phone))
    await session.flush()

    existing_city = {
        (c.country_iso2, c.name) for c in (await session.scalars(select(City))).all()
    }
    for iso2, name, iata, tz, lat, lon in CITIES:
        if (iso2, name) not in existing_city:
            session.add(
                City(country_iso2=iso2, name=name, iata_code=iata, timezone=tz,
                     latitude=lat, longitude=lon)
            )

    existing_visa = {
        (v.origin_iso2, v.destination_iso2)
        for v in (await session.scalars(select(VisaRule))).all()
    }
    for origin, dest, req, days, notes in VISA_RULES:
        if (origin, dest) not in existing_visa:
            session.add(
                VisaRule(origin_iso2=origin, destination_iso2=dest, requirement=req,
                         allowed_stay_days=days, notes=notes, source=_SRC)
            )

    if not await session.scalar(select(AppConfig).where(AppConfig.key == "default_market")):
        session.add(AppConfig(key="default_market", value={
            "country": "AE", "city": "Dubai", "currency": "AED",
            "locale": "en", "timezone": "Asia/Dubai",
        }))

    await session.flush()
