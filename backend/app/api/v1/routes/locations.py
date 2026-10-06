"""Location & configuration (reference data, public)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.db.session import get_db
from app.schemas.location import (
    CityOut,
    CountryOut,
    CurrencyOut,
    VisaResponse,
    VisaRuleOut,
)
from app.services import location_service

router = APIRouter()


@router.get("/countries", response_model=list[CountryOut])
async def countries(db: AsyncSession = Depends(get_db)):
    if (hit := cache.get("loc:countries")) is not None:
        return hit
    out = [CountryOut.model_validate(c) for c in await location_service.list_countries(db)]
    cache.set("loc:countries", out)
    return out


@router.get("/currencies", response_model=list[CurrencyOut])
async def currencies(db: AsyncSession = Depends(get_db)):
    if (hit := cache.get("loc:currencies")) is not None:
        return hit
    out = [CurrencyOut.model_validate(c) for c in await location_service.list_currencies(db)]
    cache.set("loc:currencies", out)
    return out


@router.get("/cities", response_model=list[CityOut])
async def cities(
    country: str | None = Query(default=None, max_length=2, description="ISO2 filter"),
    db: AsyncSession = Depends(get_db),
):
    key = f"loc:cities:{(country or '').upper()}"
    if (hit := cache.get(key)) is not None:
        return hit
    out = [CityOut.model_validate(c) for c in await location_service.list_cities(db, country)]
    cache.set(key, out)
    return out


@router.get("/visa", response_model=VisaResponse)
async def visa(
    origin: str = Query(min_length=2, max_length=2),
    destination: str = Query(min_length=2, max_length=2),
    db: AsyncSession = Depends(get_db),
):
    key = f"loc:visa:{origin.upper()}:{destination.upper()}"
    if (hit := cache.get(key)) is not None:
        return hit
    rule = await location_service.get_visa_rule(db, origin, destination)
    out = VisaResponse(found=rule is not None, rule=VisaRuleOut.model_validate(rule) if rule else None)
    cache.set(key, out)
    return out


@router.get("/market")
async def market(db: AsyncSession = Depends(get_db)) -> dict:
    if (hit := cache.get("loc:market")) is not None:
        return hit
    out = await location_service.get_default_market(db)
    cache.set("loc:market", out)
    return out
