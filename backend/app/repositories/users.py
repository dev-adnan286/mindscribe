from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChatSession, Note, Notebook, Tag, User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: str) -> User | None:
        return await self.db.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def create(self, *, email: str, hashed_password: str, name: str) -> User:
        user = User(email=email.lower(), hashed_password=hashed_password, name=name)
        self.db.add(user)
        await self.db.flush()
        return user

    async def stats(self, user_id: str) -> dict[str, int]:
        notes_q = select(func.count(Note.id), func.coalesce(func.sum(func.length(Note.content)), 0))
        notes_q = notes_q.where(Note.owner_id == user_id, Note.is_deleted.is_(False))
        note_count, char_total = (await self.db.execute(notes_q)).one()
        notebook_count = (
            await self.db.execute(
                select(func.count(Notebook.id)).where(Notebook.owner_id == user_id)
            )
        ).scalar_one()
        tag_count = (
            await self.db.execute(select(func.count(Tag.id)).where(Tag.owner_id == user_id))
        ).scalar_one()
        session_count = (
            await self.db.execute(
                select(func.count(ChatSession.id)).where(ChatSession.owner_id == user_id)
            )
        ).scalar_one()
        return {
            "notes": int(note_count),
            "notebooks": int(notebook_count),
            "tags": int(tag_count),
            "chat_sessions": int(session_count),
            # rough word estimate: ~5.5 characters per word incl. whitespace
            "words": int(round(int(char_total) / 5.5)),
        }
