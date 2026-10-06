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

# ---------------------------------------------------------------------------
# Visa types / routes per destination & purpose (from Pakistan).
# Researched from current 2026 guidance — indicative, verify at official links.
# ---------------------------------------------------------------------------
_VISA_TYPES_AE = [
    {"name": "30-day tourist visa", "duration": "30 days stay",
     "fee": "≈ AED 252 + 5% VAT", "entry": "single or multiple entry",
     "notes": "Most common for short visits; apply via an airline, hotel or licensed agent. Approval usually 3–7 working days."},
    {"name": "60-day tourist visa", "duration": "60 days stay",
     "fee": "≈ AED 352 + 5% VAT", "entry": "single or multiple entry",
     "notes": "For longer visits."},
    {"name": "5-year multiple-entry tourist visa", "duration": "up to 90 days per visit (5-year validity)",
     "fee": "varies", "entry": "multiple entry",
     "notes": "Opened to Pakistani nationals in 2025. No local sponsor needed; show proof of funds (about USD 4,000)."},
    {"name": "Transit visa", "duration": "48 or 96 hours",
     "fee": "48h free / 96h ≈ AED 50", "entry": "single",
     "notes": "For short layovers. Note: ordinary Pakistani passports have no visa-on-arrival — arrange a visa before travel."},
]
_VISA_TYPES_SA_TOURISM = [
    {"name": "Tourist eVisa", "duration": "up to 90 days per visit (1-year multiple entry)",
     "fee": "≈ SAR 480 (incl. insurance)", "entry": "multiple entry",
     "notes": "Allows tourism and Umrah outside the Hajj season. IMPORTANT: Pakistani passport holders are generally NOT on the tourist eVisa eligible list — use the Umrah visa route instead."},
    {"name": "Transit / stopover visa", "duration": "up to 96 hours",
     "fee": "visa free (processing ≈ SAR 39.5 + insurance ≈ SAR 13)", "entry": "multiple within 3 months",
     "notes": "For Saudia/flynas transits; Umrah is permitted during its validity."},
]
_VISA_TYPES_SA_UMRAH = [
    {"name": "Umrah visa", "duration": "up to 90 days stay (must enter within 30 days of issuance)",
     "fee": "from ≈ SAR 300 (varies by package)", "entry": "single entry",
     "notes": "The primary route for Pakistani pilgrims. Requires a sponsored package with pre-booked Makkah/Madinah hotels and transport, applied through a licensed agent via the Nusuk / Masar system. Nusuk is mandatory for all pilgrims."},
    {"name": "Tourist eVisa (if eligible)", "duration": "90 days per visit",
     "fee": "≈ SAR 480", "entry": "multiple entry",
     "notes": "Permits Umrah outside the Hajj season, but Pakistani passport holders are generally not eligible — most use the Umrah visa."},
]
_VISA_TYPES_SA_HAJJ = [
    {"name": "Hajj visa", "duration": "valid for the Hajj season only",
     "fee": "included in the Hajj package", "entry": "single entry",
     "notes": "Quota-based, issued only via the Nusuk Hajj platform or an approved operator. A tourist, Umrah or transit visa is NOT valid for Hajj."},
]
_VISA_TYPES_PK = [
    {"name": "Tourist eVisa", "duration": "up to 90 days",
     "fee": "USD 8–60 (nationality dependent)", "entry": "single/multiple",
     "notes": "Apply online via the NADRA visa portal."},
    {"name": "NICOP / POC", "duration": "long-term",
     "fee": "varies", "entry": "multiple entry",
     "notes": "For overseas Pakistanis and persons of Pakistani origin — no separate visa needed."},
]

