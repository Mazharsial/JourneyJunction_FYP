"""
Developer convenience: create all tables (from the ORM models) and seed
reference data, for a quick local run WITHOUT Docker/PostgreSQL.

Unlike `python -m app.db.init_db` (which expects Alembic migrations to have run,
i.e. a PostgreSQL database), this script calls SQLAlchemy `create_all`, so it
works against SQLite out of the box. Use it only for local development.

Usage (from the `backend/` folder, with the venv active):
    # SQLite (default for local dev)
    set DATABASE_URL=sqlite+aiosqlite:///./dev.db      (PowerShell: $env:DATABASE_URL=...)
    set SUPERUSER_EMAIL=admin@journeyjunction.app
    set SUPERUSER_PASSWORD=Admin@12345
    python -m scripts.dev_seed
"""
from __future__ import annotations

import asyncio
import os

from sqlalchemy import select

from app.core.rbac import Roles
from app.core.security import hash_password
from app.db.seed import seed_rbac
from app.db.seed_billing import seed_billing
from app.db.seed_locations import seed_locations
from app.db.session import get_engine, get_sessionmaker
from app.models import Base
from app.models.user import Role, User


async def main() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sm = get_sessionmaker()
    async with sm() as session:
        await seed_rbac(session)
        await seed_locations(session)
        await seed_billing(session)

        email = os.getenv("SUPERUSER_EMAIL")
        password = os.getenv("SUPERUSER_PASSWORD")
        if email and password:
            role = await session.scalar(select(Role).where(Role.name == Roles.SUPER_ADMIN))
            exists = await session.scalar(select(User).where(User.email == email.lower()))
            if not exists:
                user = User(
                    email=email.lower().strip(),
                    password_hash=hash_password(password),
                    full_name="Super Admin",
                    is_verified=True,
                )
                user.roles = [role]
                session.add(user)
                print(f"created superuser: {email}")
        await session.commit()

    await engine.dispose()
    print("DEV DATABASE READY")


if __name__ == "__main__":
    asyncio.run(main())
