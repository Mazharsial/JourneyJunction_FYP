"""Administrative operations (admin/super-admin only) + audit logging."""
from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.rbac import Roles
from app.models.audit import AuditLog
from app.models.billing import Plan, PlanFeature, Subscription
from app.models.chat import AIRequest
from app.models.document import Document
from app.models.location import City, Country, VisaRule
from app.models.travel import Trip
from app.models.user import Role, User


async def record_audit(session, *, actor_id, action, entity="", entity_id="", meta=None, ip=""):
    session.add(AuditLog(
        actor_user_id=actor_id, action=action, entity=entity,
        entity_id=str(entity_id), meta=meta or {}, ip=ip,
    ))
    await session.flush()


async def _count(session, model) -> int:
    return int(await session.scalar(select(func.count()).select_from(model)) or 0)


async def stats(session: AsyncSession) -> dict:
    active_users = int(await session.scalar(
        select(func.count()).select_from(User).where(User.is_active.is_(True))
    ) or 0)
    by_plan_rows = (await session.execute(
        select(Plan.code, func.count(Subscription.id))
        .join(Subscription, Subscription.plan_id == Plan.id, isouter=True)
        .where(Subscription.status == "active")
        .group_by(Plan.code)
    )).all()
    return {
        "users_total": await _count(session, User),
        "users_active": active_users,
        "trips_total": await _count(session, Trip),
        "documents_total": await _count(session, Document),
        "ai_requests_total": await _count(session, AIRequest),
        "paid_subscriptions": {code: int(n) for code, n in by_plan_rows},
    }


async def list_users(session, *, q: str | None, limit: int, offset: int):
    stmt = select(User)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(User.email).like(like), func.lower(User.full_name).like(like)))
    total = int(await session.scalar(
        select(func.count()).select_from(stmt.subquery())
    ) or 0)
    rows = (await session.scalars(stmt.order_by(User.created_at.desc()).limit(limit).offset(offset))).all()
    return list(rows), total


async def get_user(session, user_id: uuid.UUID) -> User | None:
    return await session.scalar(select(User).where(User.id == user_id))


async def update_user(session, *, actor: User, target_id: uuid.UUID,
                      is_active=None, is_verified=None, role_names=None, ip="") -> User:
    target = await get_user(session, target_id)
    if not target:
        raise AppError("User not found.", code="user_not_found", status_code=404)

    if is_active is not None:
        if target.id == actor.id and is_active is False:
            raise AppError("You cannot deactivate your own account.", code="self_deactivate", status_code=400)
        target.is_active = is_active
    if is_verified is not None:
        target.is_verified = is_verified
    if role_names is not None:
        actor_is_super = Roles.SUPER_ADMIN in actor.role_names
        new_set = set(role_names)
        current_set = target.role_names
        # Only a super admin may grant or revoke the super_admin role.
        if (Roles.SUPER_ADMIN in (new_set ^ current_set)) and not actor_is_super:
            raise AppError("Only a super admin can change the super_admin role.", code="forbidden", status_code=403)
        roles = (await session.scalars(select(Role).where(Role.name.in_(new_set)))).all()
        target.roles = list(roles)

    await record_audit(session, actor_id=actor.id, action="user.update", entity="user",
                       entity_id=target.id, meta={"is_active": is_active, "is_verified": is_verified,
                                                   "roles": sorted(role_names) if role_names is not None else None},
                       ip=ip)
    await session.flush()
    return target


async def list_roles(session):
    return list((await session.scalars(select(Role).order_by(Role.name))).all())


async def list_plans(session):
    return list((await session.scalars(select(Plan).order_by(Plan.sort_order))).all())


async def update_plan_feature(session, *, actor: User, plan_code: str, feature_key: str,
                              enabled=None, limit_value=None, ip="") -> Plan:
    plan = await session.scalar(select(Plan).where(Plan.code == plan_code))
    if not plan:
        raise AppError("Plan not found.", code="plan_not_found", status_code=404)
    feature = next((f for f in plan.features if f.feature_key == feature_key), None)
    if not feature:
        feature = PlanFeature(plan_id=plan.id, feature_key=feature_key, enabled=True, limit_value=-1)
        plan.features.append(feature)
    if enabled is not None:
        feature.enabled = enabled
    if limit_value is not None:
        feature.limit_value = limit_value
    await record_audit(session, actor_id=actor.id, action="plan.feature.update", entity="plan",
                       entity_id=plan_code, meta={"feature": feature_key, "enabled": enabled, "limit": limit_value},
                       ip=ip)
    await session.flush()
    return plan


# ---- visa rules ----
async def list_visa_rules(session):
    return list((await session.scalars(select(VisaRule).order_by(VisaRule.origin_iso2))).all())


async def upsert_visa_rule(session, *, actor: User, origin, destination, requirement,
                           allowed_stay_days=None, notes="", source="", ip="") -> VisaRule:
    origin, destination = origin.upper(), destination.upper()
    rule = await session.scalar(select(VisaRule).where(
        VisaRule.origin_iso2 == origin, VisaRule.destination_iso2 == destination))
    created = rule is None
    if rule is None:
        rule = VisaRule(origin_iso2=origin, destination_iso2=destination)
        session.add(rule)
    rule.requirement = requirement
    rule.allowed_stay_days = allowed_stay_days
    rule.notes = notes
    rule.source = source or rule.source
    await record_audit(session, actor_id=actor.id, action="visa_rule.upsert", entity="visa_rule",
                       entity_id=f"{origin}->{destination}", meta={"created": created, "requirement": requirement}, ip=ip)
    await session.flush()
    return rule


async def delete_visa_rule(session, *, actor: User, rule_id: uuid.UUID, ip="") -> None:
    rule = await session.scalar(select(VisaRule).where(VisaRule.id == rule_id))
    if not rule:
        raise AppError("Visa rule not found.", code="not_found", status_code=404)
    await record_audit(session, actor_id=actor.id, action="visa_rule.delete", entity="visa_rule",
                       entity_id=f"{rule.origin_iso2}->{rule.destination_iso2}", ip=ip)
    await session.delete(rule)
    await session.flush()


async def list_audit_logs(session, *, limit: int, offset: int):
    total = await _count(session, AuditLog)
    rows = (await session.scalars(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    )).all()
    return list(rows), total


async def health(session) -> dict:
    from app.services.ai import gemini_client
    from app.services.billing import stripe_service
    from app.core.config import get_settings

    db_ok = True
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    s = get_settings()
    return {
        "database": "ok" if db_ok else "down",
        "gemini": "configured" if gemini_client.is_configured() else "mock",
        "stripe": "configured" if stripe_service.is_configured() else "disabled",
        "amadeus": "configured" if (s.amadeus_client_id and s.amadeus_client_secret) else "mock",
    }
