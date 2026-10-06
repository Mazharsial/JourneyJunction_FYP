"""Admin schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    roles: list[str] = []


class UsersPage(BaseModel):
    items: list[AdminUserOut]
    total: int
    limit: int
    offset: int


class UserUpdate(BaseModel):
    is_active: bool | None = None
    is_verified: bool | None = None
    roles: list[str] | None = None


class RoleOut(BaseModel):
    name: str
    description: str
    permissions: list[str]


class PlanFeatureUpdate(BaseModel):
    feature_key: str
    enabled: bool | None = None
    limit_value: int | None = None


class VisaRuleIn(BaseModel):
    origin: str
    destination: str
    requirement: str
    allowed_stay_days: int | None = None
    notes: str = ""
    source: str = ""


class VisaRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    origin_iso2: str
    destination_iso2: str
    requirement: str
    allowed_stay_days: int | None
    notes: str
    source: str


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    actor_user_id: uuid.UUID | None
    action: str
    entity: str
    entity_id: str
    meta: dict
    ip: str
    created_at: datetime


class AuditPage(BaseModel):
    items: list[AuditLogOut]
    total: int
