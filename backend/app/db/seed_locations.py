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
    ("SAR", "Saudi Riyal", "﷼"),
    ("USD", "US Dollar", "$"),  # retained for billing / plan pricing display
]

# Supported markets: Pakistan (home) plus the UAE and Saudi Arabia (the
# international destinations — Saudi also covers Umrah & Hajj pilgrimage).
# Seeded as data, not hardcoded in application logic.
COUNTRIES = [
    ("PK", "Pakistan", "PKR", "+92"),
    ("AE", "United Arab Emirates", "AED", "+971"),
    ("SA", "Saudi Arabia", "SAR", "+966"),
]

# (country_iso2, name, iata, timezone, lat, lon)
# Makkah has no airport of its own — pilgrims fly into Jeddah (JED), so it
# carries the JED gateway code so flight search still works.
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
    # UAE
    ("AE", "Dubai", "DXB", "Asia/Dubai", 25.2048, 55.2708),
    ("AE", "Abu Dhabi", "AUH", "Asia/Dubai", 24.4539, 54.3773),
    ("AE", "Sharjah", "SHJ", "Asia/Dubai", 25.3463, 55.4209),
    # Saudi Arabia (incl. the holy cities for Umrah & Hajj)
    ("SA", "Jeddah", "JED", "Asia/Riyadh", 21.4858, 39.1925),
    ("SA", "Makkah", "JED", "Asia/Riyadh", 21.3891, 39.8579),
    ("SA", "Madinah", "MED", "Asia/Riyadh", 24.5247, 39.5692),
    ("SA", "Riyadh", "RUH", "Asia/Riyadh", 24.7136, 46.6753),
    ("SA", "Dammam", "DMM", "Asia/Riyadh", 26.3927, 49.9777),
]

# (origin, destination, requirement, allowed_stay_days, notes)
_SRC = "Demo data — always verify with official government sources."
VISA_RULES = [
    ("PK", "AE", "visa_required", 30, "Apply for a UAE tourist visa before travelling."),
    ("AE", "PK", "visa_required", 30, "Apply for a Pakistan visa before travelling."),
    ("PK", "SA", "visa_required", 90, "Apply via the Nusuk / Saudi eVisa platform before travelling."),
    ("AE", "SA", "visa_required", 90, "Apply via the Nusuk / Saudi eVisa platform before travelling."),
    ("SA", "PK", "visa_required", 30, "Apply for a Pakistan visa before travelling."),
]

