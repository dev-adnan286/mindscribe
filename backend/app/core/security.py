"""Password hashing and JWT access/refresh token helpers."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import bcrypt
import jwt

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError

TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    settings = get_settings()
    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def hash_token(token: str) -> str:
    """Refresh tokens are stored hashed so a DB leak cannot be replayed."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(UTC)


def create_access_token(user_id: str, extra: dict[str, Any] | None = None) -> tuple[str, int]:
    settings = get_settings()
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    now = _now()
    payload: dict[str, Any] = {
        "sub": user_id,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, int(expires_delta.total_seconds())


def create_refresh_token(user_id: str) -> tuple[str, str, datetime]:
    """Return (token, jti, expires_at)."""
    settings = get_settings()
    now = _now()
    expires_at = now + timedelta(days=settings.refresh_token_expire_days)
    jti = uuid.uuid4().hex
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": jti,
        "nonce": secrets.token_hex(8),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expires_at


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub", "type", "jti"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Token has expired") from exc
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid token") from exc
    if payload.get("type") != expected_type:
        raise UnauthorizedError(f"Expected a {expected_type} token")
    return payload
