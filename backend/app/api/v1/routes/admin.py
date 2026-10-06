"""Admin endpoints (permission-gated, audited)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permissions
from app.core.rbac import Perms
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import (
    AdminUserOut,
    AuditLogOut,
    AuditPage,
    PlanFeatureUpdate,
    RoleOut,
    UserUpdate,
    UsersPage,
    VisaRuleIn,
    VisaRuleOut,
)
from app.schemas.billing import FeatureOut, PlanOut
from app.services import admin_service
from app.core.entitlements import PAID_PLANS

router = APIRouter()


def _ip(request: Request) -> str:
    return request.client.host if request.client else ""


def _user_out(u: User) -> AdminUserOut:
    return AdminUserOut(
        id=u.id, email=u.email, full_name=u.full_name, is_active=u.is_active,
        is_verified=u.is_verified, created_at=u.created_at, roles=sorted(u.role_names),
    )


@router.get("/stats")
async def stats(db: AsyncSession = Depends(get_db), _: User = Depends(require_permissions(Perms.USER_MANAGE))):
    return await admin_service.stats(db)


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db), _: User = Depends(require_permissions(Perms.USER_MANAGE))):
    return await admin_service.health(db)


@router.get("/users", response_model=UsersPage)
async def users(
    q: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions(Perms.USER_MANAGE)),
):
    rows, total = await admin_service.list_users(db, q=q, limit=limit, offset=offset)
    return UsersPage(items=[_user_out(u) for u in rows], total=total, limit=limit, offset=offset)


@router.get("/users/{user_id}", response_model=AdminUserOut)
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                   _: User = Depends(require_permissions(Perms.USER_MANAGE))):
    from app.core.exceptions import AppError
    u = await admin_service.get_user(db, user_id)
    if not u:
        raise AppError("User not found.", code="user_not_found", status_code=404)
    return _user_out(u)


@router.patch("/users/{user_id}", response_model=AdminUserOut)
async def update_user(
    user_id: uuid.UUID, payload: UserUpdate, request: Request,
    db: AsyncSession = Depends(get_db), actor: User = Depends(require_permissions(Perms.USER_MANAGE)),
):
    u = await admin_service.update_user(
        db, actor=actor, target_id=user_id, is_active=payload.is_active,
        is_verified=payload.is_verified, role_names=payload.roles, ip=_ip(request),
    )
    return _user_out(u)


@router.get("/roles", response_model=list[RoleOut])
async def roles(db: AsyncSession = Depends(get_db), _: User = Depends(require_permissions(Perms.USER_MANAGE))):
    rows = await admin_service.list_roles(db)
    return [RoleOut(name=r.name, description=r.description, permissions=sorted(p.code for p in r.permissions))
            for r in rows]


@router.get("/plans", response_model=list[PlanOut])
async def plans(db: AsyncSession = Depends(get_db), _: User = Depends(require_permissions(Perms.PLAN_MANAGE))):
    rows = await admin_service.list_plans(db)
    return [
        PlanOut(code=p.code, name=p.name, description=p.description, price_cents=p.price_cents,
                currency=p.currency, interval=p.interval,
                purchasable=(p.code in PAID_PLANS and bool(p.stripe_price_id)),
                features=[FeatureOut(feature_key=f.feature_key, enabled=f.enabled, limit_value=f.limit_value)
                          for f in p.features])
        for p in rows
    ]


@router.patch("/plans/{plan_code}/features", response_model=PlanOut)
async def update_plan_feature(
    plan_code: str, payload: PlanFeatureUpdate, request: Request,
    db: AsyncSession = Depends(get_db), actor: User = Depends(require_permissions(Perms.PLAN_MANAGE)),
):
    p = await admin_service.update_plan_feature(
        db, actor=actor, plan_code=plan_code, feature_key=payload.feature_key,
        enabled=payload.enabled, limit_value=payload.limit_value, ip=_ip(request),
    )
    return PlanOut(code=p.code, name=p.name, description=p.description, price_cents=p.price_cents,
                   currency=p.currency, interval=p.interval,
                   purchasable=(p.code in PAID_PLANS and bool(p.stripe_price_id)),
                   features=[FeatureOut(feature_key=f.feature_key, enabled=f.enabled, limit_value=f.limit_value)
                             for f in p.features])


@router.get("/visa-rules", response_model=list[VisaRuleOut])
async def visa_rules(db: AsyncSession = Depends(get_db), _: User = Depends(require_permissions(Perms.CONFIG_MANAGE))):
    return await admin_service.list_visa_rules(db)


@router.put("/visa-rules", response_model=VisaRuleOut)
async def upsert_visa_rule(
    payload: VisaRuleIn, request: Request,
    db: AsyncSession = Depends(get_db), actor: User = Depends(require_permissions(Perms.CONFIG_MANAGE)),
):
    return await admin_service.upsert_visa_rule(
        db, actor=actor, origin=payload.origin, destination=payload.destination,
        requirement=payload.requirement, allowed_stay_days=payload.allowed_stay_days,
        notes=payload.notes, source=payload.source, ip=_ip(request),
    )


@router.delete("/visa-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_visa_rule(
    rule_id: uuid.UUID, request: Request,
    db: AsyncSession = Depends(get_db), actor: User = Depends(require_permissions(Perms.CONFIG_MANAGE)),
):
    await admin_service.delete_visa_rule(db, actor=actor, rule_id=rule_id, ip=_ip(request))


@router.get("/audit-logs", response_model=AuditPage)
async def audit_logs(
    limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db), _: User = Depends(require_permissions(Perms.AUDIT_VIEW)),
):
    rows, total = await admin_service.list_audit_logs(db, limit=limit, offset=offset)
    return AuditPage(items=[AuditLogOut.model_validate(r) for r in rows], total=total)
