from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_owner
from app.core.exceptions import ConflictError, NotFoundError
from app.db.models import Notebook, User
from app.repositories.notebooks import NotebookRepository
from app.schemas.notebooks import NotebookCreate, NotebookRead, NotebookUpdate


class NotebookService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = NotebookRepository(db)

    async def _get_owned(self, notebook_id: str, user: User) -> Notebook:
        notebook = await self.repo.get(notebook_id)
        if notebook is None:
            raise NotFoundError("Notebook not found")
        require_owner(notebook.owner_id, user, "notebook")
        return notebook

    async def list_all(self, user: User) -> list[NotebookRead]:
        rows = await self.repo.list_with_counts(user.id)
        return [self._to_read(nb, count) for nb, count in rows]

    async def get(self, notebook_id: str, user: User) -> NotebookRead:
        notebook = await self._get_owned(notebook_id, user)
        return self._to_read(notebook, await self.repo.note_count(notebook.id))

    async def create(self, data: NotebookCreate, user: User) -> NotebookRead:
        if await self.repo.get_by_name(user.id, data.name):
            raise ConflictError(f"A notebook named '{data.name}' already exists")
        notebook = await self.repo.create(user.id, **data.model_dump())
        return self._to_read(notebook, 0)

    async def update(self, notebook_id: str, data: NotebookUpdate, user: User) -> NotebookRead:
        notebook = await self._get_owned(notebook_id, user)
        changes = data.model_dump(exclude_unset=True)
        new_name = changes.get("name")
        if new_name and new_name != notebook.name:
            if await self.repo.get_by_name(user.id, new_name):
                raise ConflictError(f"A notebook named '{new_name}' already exists")
        for key, value in changes.items():
            setattr(notebook, key, value)
        await self.db.flush()
        return self._to_read(notebook, await self.repo.note_count(notebook.id))

    async def delete(self, notebook_id: str, user: User) -> None:
        notebook = await self._get_owned(notebook_id, user)
        await self.repo.delete(notebook)

    @staticmethod
    def _to_read(notebook: Notebook, count: int) -> NotebookRead:
        read = NotebookRead.model_validate(notebook)
        read.note_count = count
        return read
