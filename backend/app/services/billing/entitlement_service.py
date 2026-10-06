"""
Plan resolution + server-side entitlement/usage enforcement.

The backend is the source of truth: even if the UI hides a feature, a direct API
call is still checked here. Limits are monthly; -1 = unlimited, 0 = disabled.
"""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.entitlements import DEFAULT_PLAN
from app.core.exceptions import AppError
from app.models.billing import Plan, Subscription, UsageCounter

_ACTIVE_STATUSES = {"active", "trialing", "past_due"}  # past_due still has access briefly


def current_period() -> str:
    return date.today().strftime("%Y-%m")


async def get_plan_by_code(session: AsyncSession, code: str) -> Plan | None:
    return await session.scalar(select(Plan).where(Plan.code == code))


async def get_subscription(session: AsyncSession, user_id: uuid.UUID) -> Subscription | None:
    return await session.scalar(select(Subscription).where(Subscription.user_id == user_id))


async def get_active_plan(session: AsyncSession, user_id: uuid.UUID) -> Plan:
    sub = await get_subscription(session, user_id)
    if sub and sub.plan and sub.status in _ACTIVE_STATUSES and sub.plan.code != DEFAULT_PLAN:
        return sub.plan
    plan = await get_plan_by_code(session, DEFAULT_PLAN)
    if not plan:
        raise AppError("Billing is not configured.", code="billing_unconfigured", status_code=500)
    return plan


def _entitlement(plan: Plan, feature_key: str):
    for f in plan.features:
        if f.feature_key == feature_key:
            return f.enabled, f.limit_value
    return False, 0


async def feature_enabled(session: AsyncSession, user_id: uuid.UUID, feature_key: str) -> bool:
    plan = await get_active_plan(session, user_id)
    enabled, _ = _entitlement(plan, feature_key)
    return enabled


async def _get_usage(session: AsyncSession, user_id: uuid.UUID, feature_key: str) -> UsageCounter | None:
    return await session.scalar(
        select(UsageCounter).where(
            UsageCounter.user_id == user_id,
            UsageCounter.feature_key == feature_key,
            UsageCounter.period == current_period(),
        )
    )


async def consume(session: AsyncSession, user_id: uuid.UUID, feature_key: str) -> dict:
    """Enforce a monthly limit and increment usage. Raises on denial."""
    plan = await get_active_plan(session, user_id)
    enabled, limit = _entitlement(plan, feature_key)
    if not enabled or limit == 0:
        raise AppError(
            "This feature isn't available on your plan. Please upgrade.",
            code="feature_not_in_plan", status_code=403,
        )
    if limit == -1:
        return {"unlimited": True, "plan": plan.code}

    row = await _get_usage(session, user_id, feature_key)
    used = row.count if row else 0
    if used >= limit:
        raise AppError(
            f"You've reached your monthly limit for this feature on the {plan.name} plan. "
            "Upgrade for more.",
            code="limit_reached", status_code=402,
        )
    if row is None:
        row = UsageCounter(user_id=user_id, feature_key=feature_key, period=current_period(), count=0)
        session.add(row)
    row.count = used + 1
    await session.flush()
    return {"plan": plan.code, "used": row.count, "limit": limit, "remaining": limit - row.count}


async def usage_summary(session: AsyncSession, user_id: uuid.UUID) -> list[dict]:
    plan = await get_active_plan(session, user_id)
    rows = {
        r.feature_key: r.count
        for r in (await session.scalars(
            select(UsageCounter).where(
                UsageCounter.user_id == user_id, UsageCounter.period == current_period()
            )
        )).all()
    }
    out = []
    for f in plan.features:
        if f.limit_value != -1 or f.feature_key in (rows or {}):
            out.append({
                "feature": f.feature_key, "enabled": f.enabled,
                "limit": f.limit_value, "used": rows.get(f.feature_key, 0),
            })
    return out
