from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import utcnow
from app.db.models import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self, *, jti: str, user_id: str, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        record = RefreshToken(id=jti, user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.db.add(record)
        await self.db.flush()
        return record

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        return await self.db.get(RefreshToken, jti)

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def revoke(self, record: RefreshToken, replaced_by: str | None = None) -> None:
        record.revoked_at = utcnow()
        record.replaced_by = replaced_by
        await self.db.flush()

    async def revoke_all_for_user(self, user_id: str) -> int:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=utcnow())
        )
        result = await self.db.execute(stmt)
        return int(getattr(result, "rowcount", 0) or 0)
