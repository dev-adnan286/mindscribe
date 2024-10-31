"""Notes: CRUD, versioning, soft delete, tag sync and embedding refresh."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings.base import Embedder
from app.ai.factory import get_embedder
from app.ai.text import truncate
from app.core.deps import require_owner
from app.core.exceptions import NotFoundError
from app.db.base import utcnow
from app.db.models import Note, User
from app.repositories.notebooks import NotebookRepository
from app.repositories.notes import NoteRepository
from app.repositories.tags import TagRepository
from app.schemas.common import Page
from app.schemas.notes import (
    NoteCreate,
    NoteListParams,
    NoteRead,
    NoteSummary,
    NoteUpdate,
    NoteVersionRead,
    TagRead,
)


def embedding_text(note: Note) -> str:
    return f"{note.title}\n{note.content}\n{' '.join(note.tags or [])}"


def note_to_read(note: Note) -> NoteRead:
    read = NoteRead.model_validate(note)
    read.has_embedding = note.embedding is not None
    return read


def note_to_summary(note: Note) -> NoteSummary:
    return NoteSummary(
        id=note.id,
        notebook_id=note.notebook_id,
        title=note.title,
        excerpt=truncate(note.content, 180),
        summary=note.summary,
        tags=list(note.tags or []),
        version=note.version,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


class NoteService:
    def __init__(self, db: AsyncSession, embedder: Embedder | None = None) -> None:
        self.db = db
        self.repo = NoteRepository(db)
        self.tags = TagRepository(db)
        self.notebooks = NotebookRepository(db)
        self.embedder = embedder or get_embedder()

    async def get_owned(self, note_id: str, user: User) -> Note:
        note = await self.repo.get(note_id)
        if note is None:
            raise NotFoundError("Note not found")
        require_owner(note.owner_id, user, "note")
        return note

    async def _validate_notebook(self, notebook_id: str | None, user: User) -> None:
        if notebook_id is None:
            return
        notebook = await self.notebooks.get(notebook_id)
        if notebook is None:
            raise NotFoundError("Notebook not found")
        require_owner(notebook.owner_id, user, "notebook")

    async def _sync_tags(self, note: Note, tag_names: list[str], user: User) -> None:
        note.tags = list(tag_names)
        note.tag_links = await self.tags.get_or_create_many(user.id, tag_names)

    async def _refresh_embedding(self, note: Note) -> None:
        note.embedding = await self.embedder.embed(embedding_text(note))

    async def list_notes(self, params: NoteListParams, user: User) -> Page[NoteSummary]:
        notes, total = await self.repo.list_notes(user.id, params)
        return Page.build([note_to_summary(n) for n in notes], total, params.page, params.page_size)

    async def recent(self, user: User, limit: int = 6) -> list[NoteSummary]:
        return [note_to_summary(n) for n in await self.repo.recent(user.id, limit)]

    async def get(self, note_id: str, user: User) -> NoteRead:
        return note_to_read(await self.get_owned(note_id, user))

    async def create(self, data: NoteCreate, user: User) -> NoteRead:
        await self._validate_notebook(data.notebook_id, user)
        # Resolve tag rows first so the collection is populated before the first flush;
        # touching an unloaded relationship on a persistent object would lazy-load (not
        # allowed in async sessions).
        tag_rows = await self.tags.get_or_create_many(user.id, data.tags)
        note = await self.repo.create(
            user.id,
            title=data.title,
            content=data.content,
            notebook_id=data.notebook_id,
            tags=list(data.tags),
            tag_links=tag_rows,
            version=1,
        )
        await self._refresh_embedding(note)
        await self.repo.add_version(note)
        await self.db.flush()
        return note_to_read(note)

    async def update(self, note_id: str, data: NoteUpdate, user: User) -> NoteRead:
        note = await self.get_owned(note_id, user)
        changes = data.model_dump(exclude_unset=True)
        content_changed = False

        if "title" in changes and changes["title"] is not None and changes["title"] != note.title:
            note.title = changes["title"]
            content_changed = True
        if "content" in changes and changes["content"] is not None:
            if changes["content"] != note.content:
                note.content = changes["content"]
                content_changed = True
        if "summary" in changes:
            note.summary = changes["summary"]
        if changes.get("clear_notebook"):
            note.notebook_id = None
        elif "notebook_id" in changes and changes["notebook_id"] is not None:
            await self._validate_notebook(changes["notebook_id"], user)
            note.notebook_id = changes["notebook_id"]
        if "tags" in changes and changes["tags"] is not None:
            if list(changes["tags"]) != list(note.tags or []):
                await self._sync_tags(note, changes["tags"], user)
                content_changed = True

        if content_changed:
            note.version += 1
            await self._refresh_embedding(note)
            await self.repo.add_version(note)
        note.updated_at = utcnow()
        await self.db.flush()
        return note_to_read(note)

    async def delete(self, note_id: str, user: User) -> None:
        note = await self.get_owned(note_id, user)
        note.is_deleted = True
        note.deleted_at = utcnow()
        note.tag_links = []
        await self.db.flush()
        await self.tags.prune_unused(user.id)

    async def versions(self, note_id: str, user: User) -> list[NoteVersionRead]:
        note = await self.get_owned(note_id, user)
        return [NoteVersionRead.model_validate(v) for v in await self.repo.list_versions(note.id)]

    async def restore_version(self, note_id: str, version: int, user: User) -> NoteRead:
        note = await self.get_owned(note_id, user)
        snapshot = await self.repo.get_version(note.id, version)
        if snapshot is None:
            raise NotFoundError(f"Version {version} not found")
        note.title = snapshot.title
        note.content = snapshot.content
        note.summary = snapshot.summary
        await self._sync_tags(note, list(snapshot.tags or []), user)
        note.version += 1
        await self._refresh_embedding(note)
        await self.repo.add_version(note)
        note.updated_at = utcnow()
        await self.db.flush()
        return note_to_read(note)

    async def list_tags(self, user: User) -> list[TagRead]:
        rows = await self.tags.list_with_counts(user.id)
        return [TagRead(id=tag.id, name=tag.name, note_count=count) for tag, count in rows]

    async def apply_summary(self, note_id: str, summary: str, user: User) -> Note:
        note = await self.get_owned(note_id, user)
        note.summary = summary
        await self.db.flush()
        return note

    async def apply_tags(self, note_id: str, tags: list[str], user: User) -> Note:
        note = await self.get_owned(note_id, user)
        merged = list(note.tags or [])
        for tag in tags:
            if tag not in merged:
                merged.append(tag)
        await self._sync_tags(note, merged[:20], user)
        await self._refresh_embedding(note)
        await self.db.flush()
        return note
