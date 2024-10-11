from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Note, Tag, note_tags


class TagRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create_many(self, owner_id: str, names: list[str]) -> list[Tag]:
        if not names:
            return []
        stmt = select(Tag).where(Tag.owner_id == owner_id, Tag.name.in_(names))
        existing = {tag.name: tag for tag in (await self.db.execute(stmt)).scalars()}
        created: list[Tag] = []
        for name in names:
            if name not in existing:
                tag = Tag(owner_id=owner_id, name=name)
                self.db.add(tag)
                created.append(tag)
                existing[name] = tag
        if created:
            await self.db.flush()
        return [existing[name] for name in names]

    async def list_with_counts(self, owner_id: str) -> list[tuple[Tag, int]]:
        stmt = (
            select(Tag, func.count(Note.id))
            .outerjoin(note_tags, note_tags.c.tag_id == Tag.id)
            .outerjoin(Note, (Note.id == note_tags.c.note_id) & (Note.is_deleted.is_(False)))
            .where(Tag.owner_id == owner_id)
            .group_by(Tag.id)
            .order_by(func.count(Note.id).desc(), Tag.name.asc())
        )
        rows = (await self.db.execute(stmt)).all()
        return [(row[0], int(row[1])) for row in rows]

    async def prune_unused(self, owner_id: str) -> int:
        used = select(note_tags.c.tag_id)
        stmt = delete(Tag).where(Tag.owner_id == owner_id, Tag.id.not_in(used))
        result = await self.db.execute(stmt)
        return int(getattr(result, "rowcount", 0) or 0)
