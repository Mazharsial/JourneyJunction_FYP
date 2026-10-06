"""Idempotent seeding of subscription plans and feature entitlements."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.entitlements import PLAN_SPECS
from app.models.billing import Plan, PlanFeature


async def seed_billing(session: AsyncSession) -> None:
    existing = {p.code: p for p in (await session.scalars(select(Plan))).all()}
    for code, spec in PLAN_SPECS.items():
        plan = existing.get(code)
        if plan is None:
            plan = Plan(
                code=code, name=spec["name"], description=spec["description"],
                price_cents=spec["price_cents"], currency="USD", interval="month",
                sort_order=spec["sort_order"],
                features=[
                    PlanFeature(feature_key=k, enabled=en, limit_value=lim)
                    for k, (en, lim) in spec["features"].items()
                ],
            )
            session.add(plan)
        else:
            # Keep Stripe IDs; sync descriptive fields + entitlements.
            plan.name, plan.description = spec["name"], spec["description"]
            plan.price_cents, plan.sort_order = spec["price_cents"], spec["sort_order"]
            current = {f.feature_key: f for f in plan.features}
            for k, (en, lim) in spec["features"].items():
                if k in current:
                    current[k].enabled, current[k].limit_value = en, lim
                else:
                    plan.features.append(PlanFeature(feature_key=k, enabled=en, limit_value=lim))
    await session.flush()
