"""Location & configuration (reference data, public)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

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
    return await location_service.list_countries(db)


@router.get("/currencies", response_model=list[CurrencyOut])
async def currencies(db: AsyncSession = Depends(get_db)):
    return await location_service.list_currencies(db)


@router.get("/cities", response_model=list[CityOut])
async def cities(
    country: str | None = Query(default=None, max_length=2, description="ISO2 filter"),
    db: AsyncSession = Depends(get_db),
):
    return await location_service.list_cities(db, country)


@router.get("/visa", response_model=VisaResponse)
async def visa(
    origin: str = Query(min_length=2, max_length=2),
    destination: str = Query(min_length=2, max_length=2),
    db: AsyncSession = Depends(get_db),
):
    rule = await location_service.get_visa_rule(db, origin, destination)
    return VisaResponse(found=rule is not None, rule=VisaRuleOut.model_validate(rule) if rule else None)


@router.get("/market")
async def market(db: AsyncSession = Depends(get_db)) -> dict:
    return await location_service.get_default_market(db)
