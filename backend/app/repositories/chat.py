from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChatMessage, ChatSession


class ChatRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_session(self, session_id: str) -> ChatSession | None:
        return await self.db.get(ChatSession, session_id)

    async def create_session(self, owner_id: str, title: str) -> ChatSession:
        session = ChatSession(owner_id=owner_id, title=title[:200])
        self.db.add(session)
        await self.db.flush()
        return session

    async def list_sessions(self, owner_id: str) -> list[tuple[ChatSession, int]]:
        count_sq = (
            select(ChatMessage.session_id, func.count(ChatMessage.id).label("cnt"))
            .group_by(ChatMessage.session_id)
            .subquery()
        )
        stmt = (
            select(ChatSession, func.coalesce(count_sq.c.cnt, 0))
            .outerjoin(count_sq, count_sq.c.session_id == ChatSession.id)
            .where(ChatSession.owner_id == owner_id)
            .order_by(ChatSession.updated_at.desc())
        )
        rows = (await self.db.execute(stmt)).all()
        return [(row[0], int(row[1])) for row in rows]

    async def list_messages(self, session_id: str, limit: int | None = None) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        )
        if limit:
            stmt = stmt.limit(limit)
        return list((await self.db.execute(stmt)).scalars().all())

    async def add_message(
        self, session: ChatSession, role: str, content: str, citations: list[dict] | None = None
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session.id, role=role, content=content, citations=citations or []
        )
        self.db.add(message)
        await self.db.flush()
        return message

    async def delete_session(self, session: ChatSession) -> None:
        await self.db.delete(session)
        await self.db.flush()