# ---------------------------------------------------------------------------
# Step-by-step preparation guides (from Pakistan). Each step:
# {title, detail, url (official source), fee, timeline}. Fees/timelines are
# indicative demo values — always verify with the linked official source.
# ---------------------------------------------------------------------------
_PREP_AE_TOURISM = [
    {"title": "1. Get / renew your passport",
     "detail": "Make sure your machine-readable or e-passport is valid for at least 6 months beyond your travel dates. Apply or renew at a DGIP Passport office.",
     "url": "https://dgip.gov.pk", "fee": "PKR 4,500–27,500 (normal to urgent)", "timeline": "7–21 working days"},
    {"title": "2. Prepare photographs & documents",
     "detail": "Arrange 2 recent passport-size photos (white background), a copy of your CNIC, and your passport's first page.",
     "url": "", "fee": "PKR 500–1,500", "timeline": "Same day"},
    {"title": "3. Attest documents (only if required)",
     "detail": "Tourism usually needs no attestation. If you carry educational/employment documents (e.g. for a longer stay), get them attested by IBCC/HEC, then MOFA Pakistan, then the UAE Embassy.",
     "url": "https://mofa.gov.pk", "fee": "PKR 500–2,000 per document", "timeline": "2–7 working days"},
    {"title": "4. Apply for the UAE tourist visa",
     "detail": "Apply through an airline (Emirates/Etihad/flydubai), a licensed travel agent, or the UAE ICP / GDRFA portal. Choose 30-day or 60-day tourist visa. You'll need your passport scan, photo, ticket and hotel booking.",
     "url": "https://icp.gov.ae", "fee": "AED 350–700 (≈ PKR 27,000–54,000)", "timeline": "3–5 working days"},
    {"title": "5. Book flights & hotel",
     "detail": "Book a confirmed return/onward ticket and accommodation (required for the visa). Use the Book links on this page to compare and reserve.",
     "url": "", "fee": "Varies", "timeline": "Same day"},
    {"title": "6. Travel insurance & proof of funds",
     "detail": "Arrange travel/health insurance (recommended) and keep a recent bank statement as proof of sufficient funds.",
     "url": "", "fee": "PKR 2,000–6,000", "timeline": "1–2 days"},
    {"title": "7. Final checks before you fly",
     "detail": "Carry printed visa, ticket, hotel booking and insurance. Confirm your passport, visa and vaccination (if any) are in order.",
     "url": "https://u.ae/en/information-and-services/visa-and-emirates-id", "fee": "—", "timeline": "Before departure"},
]

_PREP_SA_UMRAH = [
    {"title": "1. Valid passport",
     "detail": "Ensure your passport is valid for at least 6 months beyond your travel dates; renew at DGIP if needed.",
     "url": "https://dgip.gov.pk", "fee": "PKR 4,500–27,500", "timeline": "7–21 working days"},
    {"title": "2. Mandatory vaccinations",
     "detail": "Get the meningococcal (ACWY) vaccine — MANDATORY, certificate issued at least 10 days before arrival — and a polio (OPV) dose, required for travellers from Pakistan. Vaccinate at an authorized government centre.",
     "url": "https://www.nhsrc.gov.pk", "fee": "PKR 2,500–6,000", "timeline": "Certificate valid 10 days+ before travel"},
    {"title": "3. Photographs & documents",
     "detail": "Arrange recent white-background photos, CNIC copy, and (for women) mahram/relationship documents if applicable. Women may travel without a mahram under current rules — verify first.",
     "url": "", "fee": "PKR 500–1,500", "timeline": "Same day"},
    {"title": "4. Apply for the Umrah visa (Nusuk)",
     "detail": "Apply through the Nusuk platform/app or an approved Umrah operator. You'll choose a package (visa + hotel + sometimes transport) and upload your passport and photo.",
     "url": "https://www.nusuk.sa", "fee": "SAR 300+ (visa) + package", "timeline": "3–7 working days"},
    {"title": "5. Book flights & Makkah/Madinah hotels",
     "detail": "Confirm return flights and hotels close to the Haram (often part of the Nusuk package). Use the Book links on this page to compare.",
     "url": "", "fee": "Varies by package", "timeline": "Same day"},
    {"title": "6. Nusuk permits (Rawdah & prayers)",
     "detail": "Use the Nusuk app to book your Umrah permit and Rawdah/prayer slots after your visa is issued.",
     "url": "https://www.nusuk.sa", "fee": "Free", "timeline": "After visa issuance"},
    {"title": "7. Pack Ihram & final checks",
     "detail": "Carry Ihram clothing, your vaccination certificates, visa, ticket and hotel confirmation. Keep the Nusuk app installed.",
     "url": "", "fee": "—", "timeline": "Before departure"},
]

