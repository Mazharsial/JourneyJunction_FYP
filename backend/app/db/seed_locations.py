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
    ("PKR", "Pakistani Rupee", "₨"),
    ("USD", "US Dollar", "$"),  # retained for billing / plan pricing display
]

# Supported markets: Pakistan (home) and the UAE (the single international
# destination). Seeded as data, not hardcoded in application logic.
COUNTRIES = [
    ("PK", "Pakistan", "PKR", "+92"),
    ("AE", "United Arab Emirates", "AED", "+971"),
]

# (country_iso2, name, iata, timezone, lat, lon)
CITIES = [
    # Pakistan cities
    ("PK", "Karachi", "KHI", "Asia/Karachi", 24.8607, 67.0011),
    ("PK", "Lahore", "LHE", "Asia/Karachi", 31.5204, 74.3587),
    ("PK", "Islamabad", "ISB", "Asia/Karachi", 33.6844, 73.0479),
    ("PK", "Peshawar", "PEW", "Asia/Karachi", 34.0151, 71.5249),
    ("PK", "Quetta", "UET", "Asia/Karachi", 30.1798, 66.9750),
    ("PK", "Faisalabad", "LYP", "Asia/Karachi", 31.4504, 73.1350),
    ("PK", "Multan", "MUX", "Asia/Karachi", 30.1575, 71.5249),
    ("PK", "Sialkot", "SKT", "Asia/Karachi", 32.4945, 74.5229),
    # UAE — the only out-of-country destination
    ("AE", "Dubai", "DXB", "Asia/Dubai", 25.2048, 55.2708),
    ("AE", "Abu Dhabi", "AUH", "Asia/Dubai", 24.4539, 54.3773),
    ("AE", "Sharjah", "SHJ", "Asia/Dubai", 25.3463, 55.4209),
]

# (origin, destination, requirement, allowed_stay_days, notes)
_SRC = "Demo data — always verify with official government sources."
VISA_RULES = [
    ("PK", "AE", "visa_required", 30, "Apply for a UAE tourist visa before travelling."),
    ("AE", "PK", "visa_required", 30, "Apply for a Pakistan visa before travelling."),
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
