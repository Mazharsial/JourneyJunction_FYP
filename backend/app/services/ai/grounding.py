"""
Intent detection and knowledge grounding for the travel assistant.

Deterministic, DB-backed: classifies the user's intent and pulls verified facts
(visa rules, city/country data, default market) so the model answers from real
data instead of hallucinating. Also powers the keyless grounded fallback.
"""
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import City, Country, VisaRule
from app.services import location_service

# Intent labels
VISA, FLIGHT, HOTEL, DESTINATION, PLAN, GREETING, OUT_OF_SCOPE = (
    "visa", "flight", "hotel", "destination", "plan", "greeting", "out_of_scope"
)

_COUNTRY_ALIASES = {
    "uae": "AE", "emirates": "AE", "dubai": "AE", "abu dhabi": "AE",
    "uk": "GB", "britain": "GB", "england": "GB", "united kingdom": "GB",
    "usa": "US", "america": "US", "united states": "US",
    "turkey": "TR", "türkiye": "TR", "turkiye": "TR",
    "pakistan": "PK", "saudi": "SA", "saudi arabia": "SA", "france": "FR",
}

_KW = {
    VISA: ["visa", "visas", "passport requirement", "entry requirement"],
    FLIGHT: ["flight", "flights", "fly", "airfare", "airline", "ticket", "fare"],
    HOTEL: ["hotel", "hotels", "accommodation", "stay", "room", "resort"],
    PLAN: ["plan a trip", "plan my trip", "itinerary", "plan trip", "organise", "organize", "help me plan"],
    DESTINATION: ["best time", "things to do", "attractions", "weather", "safe", "currency",
                  "language", "what to see", "when to go", "visit", "food", "about"],
    GREETING: ["hello", "hi ", "hey", "thanks", "thank you", "good morning", "good evening",
               "salam", "assalam"],
}


def _norm(t: str) -> str:
    return f" {t.lower().strip()} "


async def _location_maps(session: AsyncSession):
    countries = (await session.scalars(select(Country))).all()
    cities = (await session.scalars(select(City))).all()
    name_to_iso = {c.name.lower(): c.iso2 for c in countries}
    name_to_iso.update(_COUNTRY_ALIASES)
    city_to_iso = {c.name.lower(): c.country_iso2 for c in cities}
    iso_to_country = {c.iso2: c for c in countries}
    return name_to_iso, city_to_iso, iso_to_country, cities


