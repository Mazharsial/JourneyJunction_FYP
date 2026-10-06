"""Idempotent seeding of currencies, countries, cities, visa rules and config.

Dubai (UAE) is the first supported market, seeded as data — not hardcoded in
application logic. Visa data is DEMO/informational only.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import (
    AppConfig,
    City,
    Country,
    CountryRequirement,
    Currency,
    VisaRule,
)

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

# Destination entry / travel requirements (informational, demo data).
# Keyed by destination ISO2. required_documents drives the compliance check,
# so phrase them so a keyword (passport / visa / ticket / id) is detectable.
COUNTRY_REQUIREMENTS = [
    {
        "destination_iso2": "AE",
        "passport_validity_months": 6,
        "required_documents": [
            "Passport valid for at least 6 months beyond arrival",
            "UAE tourist visa (apply before travel)",
            "Confirmed return or onward flight ticket",
            "Confirmed hotel booking or host details",
            "Proof of sufficient funds for the stay",
        ],
        "health": [
            "No mandatory vaccinations for most travellers.",
            "Polio or COVID-19 certificates may be required when arriving from certain countries — check before you fly.",
        ],
        "currency_notes": (
            "Local currency is the UAE Dirham (AED). Amounts of cash, or equivalent, "
            "above AED 60,000 (about USD 16,000) must be declared on arrival."
        ),
        "customs_notes": (
            "Alcohol, pork products and some prescription medicines are restricted. "
            "Narcotics and offensive/political material are strictly prohibited."
        ),
        "entry_notes": (
            "Complete immigration formalities on arrival — a biometric eye/face scan may "
            "apply. Keep your hotel address and return ticket accessible."
        ),
        "emergency_number": "999 (police) · 998 (ambulance)",
        "official_source": "https://u.ae/en/information-and-services/visa-and-emirates-id",
    },
    {
        "destination_iso2": "PK",
        "passport_validity_months": 6,
        "required_documents": [
            "Passport valid for at least 6 months beyond arrival",
            "Pakistan visa or NICOP/POC (apply before travel)",
            "Return or onward flight ticket",
            "Proof of accommodation or host/sponsor details",
        ],
        "health": [
            "A polio vaccination certificate may be required when departing Pakistan.",
            "Hepatitis A and typhoid vaccinations are recommended.",
        ],
        "currency_notes": (
            "Local currency is the Pakistani Rupee (PKR). Foreign currency above "
            "USD 10,000 must be declared; export of PKR is restricted."
        ),
        "customs_notes": (
            "Declare goods above the duty-free allowance. Narcotics, alcohol and certain "
            "publications are prohibited."
        ),
        "entry_notes": (
            "Carry your visa and sponsor/host details. Long-term visitors may need to "
            "register with local authorities."
        ),
        "emergency_number": "15 (police) · 1122 (rescue/ambulance)",
        "official_source": "https://visa.nadra.gov.pk",
    },
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

    existing_req = {
        r.destination_iso2
        for r in (await session.scalars(select(CountryRequirement))).all()
    }
    for req in COUNTRY_REQUIREMENTS:
        if req["destination_iso2"] not in existing_req:
            session.add(CountryRequirement(**req))

    if not await session.scalar(select(AppConfig).where(AppConfig.key == "default_market")):
        session.add(AppConfig(key="default_market", value={
            "country": "AE", "city": "Dubai", "currency": "AED",
            "locale": "en", "timezone": "Asia/Dubai",
        }))

    await session.flush()
