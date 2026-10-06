"""Authentication & account endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.rate_limit import RateLimiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenPair,
    UserOut,
    VerifyEmailRequest,
)
from app.services import auth_service

router = APIRouter()
_auth_limit = RateLimiter()  # uses configured auth limits


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(_auth_limit)])
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> RegisterResponse:
    user, verification_token = await auth_service.register_user(
        db, email=payload.email, password=payload.password, full_name=payload.full_name
    )
    tokens = await auth_service.issue_token_pair(db, user)
    settings = get_settings()
    return RegisterResponse(
        user=auth_service.to_user_out(user),
        tokens=tokens,
        # Only surfaced outside production until the email provider (Klaviyo) is wired up.
        verification_token=None if settings.is_production else verification_token,
    )


@router.post("/login", response_model=TokenPair, dependencies=[Depends(_auth_limit)])
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    user = await auth_service.authenticate(db, email=payload.email, password=payload.password)
    return await auth_service.issue_token_pair(db, user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    _, pair = await auth_service.rotate_refresh_token(db, payload.refresh_token)
    return pair


@router.post("/logout", response_model=MessageResponse)
async def logout(payload: LogoutRequest, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    await auth_service.revoke_refresh_token(db, payload.refresh_token)
    return MessageResponse(message="Logged out.")


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return auth_service.to_user_out(user)


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(payload: VerifyEmailRequest, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    await auth_service.verify_email(db, payload.token)
    return MessageResponse(message="Email verified.")


@router.post("/password-reset/request", response_model=MessageResponse,
             dependencies=[Depends(_auth_limit)])
async def request_password_reset(payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    await auth_service.create_password_reset(db, payload.email)
    # Always the same response regardless of whether the email exists.
    return MessageResponse(message="If an account exists for that email, a reset link has been sent.")


@router.post("/password-reset/confirm", response_model=MessageResponse)
async def confirm_password_reset(payload: PasswordResetConfirm, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    await auth_service.reset_password(db, raw_token=payload.token, new_password=payload.new_password)
    return MessageResponse(message="Password updated. Please sign in again.")
