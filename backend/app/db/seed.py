"""Idempotent seeding of RBAC roles and permissions."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import (
    PERMISSION_DESCRIPTIONS,
    ROLE_DESCRIPTIONS,
    ROLE_PERMISSIONS,
)
from app.models.user import Permission, Role


async def seed_rbac(session: AsyncSession) -> None:
    """Create any missing permissions/roles and sync role->permission mapping."""
    # Permissions
    existing_perms = {
        p.code: p for p in (await session.scalars(select(Permission))).all()
    }
    for code, desc in PERMISSION_DESCRIPTIONS.items():
        if code not in existing_perms:
            perm = Permission(code=code, description=desc)
            session.add(perm)
            existing_perms[code] = perm
    await session.flush()

    # Roles + mapping. New roles get their permissions at construction time to
    # avoid triggering an async lazy-load on an uninitialised collection.
    existing_roles = {r.name: r for r in (await session.scalars(select(Role))).all()}
    for name, perm_codes in ROLE_PERMISSIONS.items():
        perms = [existing_perms[c] for c in perm_codes]
        role = existing_roles.get(name)
        if role is None:
            role = Role(name=name, description=ROLE_DESCRIPTIONS.get(name, ""), permissions=perms)
            session.add(role)
            existing_roles[name] = role
        else:
            # Existing roles were loaded via select() so their permissions
            # collection is already populated (selectin) and safe to reassign.
            role.permissions = perms

    await session.flush()
