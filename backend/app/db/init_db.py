"""
Database bootstrap CLI: seed RBAC, and optionally create a super admin from
environment variables (SUPERUSER_EMAIL / SUPERUSER_PASSWORD). No credentials are
hardcoded — the superuser step is skipped unless both env vars are provided.

Run after migrations:  python -m app.db.init_db
"""
from __future__ import annotations

import asyncio
import os

from sqlalchemy import select

from app.core.logging import configure_logging, get_logger
from app.core.rbac import Roles
from app.core.security import hash_password
from app.db.seed import seed_rbac
from app.db.seed_billing import seed_billing
from app.db.seed_locations import seed_locations
from app.db.session import get_engine, get_sessionmaker
from app.models.user import Role, User
from app.services import auth_service

logger = get_logger("init_db")


async def _run() -> None:
    sm = get_sessionmaker()
    async with sm() as session:
        await seed_rbac(session)
        await seed_locations(session)
        await seed_billing(session)
        logger.info("rbac_locations_billing_seeded")

        # Create Stripe products/prices for paid plans when a key is configured.
        from app.services.billing import stripe_service
        if stripe_service.is_configured():
            try:
                result = await stripe_service.create_catalog(session)
                logger.info("stripe_catalog", result=result)
            except Exception as exc:  # noqa: BLE001
                logger.warning("stripe_catalog_failed", error=str(exc))

        email = os.getenv("SUPERUSER_EMAIL")
        password = os.getenv("SUPERUSER_PASSWORD")
        if email and password:
            super_role = await session.scalar(select(Role).where(Role.name == Roles.SUPER_ADMIN))
            existing = await auth_service.get_user_by_email(session, email)
            if existing is None:
                user = User(
                    email=email.lower().strip(),
                    password_hash=hash_password(password),
                    full_name="Super Admin",
                    is_verified=True,
                )
                user.roles = [super_role]
                session.add(user)
                logger.info("superuser_created", email=email)
            elif Roles.SUPER_ADMIN not in existing.role_names:
                existing.roles = [*existing.roles, super_role]
                logger.info("superuser_role_granted", email=email)
            else:
                logger.info("superuser_exists", email=email)

        await session.commit()
    await get_engine().dispose()


def main() -> None:
    configure_logging()
    asyncio.run(_run())


if __name__ == "__main__":
    main()
