"""Read access to geographic & configuration data."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import AppConfig, City, Country, Currency, VisaRule


async def list_countries(session: AsyncSession) -> list[Country]:
    return list(
        (await session.scalars(
            select(Country).where(Country.is_active.is_(True)).order_by(Country.name)
        )).all()
    )


async def list_currencies(session: AsyncSession) -> list[Currency]:
    return list((await session.scalars(select(Currency).order_by(Currency.code))).all())


async def list_cities(session: AsyncSession, country_iso2: str | None = None) -> list[City]:
    stmt = select(City).where(City.is_active.is_(True))
    if country_iso2:
        stmt = stmt.where(City.country_iso2 == country_iso2.upper())
    return list((await session.scalars(stmt.order_by(City.name))).all())


async def get_city(session: AsyncSession, city_id: uuid.UUID) -> City | None:
    return await session.scalar(select(City).where(City.id == city_id))


async def get_visa_rule(
    session: AsyncSession, origin_iso2: str, destination_iso2: str
) -> VisaRule | None:
    return await session.scalar(
        select(VisaRule).where(
            VisaRule.origin_iso2 == origin_iso2.upper(),
            VisaRule.destination_iso2 == destination_iso2.upper(),
        )
    )


async def get_default_market(session: AsyncSession) -> dict:
    cfg = await session.scalar(select(AppConfig).where(AppConfig.key == "default_market"))
    return cfg.value if cfg else {}