def _match_iso(fragment: str, name_to_iso: dict, city_to_iso: dict) -> str | None:
    frag = fragment.lower()
    for name, iso in sorted(name_to_iso.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{re.escape(name)}\b", frag):
            return iso
    for city, iso in sorted(city_to_iso.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{re.escape(city)}\b", frag):
            return iso
    return None


def _extract_route(text: str, name_to_iso: dict, city_to_iso: dict):
    """Return (origin_iso2, destination_iso2), either may be None."""
    low = text.lower()
    origin = dest = None
    m_from = re.search(r"from\s+([a-zçğıöşü\s]+?)(?:\s+to\s+|\s+for\s+|[?.,]|$)", low)
    if m_from:
        origin = _match_iso(m_from.group(1), name_to_iso, city_to_iso)
    m_to = re.search(r"\bto\s+([a-zçğıöşü\s]+?)(?:[?.,]|$|\s+from\s+)", low)
    if m_to:
        dest = _match_iso(m_to.group(1), name_to_iso, city_to_iso)
    m_for = re.search(r"\bfor\s+([a-zçğıöşü\s]+?)(?:[?.,]|$|\s+from\s+)", low)
    if dest is None and m_for:
        dest = _match_iso(m_for.group(1), name_to_iso, city_to_iso)

    if origin is None or dest is None:
        # Fall back to first two distinct location mentions in order.
        found: list[str] = []
        tokens = re.findall(r"[a-zçğıöşü]+(?:\s+[a-zçğıöşü]+)?", low)
        for frag in tokens:
            iso = _match_iso(frag, name_to_iso, city_to_iso)
            if iso and iso not in found:
                found.append(iso)
        if origin is None and len(found) >= 1 and (dest is None or found[0] != dest):
            origin = found[0] if (dest is None or found[0] != dest) else None
        if dest is None and len(found) >= 2:
            dest = found[1]
        elif dest is None and len(found) == 1 and origin != found[0]:
            dest = found[0]
    return origin, dest


def detect_intent(text: str) -> str:
    t = _norm(text)
    # Greeting only when short and no travel keyword present.
    travel_hit = any(kw in t for group in (_KW[VISA], _KW[FLIGHT], _KW[HOTEL], _KW[PLAN]) for kw in group)
    if not travel_hit and any(kw in t for kw in _KW[GREETING]) and len(text.split()) <= 5:
        return GREETING
    for intent in (VISA, FLIGHT, HOTEL, PLAN):
        if any(kw in t for kw in _KW[intent]):
            return intent
    # Non-travel task words override the (broad) destination keywords.
    if any(w in t for w in _OOS_WORDS):
        return OUT_OF_SCOPE
    if any(kw in t for kw in _KW[DESTINATION]):
        return DESTINATION
    return DESTINATION if _has_location(text) else OUT_OF_SCOPE


_OOS_WORDS = [
    " write ", " poem", " code", " python", " javascript", " function", " calculate",
    " solve", " essay", " song", " story", " recipe", " homework", " math ",
]


_LOCATION_HINT = set(_COUNTRY_ALIASES.keys())


def _has_location(text: str) -> bool:
    low = f" {text.lower()} "
    return any(f" {h} " in low or h in low for h in _LOCATION_HINT)


async def build_context(session: AsyncSession, text: str) -> dict:
    name_to_iso, city_to_iso, iso_to_country, cities = await _location_maps(session)
    intent = detect_intent(text)
    facts: list[str] = []
    route = {"origin": None, "destination": None}

    if intent in (VISA, FLIGHT, HOTEL, PLAN, DESTINATION):
        origin, dest = _extract_route(text, name_to_iso, city_to_iso)
        route = {"origin": origin, "destination": dest}
        if intent == VISA and origin and dest and origin != dest:
            rule = await location_service.get_visa_rule(session, origin, dest)
            if rule:
                o = iso_to_country.get(origin)
                d = iso_to_country.get(dest)
                facts.append(
                    f"Visa rule {o.name if o else origin} -> {d.name if d else dest}: "
                    f"{rule.requirement.replace('_', ' ')}"
                    + (f", up to {rule.allowed_stay_days} days" if rule.allowed_stay_days else "")
                    + f". {rule.notes}"
                )
        if dest:
            d = iso_to_country.get(dest)
            if d:
                facts.append(f"Destination country: {d.name} (currency {d.currency_code}).")

    market = await location_service.get_default_market(session)
    return {"intent": intent, "route": route, "facts": facts, "market": market}


VISA_DISCLAIMER = (
    "Visa guidance is informational only and may change — always confirm with the "
    "official embassy or government source before travelling."
)


def grounded_fallback(text: str, ctx: dict) -> str:
    """Keyless answer composed from verified facts (used when Gemini is unavailable)."""
    intent = ctx["intent"]
    facts = ctx["facts"]
    if intent == GREETING:
        return "Hello! I'm your Journey Junction travel assistant. Ask me about visas, flights, hotels or planning a trip."
    if intent == VISA:
        if facts:
            return f"{facts[0]}\n\n{VISA_DISCLAIMER}"
        return ("I don't have a verified visa rule for that exact route yet. Please check the "
                "destination country's official immigration website. " + VISA_DISCLAIMER)
    if intent == OUT_OF_SCOPE:
        return ("I'm a travel assistant, so I can help with destinations, flights, hotels, "
                "itineraries and visa guidance. Could you ask me something travel-related?")
    if facts:
        return "Here's what I can tell you:\n- " + "\n- ".join(facts) + (
            f"\n\n{VISA_DISCLAIMER}" if intent == VISA else ""
        )
    return ("I can help you plan trips — try asking about flights, hotels, a destination, or "
            "whether you need a visa for a specific route.")