_PREP_SA_HAJJ = [
    {"title": "1. Valid passport",
     "detail": "Passport valid for at least 6 months beyond travel. Renew at DGIP if required.",
     "url": "https://dgip.gov.pk", "fee": "PKR 4,500–27,500", "timeline": "7–21 working days"},
    {"title": "2. Register for Hajj",
     "detail": "Register under the Government Hajj Scheme via the Ministry of Religious Affairs (Pakistan), or book through an approved private Hajj operator / Nusuk Hajj. A tourist or Umrah visa is NOT valid for Hajj.",
     "url": "https://www.mora.gov.pk", "fee": "Scheme/package dependent", "timeline": "Seasonal — apply early"},
    {"title": "3. Mandatory vaccinations",
     "detail": "Meningococcal (ACWY) is mandatory; polio (OPV) is required for Pakistan travellers. Seasonal influenza and COVID-19 are strongly recommended.",
     "url": "https://www.nhsrc.gov.pk", "fee": "PKR 2,500–6,000", "timeline": "10+ days before travel"},
    {"title": "4. Hajj visa & package",
     "detail": "Your Hajj visa is issued through your operator or the Nusuk Hajj platform along with a confirmed package covering Makkah, Mina, Arafat and Muzdalifah.",
     "url": "https://www.nusuk.sa", "fee": "Included in package", "timeline": "Before the Hajj window"},
    {"title": "5. Mahram documents (for women)",
     "detail": "Prepare relationship/mahram documents if applicable per your operator's and the current Saudi rules.",
     "url": "", "fee": "—", "timeline": "With application"},
    {"title": "6. Hajj orientation & packing",
     "detail": "Attend your operator's Hajj training, pack Ihram, carry all certificates, your visa, wristband/ID and medication.",
     "url": "", "fee": "—", "timeline": "Before departure"},
]

_PREP_SA_TOURISM = [
    {"title": "1. Valid passport",
     "detail": "Passport valid for at least 6 months beyond travel.",
     "url": "https://dgip.gov.pk", "fee": "PKR 4,500–27,500", "timeline": "7–21 working days"},
    {"title": "2. Apply for the Saudi tourist eVisa",
     "detail": "Apply online via Visit Saudi / the Saudi MOFA eVisa portal. The eVisa usually includes mandatory travel insurance.",
     "url": "https://visa.visitsaudi.com", "fee": "≈ SAR 300–480 (incl. insurance)", "timeline": "Instant to a few days"},
    {"title": "3. Book flights & hotel",
     "detail": "Confirm your flights and accommodation. Use the Book links on this page to compare options.",
     "url": "", "fee": "Varies", "timeline": "Same day"},
    {"title": "4. Final checks",
     "detail": "Carry your eVisa, ticket and hotel booking. Respect local dress and conduct rules.",
     "url": "https://www.visitsaudi.com", "fee": "—", "timeline": "Before departure"},
]

_PREP_PK = [
    {"title": "1. Valid passport",
     "detail": "Ensure your passport is valid for at least 6 months beyond travel.",
     "url": "", "fee": "Varies by country", "timeline": "Varies"},
    {"title": "2. Apply for a Pakistan visa / NICOP",
     "detail": "Apply for the appropriate visa through the NADRA online visa portal, or carry your NICOP/POC if eligible.",
     "url": "https://visa.nadra.gov.pk", "fee": "USD 8–60 (visa dependent)", "timeline": "3–7 working days"},
    {"title": "3. Book flights & accommodation",
     "detail": "Confirm your flights and accommodation / host details. Use the Book links on this page.",
     "url": "", "fee": "Varies", "timeline": "Same day"},
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
        "preparation": _PREP_AE_TOURISM,
        "visa_types": _VISA_TYPES_AE,
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
        "preparation": _PREP_PK,
        "visa_types": _VISA_TYPES_PK,
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
        "preparation": _PREP_SA_TOURISM,
        "visa_types": _VISA_TYPES_SA_TOURISM,
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
        "preparation": _PREP_SA_UMRAH,
        "visa_types": _VISA_TYPES_SA_UMRAH,
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
        "preparation": _PREP_SA_HAJJ,
        "visa_types": _VISA_TYPES_SA_HAJJ,
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
