"""Billing schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class FeatureOut(BaseModel):
    feature_key: str
    enabled: bool
    limit_value: int


class PlanOut(BaseModel):
    code: str
    name: str
    description: str
    price_cents: int
    currency: str
    interval: str
    purchasable: bool
    features: list[FeatureOut]


class PlansResponse(BaseModel):
    plans: list[PlanOut]
    publishable_key: str
    billing_enabled: bool


class SubscriptionOut(BaseModel):
    plan_code: str
    plan_name: str
    status: str
    current_period_end: datetime | None
    usage: list[dict]


class CheckoutRequest(BaseModel):
    plan_code: str


class UrlResponse(BaseModel):
    url: str
