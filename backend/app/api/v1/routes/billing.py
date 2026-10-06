"""Billing & subscription endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permissions
from app.core.config import get_settings
from app.core.entitlements import PAID_PLANS
from app.core.rbac import Perms
from app.db.session import get_db
from app.models.billing import Plan
from app.models.user import User
from app.schemas.billing import (
    CheckoutRequest,
    FeatureOut,
    PlanOut,
    PlansResponse,
    SubscriptionOut,
    UrlResponse,
)
from app.services.billing import entitlement_service, stripe_service

router = APIRouter()


@router.get("/plans", response_model=PlansResponse)
async def plans(db: AsyncSession = Depends(get_db)):
    rows = (await db.scalars(select(Plan).where(Plan.is_active.is_(True)).order_by(Plan.sort_order))).all()
    settings = get_settings()
    return PlansResponse(
        plans=[
            PlanOut(
                code=p.code, name=p.name, description=p.description, price_cents=p.price_cents,
                currency=p.currency, interval=p.interval,
                purchasable=(p.code in PAID_PLANS and bool(p.stripe_price_id)),
                features=[FeatureOut(feature_key=f.feature_key, enabled=f.enabled, limit_value=f.limit_value)
                          for f in p.features],
            )
            for p in rows
        ],
        publishable_key=settings.stripe_publishable_key,
        billing_enabled=stripe_service.is_configured(),
    )


@router.get("/subscription", response_model=SubscriptionOut)
async def subscription(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    plan = await entitlement_service.get_active_plan(db, user.id)
    sub = await entitlement_service.get_subscription(db, user.id)
    usage = await entitlement_service.usage_summary(db, user.id)
    return SubscriptionOut(
        plan_code=plan.code, plan_name=plan.name,
        status=sub.status if sub else "active",
        current_period_end=sub.current_period_end if sub else None,
        usage=usage,
    )


@router.post("/checkout", response_model=UrlResponse)
async def checkout(
    payload: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Perms.SUBSCRIPTION_MANAGE)),
):
    url = await stripe_service.create_checkout_session(db, user, payload.plan_code)
    return UrlResponse(url=url)


@router.post("/portal", response_model=UrlResponse)
async def portal(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Perms.SUBSCRIPTION_MANAGE)),
):
    url = await stripe_service.create_portal_session(db, user)
    return UrlResponse(url=url)


@router.post("/webhook")
async def webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    event_type = await stripe_service.handle_webhook(db, payload, sig)
    return {"received": True, "type": event_type}