# Destination entry / travel requirements (informational, demo data).
# Keyed by (destination ISO2, purpose). purpose defaults to "tourism"; Saudi
# Arabia also carries "umrah" and "hajj" variants with pilgrimage-specific
# rules. required_documents drives the compliance check, so phrase them so a
# keyword (passport / visa / ticket / id) is detectable.
COUNTRY_REQUIREMENTS = [
    {
        "destination_iso2": "AE",
        "purpose": "tourism",
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
        "purpose": "tourism",
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
    # ----- Saudi Arabia: general tourism -----
    {
        "destination_iso2": "SA",
        "purpose": "tourism",
        "passport_validity_months": 6,
        "required_documents": [
            "Passport valid for at least 6 months beyond arrival",
            "Saudi tourist eVisa (apply via the Nusuk / Visit Saudi platform)",
            "Return or onward flight ticket",
            "Confirmed hotel booking",
            "Proof of sufficient funds for the stay",
        ],
        "health": [
            "No mandatory vaccinations for general tourism for most travellers.",
            "A polio certificate may be required when arriving from affected countries.",
        ],
        "currency_notes": (
            "Local currency is the Saudi Riyal (SAR). Cash, or equivalent, above "
            "SAR 60,000 (about USD 16,000) must be declared on arrival."
        ),
        "customs_notes": (
            "Alcohol, pork products, narcotics and material offensive to Islam are "
            "strictly prohibited. Respect local dress and conduct codes."
        ),
        "entry_notes": (
            "Complete immigration formalities and fingerprint/biometric capture on "
            "arrival. Keep your hotel address and return ticket accessible."
        ),
        "emergency_number": "999 (police) · 997 (ambulance) · 998 (civil defence)",
        "official_source": "https://www.visitsaudi.com/en/do-saudi/visa-information",
    },
    # ----- Saudi Arabia: Umrah -----
    {
        "destination_iso2": "SA",
        "purpose": "umrah",
        "passport_validity_months": 6,
        "required_documents": [
            "Passport valid for at least 6 months beyond arrival",
            "Umrah visa or tourist eVisa issued through the Nusuk platform",
            "Return or onward flight ticket with confirmed dates",
            "Confirmed Makkah / Madinah hotel booking",
            "Meningococcal (ACWY) vaccination certificate",
        ],
        "health": [
            "Meningococcal meningitis (ACWY) vaccination is MANDATORY — certificate "
            "issued at least 10 days before arrival and valid for the trip.",
            "Seasonal influenza and COVID-19 vaccination are recommended.",
            "A polio certificate is required for arrivals from polio-affected countries.",
        ],
        "currency_notes": (
            "Carry Saudi Riyal (SAR) for local expenses; cards are widely accepted. "
            "Declare cash, or equivalent, above SAR 60,000 on arrival."
        ),
        "customs_notes": (
            "Carry Ihram clothing. Zamzam water is provided at the airport on departure "
            "(do not pack it in checked baggage from the city). Alcohol and narcotics are "
            "strictly prohibited."
        ),
        "entry_notes": (
            "Book your Umrah permit and prayer/Rawdah slots through the Nusuk app. "
            "Umrah can be performed year-round except during the Hajj season. Women may "
            "travel without a mahram under current rules — verify before booking."
        ),
        "emergency_number": "999 (police) · 997 (ambulance) · 911 (in Makkah/Madinah)",
        "official_source": "https://www.nusuk.sa",
    },
    # ----- Saudi Arabia: Hajj -----
    {
        "destination_iso2": "SA",
        "purpose": "hajj",
        "passport_validity_months": 6,
        "required_documents": [
            "Passport valid for at least 6 months beyond arrival",
            "Hajj visa issued through an approved operator or the Nusuk platform",
            "Return flight ticket within the permitted Hajj travel window",
            "Confirmed Hajj package (Makkah, Mina, Arafat, Muzdalifah accommodation)",
            "Meningococcal (ACWY) vaccination certificate",
        ],
        "health": [
            "Meningococcal meningitis (ACWY) vaccination is MANDATORY — certificate "
            "issued at least 10 days before arrival.",
            "Seasonal influenza and COVID-19 vaccination are strongly recommended.",
            "A polio certificate is required for arrivals from polio-affected countries "
            "(including Pakistan) — carry proof of OPV.",
        ],
        "currency_notes": (
            "Carry Saudi Riyal (SAR) for local expenses and sacrifice (Hady) payment. "
            "Declare cash, or equivalent, above SAR 60,000 on arrival."
        ),
        "customs_notes": (
            "Carry Ihram clothing. Alcohol, narcotics and prohibited items are strictly "
            "banned. Follow your group's schedule for Mina, Arafat and Muzdalifah."
        ),
        "entry_notes": (
            "Hajj is performed once a year in Dhul-Hijjah and requires an official Hajj "
            "visa and package — a tourist or Umrah visa is NOT valid for Hajj. Book only "
            "through a licensed operator or the Nusuk Hajj platform. A wristband/ID is "
            "issued on arrival; keep it on at all times."
        ),
        "emergency_number": "999 (police) · 997 (ambulance) · 911 (in Makkah/Madinah)",
        "official_source": "https://www.nusuk.sa",
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
        (r.destination_iso2, r.purpose)
        for r in (await session.scalars(select(CountryRequirement))).all()
    }
    for req in COUNTRY_REQUIREMENTS:
        if (req["destination_iso2"], req.get("purpose", "tourism")) not in existing_req:
            session.add(CountryRequirement(**req))

    if not await session.scalar(select(AppConfig).where(AppConfig.key == "default_market")):
        session.add(AppConfig(key="default_market", value={
            "country": "AE", "city": "Dubai", "currency": "AED",
            "locale": "en", "timezone": "Asia/Dubai",
        }))

    await session.flush()
