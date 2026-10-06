"""
Stripe integration: customers, Checkout, billing portal, catalog setup and
webhook handling. The Stripe SDK is synchronous, so calls run in a threadpool to
avoid blocking the event loop. When no key is configured, callers get a clear
"billing not configured" error (503).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.entitlements import PAID_PLANS
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.models.billing import Payment, Plan, Subscription
from app.models.user import User
from app.services.billing import entitlement_service

logger = get_logger("stripe")


def is_configured() -> bool:
    return bool(get_settings().stripe_secret_key)


def _require() -> None:
    if not is_configured():
        raise AppError("Billing is not configured on the server.", code="billing_unconfigured", status_code=503)
    stripe.api_key = get_settings().stripe_secret_key


async def _get_or_create_sub_row(session: AsyncSession, user_id: uuid.UUID) -> Subscription:
    sub = await entitlement_service.get_subscription(session, user_id)
    if sub is None:
        sub = Subscription(user_id=user_id, status="incomplete")
        session.add(sub)
        await session.flush()
    return sub


async def get_or_create_customer(session: AsyncSession, user: User) -> str:
    _require()
    sub = await _get_or_create_sub_row(session, user.id)
    if sub.stripe_customer_id:
        return sub.stripe_customer_id
    customer = await run_in_threadpool(
        lambda: stripe.Customer.create(email=user.email, name=user.full_name or None,
                                       metadata={"user_id": str(user.id)})
    )
    sub.stripe_customer_id = customer["id"]
    await session.flush()
    return customer["id"]


async def create_checkout_session(session: AsyncSession, user: User, plan_code: str) -> str:
    _require()
    plan = await entitlement_service.get_plan_by_code(session, plan_code)
    if not plan or plan_code not in PAID_PLANS:
        raise AppError("Unknown or non-purchasable plan.", code="invalid_plan", status_code=400)
    if not plan.stripe_price_id:
        raise AppError("This plan is not yet available for purchase.", code="plan_not_ready", status_code=409)

    customer_id = await get_or_create_customer(session, user)
    settings = get_settings()
    checkout = await run_in_threadpool(
        lambda: stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
            success_url=settings.billing_success_url,
            cancel_url=settings.billing_cancel_url,
            client_reference_id=str(user.id),
            metadata={"user_id": str(user.id), "plan_code": plan_code},
            allow_promotion_codes=True,
        )
    )
    return checkout["url"]


async def create_portal_session(session: AsyncSession, user: User) -> str:
    _require()
    sub = await entitlement_service.get_subscription(session, user.id)
    if not sub or not sub.stripe_customer_id:
        raise AppError("No billing account yet. Subscribe to a plan first.", code="no_customer", status_code=400)
    portal = await run_in_threadpool(
        lambda: stripe.billing_portal.Session.create(
            customer=sub.stripe_customer_id, return_url=get_settings().billing_cancel_url
        )
    )
    return portal["url"]


async def create_catalog(session: AsyncSession) -> list[dict]:
    """Create Stripe Products/Prices for paid plans and store IDs.

    Idempotent across fresh databases via a stable Price `lookup_key`, so a
    redeploy reuses existing Stripe prices instead of creating duplicates.
    """
    _require()
    out = []
    for code in PAID_PLANS:
        plan = await entitlement_service.get_plan_by_code(session, code)
        if not plan:
            continue
        if plan.stripe_price_id:
            out.append({"plan": code, "price_id": plan.stripe_price_id, "created": False})
            continue

        lookup_key = f"journeyjunction_{code}"
        existing = await run_in_threadpool(
            lambda lk=lookup_key: stripe.Price.list(lookup_keys=[lk], limit=1)
        )
        if existing["data"]:
            price = existing["data"][0]
            plan.stripe_product_id = price["product"]
            plan.stripe_price_id = price["id"]
            await session.flush()
            out.append({"plan": code, "price_id": price["id"], "created": False})
            continue

        product = await run_in_threadpool(
            lambda p=plan: stripe.Product.create(name=f"Journey Junction {p.name}", metadata={"plan_code": p.code})
        )
        price = await run_in_threadpool(
            lambda p=plan, pr=product, lk=lookup_key: stripe.Price.create(
                product=pr["id"], unit_amount=p.price_cents, currency=p.currency.lower(),
                recurring={"interval": p.interval}, lookup_key=lk, metadata={"plan_code": p.code},
            )
        )
        plan.stripe_product_id = product["id"]
        plan.stripe_price_id = price["id"]
        await session.flush()
        out.append({"plan": code, "price_id": price["id"], "created": True})
    return out


async def _upsert_subscription(session: AsyncSession, *, user_id, plan, customer_id, sub_id, status, period_end):
    sub = await entitlement_service.get_subscription(session, user_id)
    if sub is None:
        sub = Subscription(user_id=user_id)
        session.add(sub)
    sub.plan_id = plan.id if plan else sub.plan_id
    sub.stripe_customer_id = customer_id or sub.stripe_customer_id
    sub.stripe_subscription_id = sub_id or sub.stripe_subscription_id
    sub.status = status
    sub.current_period_end = period_end
    await session.flush()


async def _plan_from_subscription_obj(session: AsyncSession, sub_obj: dict) -> Plan | None:
    try:
        price_id = sub_obj["items"]["data"][0]["price"]["id"]
    except (KeyError, IndexError):
        return None
    return await session.scalar(select(Plan).where(Plan.stripe_price_id == price_id))


async def handle_webhook(session: AsyncSession, payload: bytes, sig_header: str) -> str:
    settings = get_settings()
    if not settings.stripe_webhook_secret:
        raise AppError("Webhook secret not configured.", code="webhook_unconfigured", status_code=503)
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except (ValueError, stripe.SignatureVerificationError) as exc:
        raise AppError("Invalid webhook signature.", code="invalid_signature", status_code=400) from exc

    etype = event["type"]
    obj = event["data"]["object"]
    logger.info("stripe_webhook", event_type=etype)

    if etype == "checkout.session.completed":
        user_id = (obj.get("metadata") or {}).get("user_id") or obj.get("client_reference_id")
        plan_code = (obj.get("metadata") or {}).get("plan_code")
        if user_id:
            plan = await entitlement_service.get_plan_by_code(session, plan_code) if plan_code else None
            await _upsert_subscription(
                session, user_id=uuid.UUID(user_id), plan=plan,
                customer_id=obj.get("customer"), sub_id=obj.get("subscription"),
                status="active", period_end=None,
            )
    elif etype in ("customer.subscription.updated", "customer.subscription.created"):
        plan = await _plan_from_subscription_obj(session, obj)
        sub = await session.scalar(
            select(Subscription).where(Subscription.stripe_customer_id == obj.get("customer"))
        )
        if sub:
            if plan:
                sub.plan_id = plan.id
            sub.stripe_subscription_id = obj.get("id") or sub.stripe_subscription_id
            sub.status = obj.get("status", sub.status)
            cpe = obj.get("current_period_end")
            sub.current_period_end = datetime.fromtimestamp(cpe, tz=timezone.utc) if cpe else None
            await session.flush()
    elif etype == "customer.subscription.deleted":
        sub = await session.scalar(
            select(Subscription).where(Subscription.stripe_customer_id == obj.get("customer"))
        )
        if sub:
            sub.status = "canceled"
            await session.flush()
    elif etype in ("invoice.paid", "invoice.payment_failed"):
        sub = await session.scalar(
            select(Subscription).where(Subscription.stripe_customer_id == obj.get("customer"))
        )
        session.add(Payment(
            user_id=sub.user_id if sub else None,
            stripe_invoice_id=obj.get("id", ""), amount_cents=obj.get("amount_paid", 0) or obj.get("amount_due", 0),
            currency=(obj.get("currency") or "usd").upper(),
            status="paid" if etype == "invoice.paid" else "failed",
        ))
        if etype == "invoice.payment_failed" and sub:
            sub.status = "past_due"
        await session.flush()

    return etype
