"""Authentication: registration, login, refresh-token rotation and logout."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError, ValidationFailedError
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.models import User
from app.repositories.refresh_tokens import RefreshTokenRepository
from app.repositories.users import UserRepository
from app.schemas.auth import AuthResponse, TokenPair
from app.schemas.users import UserRead, UserUpdate

log = get_logger("auth")


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.tokens = RefreshTokenRepository(db)

    async def _issue_tokens(self, user: User) -> TokenPair:
        access, expires_in = create_access_token(user.id, {"email": user.email})
        refresh, jti, expires_at = create_refresh_token(user.id)
        await self.tokens.create(
            jti=jti, user_id=user.id, token_hash=hash_token(refresh), expires_at=expires_at
        )
        return TokenPair(access_token=access, refresh_token=refresh, expires_in=expires_in)

    async def register(self, *, email: str, password: str, name: str) -> AuthResponse:
        if await self.users.get_by_email(email):
            raise ConflictError("An account with this email already exists")
        user = await self.users.create(
            email=email, hashed_password=hash_password(password), name=name
        )
        tokens = await self._issue_tokens(user)
        log.info("registered user %s", user.id)
        return AuthResponse(**tokens.model_dump(), user=UserRead.model_validate(user))

    async def login(self, *, email: str, password: str) -> AuthResponse:
        user = await self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        tokens = await self._issue_tokens(user)
        return AuthResponse(**tokens.model_dump(), user=UserRead.model_validate(user))

    async def refresh(self, refresh_token: str) -> TokenPair:
        payload = decode_token(refresh_token, expected_type="refresh")
        record = await self.tokens.get_by_jti(str(payload["jti"]))
        if record is None or record.token_hash != hash_token(refresh_token):
            raise UnauthorizedError("Refresh token is not recognised")
        if record.revoked_at is not None:
            # Reuse of a rotated token signals theft: revoke the whole family for safety.
            revoked = await self.tokens.revoke_all_for_user(record.user_id)
            # Persist the revocation now: the 401 below makes the request scope roll back.
            await self.db.commit()
            log.warning(
                "refresh token reuse detected for user %s, revoked %d tokens",
                record.user_id,
                revoked,
            )
            raise UnauthorizedError("Refresh token has been revoked")
        if not record.is_active:
            raise UnauthorizedError("Refresh token has expired")
        user = await self.users.get_by_id(record.user_id)
        if user is None:
            raise UnauthorizedError("User no longer exists")
        tokens = await self._issue_tokens(user)
        new_payload = decode_token(tokens.refresh_token, expected_type="refresh")
        await self.tokens.revoke(record, replaced_by=str(new_payload["jti"]))
        return tokens

    async def logout(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except UnauthorizedError:
            return  # logging out with a dead token is a no-op
        record = await self.tokens.get_by_jti(str(payload["jti"]))
        if record is not None and record.revoked_at is None:
            await self.tokens.revoke(record)

    async def update_profile(self, user: User, data: UserUpdate) -> User:
        if data.name is not None:
            user.name = data.name
        if data.new_password:
            if not data.current_password:
                raise ValidationFailedError("current_password is required to set a new password")
            if not verify_password(data.current_password, user.hashed_password):
                raise UnauthorizedError("Current password is incorrect")
            user.hashed_password = hash_password(data.new_password)
            await self.tokens.revoke_all_for_user(user.id)
        await self.db.flush()
        return user
