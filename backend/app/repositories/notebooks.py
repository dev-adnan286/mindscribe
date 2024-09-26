from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Note, Notebook


class NotebookRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, notebook_id: str) -> Notebook | None:
        return await self.db.get(Notebook, notebook_id)

    async def get_by_name(self, owner_id: str, name: str) -> Notebook | None:
        stmt = select(Notebook).where(Notebook.owner_id == owner_id, Notebook.name == name)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_with_counts(self, owner_id: str) -> list[tuple[Notebook, int]]:
        count_sq = (
            select(Note.notebook_id, func.count(Note.id).label("cnt"))
            .where(Note.owner_id == owner_id, Note.is_deleted.is_(False))
            .group_by(Note.notebook_id)
            .subquery()
        )
        stmt = (
            select(Notebook, func.coalesce(count_sq.c.cnt, 0))
            .outerjoin(count_sq, count_sq.c.notebook_id == Notebook.id)
            .where(Notebook.owner_id == owner_id)
            .order_by(Notebook.name.asc())
        )
        rows = (await self.db.execute(stmt)).all()
        return [(row[0], int(row[1])) for row in rows]

    async def note_count(self, notebook_id: str) -> int:
        stmt = select(func.count(Note.id)).where(
            Note.notebook_id == notebook_id, Note.is_deleted.is_(False)
        )
        return int((await self.db.execute(stmt)).scalar_one())

    async def create(self, owner_id: str, **fields: object) -> Notebook:
        notebook = Notebook(owner_id=owner_id, **fields)
        self.db.add(notebook)
        await self.db.flush()
        return notebook

    async def delete(self, notebook: Notebook) -> None:
        # Detach notes rather than deleting them: a notebook is a container, not the content.
        await self.db.execute(
            update(Note).where(Note.notebook_id == notebook.id).values(notebook_id=None)
        )
        await self.db.delete(notebook)
        await self.db.flush()
