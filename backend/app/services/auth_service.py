"""Authentication & account business logic."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.core.rbac import DEFAULT_SIGNUP_ROLE
from app.core import security
from app.models.auth import EmailVerification, PasswordReset, RefreshToken
from app.models.user import Role, User
from app.schemas.auth import TokenPair, UserOut

logger = get_logger("auth")


def _as_aware(dt: datetime) -> datetime:
    """Treat naive datetimes (e.g. from SQLite) as UTC for safe comparison."""
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def to_user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        roles=sorted(user.role_names),
        permissions=sorted(user.permission_codes),
    )


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    return await session.scalar(select(User).where(User.email == email.lower()))


async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    # select() (not session.get) so the selectin eager-load of roles/permissions
    # fires — required for safe attribute access under async.
    return await session.scalar(select(User).where(User.id == user_id))


# ---- registration ----
async def register_user(
    session: AsyncSession, *, email: str, password: str, full_name: str
) -> tuple[User, str]:
    email = email.lower().strip()
    if await get_user_by_email(session, email):
        raise AppError("An account with this email already exists.", code="email_taken", status_code=409)

    user = User(
        email=email,
        password_hash=security.hash_password(password),
        full_name=full_name.strip(),
        is_verified=False,
    )
    default_role = await session.scalar(select(Role).where(Role.name == DEFAULT_SIGNUP_ROLE))
    if default_role:
        user.roles = [default_role]
    session.add(user)
    await session.flush()

    raw_token = await create_email_verification(session, user)
    logger.info("user_registered", user_id=str(user.id))
    return user, raw_token


# ---- authentication ----
async def authenticate(session: AsyncSession, *, email: str, password: str) -> User:
    settings = get_settings()
    user = await get_user_by_email(session, email.lower().strip())
    if not user or not security.verify_password(password, user.password_hash):
        raise AppError("Invalid email or password.", code="invalid_credentials", status_code=401)
    if not user.is_active:
        raise AppError("This account is disabled.", code="account_disabled", status_code=403)
    if settings.require_email_verification and not user.is_verified:
        raise AppError("Please verify your email before signing in.", code="email_unverified", status_code=403)

    # Opportunistic password rehash if Argon2 parameters changed.
    if security.needs_rehash(user.password_hash):
        user.password_hash = security.hash_password(password)
    return user


# ---- tokens ----
async def issue_token_pair(session: AsyncSession, user: User) -> TokenPair:
    access = security.create_access_token(str(user.id))
    raw_refresh = security.generate_token()
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=security.hash_token(raw_refresh),
            expires_at=security.refresh_token_expiry(),
        )
    )
    await session.flush()
    return TokenPair(access_token=access, refresh_token=raw_refresh)


async def rotate_refresh_token(session: AsyncSession, raw_refresh: str) -> tuple[User, TokenPair]:
    token_hash = security.hash_token(raw_refresh)
    row = await session.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if not row or row.revoked_at is not None or _as_aware(row.expires_at) < datetime.now(timezone.utc):
        raise AppError("Invalid or expired refresh token.", code="invalid_refresh", status_code=401)

    row.revoked_at = datetime.now(timezone.utc)  # rotation: old token is single-use
    user = await get_user_by_id(session, row.user_id)
    if not user or not user.is_active:
        raise AppError("Invalid or expired refresh token.", code="invalid_refresh", status_code=401)
    pair = await issue_token_pair(session, user)
    return user, pair


async def revoke_refresh_token(session: AsyncSession, raw_refresh: str) -> None:
    token_hash = security.hash_token(raw_refresh)
    row = await session.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if row and row.revoked_at is None:
        row.revoked_at = datetime.now(timezone.utc)


async def _revoke_all_refresh_tokens(session: AsyncSession, user_id: uuid.UUID) -> None:
    rows = (await session.scalars(select(RefreshToken).where(RefreshToken.user_id == user_id))).all()
    now = datetime.now(timezone.utc)
    for r in rows:
        if r.revoked_at is None:
            r.revoked_at = now


# ---- email verification ----
async def create_email_verification(session: AsyncSession, user: User) -> str:
    settings = get_settings()
    raw = security.generate_token()
    session.add(
        EmailVerification(
            user_id=user.id,
            token_hash=security.hash_token(raw),
            expires_at=datetime.now(timezone.utc)
            + timedelta(hours=settings.email_verification_expire_hours),
        )
    )
    await session.flush()
    # TODO(P8): send via Klaviyo. For now the raw token is returned to the caller (dev).
    return raw


async def verify_email(session: AsyncSession, raw_token: str) -> None:
    row = await session.scalar(
        select(EmailVerification).where(EmailVerification.token_hash == security.hash_token(raw_token))
    )
    if not row or row.used_at is not None or _as_aware(row.expires_at) < datetime.now(timezone.utc):
        raise AppError("Invalid or expired verification token.", code="invalid_token", status_code=400)
    user = await get_user_by_id(session, row.user_id)
    if not user:
        raise AppError("Invalid or expired verification token.", code="invalid_token", status_code=400)
    user.is_verified = True
    row.used_at = datetime.now(timezone.utc)


# ---- password reset ----
async def create_password_reset(session: AsyncSession, email: str) -> str | None:
    settings = get_settings()
    user = await get_user_by_email(session, email.lower().strip())
    if not user:
        return None  # do not reveal whether the email exists
    raw = security.generate_token()
    session.add(
        PasswordReset(
            user_id=user.id,
            token_hash=security.hash_token(raw),
            expires_at=datetime.now(timezone.utc)
            + timedelta(hours=settings.password_reset_expire_hours),
        )
    )
    await session.flush()
    return raw


async def reset_password(session: AsyncSession, *, raw_token: str, new_password: str) -> None:
    row = await session.scalar(
        select(PasswordReset).where(PasswordReset.token_hash == security.hash_token(raw_token))
    )
    if not row or row.used_at is not None or _as_aware(row.expires_at) < datetime.now(timezone.utc):
        raise AppError("Invalid or expired reset token.", code="invalid_token", status_code=400)
    user = await get_user_by_id(session, row.user_id)
    if not user:
        raise AppError("Invalid or expired reset token.", code="invalid_token", status_code=400)
    user.password_hash = security.hash_password(new_password)
    row.used_at = datetime.now(timezone.utc)
    await _revoke_all_refresh_tokens(session, user.id)  # force re-login everywhere
