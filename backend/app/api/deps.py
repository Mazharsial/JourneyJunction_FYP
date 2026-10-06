"""Shared API dependencies: current-user resolution and RBAC guards."""
from __future__ import annotations

import uuid

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import get_user_by_id

# auto_error=False so we can raise our own consistent error envelope.
_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    credentials=Depends(_bearer),
) -> User:
    if credentials is None or not credentials.credentials:
        raise AppError("Authentication required.", code="not_authenticated", status_code=401)
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(payload["sub"])
    except (jwt.ExpiredSignatureError,):
        raise AppError("Access token has expired.", code="token_expired", status_code=401)
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise AppError("Invalid authentication token.", code="invalid_token", status_code=401)

    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise AppError("Account not found or disabled.", code="account_invalid", status_code=401)
    request.state.user_id = str(user.id)
    return user


def require_roles(*roles: str):
    """Dependency enforcing that the current user has at least one of `roles`."""
    required = set(roles)

    async def _guard(user: User = Depends(get_current_user)) -> User:
        if not (required & user.role_names):
            raise AppError("You do not have access to this resource.", code="forbidden", status_code=403)
        return user

    return _guard


def require_permissions(*permissions: str):
    """Dependency enforcing that the current user holds ALL of `permissions`."""
    required = set(permissions)

    async def _guard(user: User = Depends(get_current_user)) -> User:
        if not required.issubset(user.permission_codes):
            raise AppError("You do not have permission to perform this action.", code="forbidden", status_code=403)
        return user

    return _guard
