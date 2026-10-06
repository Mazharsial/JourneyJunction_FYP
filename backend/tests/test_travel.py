"""Integration tests for Phase 5 — locations & core travel."""
from __future__ import annotations

from datetime import date, timedelta

START = (date.today() + timedelta(days=10)).isoformat()
END = (date.today() + timedelta(days=14)).isoformat()


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _token(client, email="trav@example.com") -> str:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "TravelPass9!", "full_name": "Trav"},
    )
    return r.json()["tokens"]["access_token"]


async def _city_id(client, name: str, country: str) -> str:
    cities = (await client.get(f"/api/v1/locations/cities?country={country}")).json()
    return next(c["id"] for c in cities if c["name"] == name)


# ---- locations ----
async def test_list_countries_includes_uae(client):
    r = await client.get("/api/v1/locations/countries")
    assert r.status_code == 200
    assert any(c["iso2"] == "AE" for c in r.json())


async def test_cities_filtered_by_country(client):
    r = await client.get("/api/v1/locations/cities?country=AE")
    assert r.status_code == 200
    names = [c["name"] for c in r.json()]
    assert "Dubai" in names
    assert all(c["country_iso2"] == "AE" for c in r.json())


async def test_visa_lookup(client):
    r = await client.get("/api/v1/locations/visa?origin=PK&destination=AE")
    assert r.status_code == 200
    body = r.json()
    assert body["found"] is True
    assert body["rule"]["requirement"] == "visa_required"
    assert "disclaimer" in body


async def test_default_market_is_dubai(client):
    r = await client.get("/api/v1/locations/market")
    assert r.json()["city"] == "Dubai"


# ---- search ----
async def test_flight_search_requires_auth(client):
    r = await client.get(f"/api/v1/flights/search?origin=LHE&destination=DXB&date={START}")
    assert r.status_code == 401


