from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.core.config import get_settings
from app.core.deps import CurrentUser, DbSession
from app.core.rate_limit import rate_limit
from app.repositories.users import UserRepository
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
)
from app.schemas.users import UserRead, UserStats, UserUpdate
from app.services.auth import AuthService

router = APIRouter()
_auth_limit = rate_limit("auth", get_settings().auth_rate_limit_requests)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_auth_limit)],
    summary="Create an account and receive tokens",
)
async def register(payload: RegisterRequest, db: DbSession) -> AuthResponse:
    return await AuthService(db).register(
        email=payload.email, password=payload.password, name=payload.name
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    dependencies=[Depends(_auth_limit)],
    summary="Exchange credentials for tokens",
)
async def login(payload: LoginRequest, db: DbSession) -> AuthResponse:
    return await AuthService(db).login(email=payload.email, password=payload.password)


@router.post(
    "/refresh",
    response_model=TokenPair,
    dependencies=[Depends(_auth_limit)],
    summary="Rotate a refresh token for a new token pair",
)
async def refresh(payload: RefreshRequest, db: DbSession) -> TokenPair:
    return await AuthService(db).refresh(payload.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a refresh token",
)
async def logout(payload: LogoutRequest, db: DbSession) -> None:
    await AuthService(db).logout(payload.refresh_token)


@router.get("/me", response_model=UserRead, summary="Current user profile")
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me", response_model=UserRead, summary="Update profile or password")
async def update_me(payload: UserUpdate, user: CurrentUser, db: DbSession) -> UserRead:
    updated = await AuthService(db).update_profile(user, payload)
    return UserRead.model_validate(updated)


@router.get("/me/stats", response_model=UserStats, summary="Usage statistics")
async def my_stats(user: CurrentUser, db: DbSession) -> UserStats:
    return UserStats(**await UserRepository(db).stats(user.id))
