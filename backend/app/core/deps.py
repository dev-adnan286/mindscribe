"""Shared FastAPI dependencies: database session, current user, ownership checks."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.db.models import User
from app.db.session import get_session_factory
from app.repositories.users import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    factory = get_session_factory(request.app)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Missing bearer token")
    payload = decode_token(credentials.credentials, expected_type="access")
    user = await UserRepository(db).get_by_id(str(payload["sub"]))
    if user is None:
        raise UnauthorizedError("User no longer exists")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_owner(owner_id: str, user: User, resource: str = "resource") -> None:
    """Raise 403 when the current user does not own the resource."""
    if owner_id != user.id:
        raise ForbiddenError(f"You do not have access to this {resource}")