async def test_flight_search_returns_sorted_offers(client):
    token = await _token(client)
    r = await client.get(
        f"/api/v1/flights/search?origin=LHE&destination=DXB&date={START}&budget=medium&travelers=2",
        headers=auth_header(token),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["currency"] == "AED"
    offers = body["offers"]
    assert len(offers) >= 1
    prices = [o["price_amount"] for o in offers]
    assert prices == sorted(prices)


async def test_hotel_search(client):
    token = await _token(client)
    r = await client.get(
        f"/api/v1/hotels/search?city=Dubai&iata=DXB&checkin={START}&checkout={END}&budget=luxury",
        headers=auth_header(token),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["nights"] == 4
    assert len(body["offers"]) >= 1
    assert all(o["rating"] >= 4.5 for o in body["offers"])  # luxury tier floor


# ---- trips ----
async def test_create_list_and_detail_trip(client):
    token = await _token(client)
    dest = await _city_id(client, "Dubai", "AE")
    origin = await _city_id(client, "Lahore", "PK")

    created = await client.post(
        "/api/v1/trips",
        headers=auth_header(token),
        json={
            "destination_city_id": dest,
            "origin_city_id": origin,
            "start_date": START,
            "end_date": END,
            "budget_tier": "medium",
            "travelers": 2,
        },
    )
    assert created.status_code == 201, created.text
    trip = created.json()
    assert trip["destination"]["name"] == "Dubai"
    assert trip["title"] == "Trip to Dubai"

    listed = await client.get("/api/v1/trips", headers=auth_header(token))
    assert listed.status_code == 200
    assert any(t["id"] == trip["id"] for t in listed.json())

    detail = await client.get(f"/api/v1/trips/{trip['id']}", headers=auth_header(token))
    assert detail.status_code == 200
    d = detail.json()
    assert len(d["itinerary"]) == 5  # inclusive day count for START..END
    assert len(d["suggested_flights"]) >= 1
    assert len(d["suggested_hotels"]) >= 1
    assert d["visa"]["requirement"] == "visa_required"  # PK -> AE
    # Every offer carries an authentic booking/verify link.
    assert d["suggested_flights"][0]["booking_url"].startswith("http")
    assert d["suggested_hotels"][0]["booking_url"].startswith("http")
    # Destination carries a step-by-step preparation guide.
    assert len(d["requirements"]["preparation"]) >= 3


async def test_trip_detail_includes_travel_requirements(client):
    token = await _token(client, "reqs@example.com")
    dest = await _city_id(client, "Dubai", "AE")
    origin = await _city_id(client, "Lahore", "PK")
    created = await client.post(
        "/api/v1/trips",
        headers=auth_header(token),
        json={"destination_city_id": dest, "origin_city_id": origin,
              "start_date": START, "end_date": END},
    )
    trip_id = created.json()["id"]

    d = (await client.get(f"/api/v1/trips/{trip_id}", headers=auth_header(token))).json()
    req = d["requirements"]
    assert req is not None
    assert req["destination_country"] == "United Arab Emirates"
    assert req["passport_validity_months"] == 6
    assert req["visa"]["requirement"] == "visa_required"
    assert len(req["required_documents"]) >= 3
    assert req["currency_notes"] and req["official_source"]
    # No documents uploaded yet -> compliance shows nothing verified.
    assert req["documents_required"] >= 1
    assert req["documents_ready"] == 0
    passport = next(x for x in req["required_documents"] if x["doc_type"] == "passport")
    assert passport["status"] == "not_verified"


async def test_saudi_cities_available(client):
    cities = (await client.get("/api/v1/locations/cities?country=SA")).json()
    names = [c["name"] for c in cities]
    assert {"Makkah", "Madinah", "Jeddah"}.issubset(set(names))
    assert all(c["country_iso2"] == "SA" for c in cities)


async def test_umrah_trip_has_pilgrimage_requirements(client):
    token = await _token(client, "umrah@example.com")
    makkah = await _city_id(client, "Makkah", "SA")
    karachi = await _city_id(client, "Karachi", "PK")
    created = await client.post(
        "/api/v1/trips",
        headers=auth_header(token),
        json={"destination_city_id": makkah, "origin_city_id": karachi,
              "start_date": START, "end_date": END, "purpose": "umrah"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["purpose"] == "umrah"
    assert created.json()["title"] == "Umrah to Makkah"

    d = (await client.get(f"/api/v1/trips/{created.json()['id']}", headers=auth_header(token))).json()
    req = d["requirements"]
    assert req["purpose"] == "umrah"
    assert req["destination_country"] == "Saudi Arabia"
    assert "nusuk" in req["official_source"].lower()
    # Mandatory meningococcal vaccination is the defining pilgrimage health rule.
    assert any("meningococcal" in h.lower() for h in req["health"])
    labels = " ".join(x["label"].lower() for x in req["required_documents"])
    assert "nusuk" in labels or "umrah visa" in labels
    # Umrah preparation guide includes the mandatory-vaccination step with a link.
    prep = req["preparation"]
    assert len(prep) >= 5
    assert any("vaccinat" in s["title"].lower() or "vaccinat" in s["detail"].lower() for s in prep)
    assert any(s["url"].startswith("http") for s in prep)


async def test_pilgrimage_requires_saudi_destination(client):
    token = await _token(client, "badpilgrim@example.com")
    dubai = await _city_id(client, "Dubai", "AE")
    r = await client.post(
        "/api/v1/trips",
        headers=auth_header(token),
        json={"destination_city_id": dubai, "start_date": START, "end_date": END,
              "purpose": "hajj"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_pilgrimage_destination"


async def test_trip_is_idor_safe(client):
    a_token = await _token(client, "owner@example.com")
    dest = await _city_id(client, "Dubai", "AE")
    created = await client.post(
        "/api/v1/trips",
        headers=auth_header(a_token),
        json={"destination_city_id": dest, "start_date": START, "end_date": END},
    )
    trip_id = created.json()["id"]

    b_token = await _token(client, "intruder@example.com")
    stolen = await client.get(f"/api/v1/trips/{trip_id}", headers=auth_header(b_token))
    assert stolen.status_code == 404  # not 403 — do not leak existence


async def test_create_trip_rejects_bad_dates(client):
    token = await _token(client)
    dest = await _city_id(client, "Dubai", "AE")
    # end before start
    r = await client.post(
        "/api/v1/trips",
        headers=auth_header(token),
        json={"destination_city_id": dest, "start_date": END, "end_date": START},
    )
    assert r.status_code == 422
    # start in the past
    past = (date.today() - timedelta(days=2)).isoformat()
    r2 = await client.post(
        "/api/v1/trips",
        headers=auth_header(token),
        json={"destination_city_id": dest, "start_date": past, "end_date": END},
    )
    assert r2.status_code == 422
