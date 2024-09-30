from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Note, NoteVersion, Tag, note_tags
from app.schemas.notes import NoteListParams


class NoteRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @property
    def dialect(self) -> str:
        return self.db.get_bind().dialect.name

    def _base(self, owner_id: str) -> Select[Any]:
        return select(Note).where(Note.owner_id == owner_id, Note.is_deleted.is_(False))

    async def get(self, note_id: str, *, include_deleted: bool = False) -> Note | None:
        stmt = select(Note).options(selectinload(Note.tag_links)).where(Note.id == note_id)
        if not include_deleted:
            stmt = stmt.where(Note.is_deleted.is_(False))
        return (await self.db.execute(stmt)).scalar_one_or_none()

    def _apply_keyword_filter(self, stmt: Select[Any], q: str) -> Select[Any]:
        if self.dialect == "postgresql":
            document = func.to_tsvector(
                "english", Note.title + " " + Note.content + " " + func.coalesce(Note.summary, "")
            )
            return stmt.where(document.op("@@")(func.plainto_tsquery("english", q)))
        # SQLite / other dialects: case-insensitive LIKE across each term.
        terms = [term for term in q.lower().split() if term]
        for term in terms:
            pattern = f"%{term}%"
            stmt = stmt.where(
                or_(
                    func.lower(Note.title).like(pattern),
                    func.lower(Note.content).like(pattern),
                    func.lower(func.coalesce(Note.summary, "")).like(pattern),
                )
            )
        return stmt

    async def list_notes(self, owner_id: str, params: NoteListParams) -> tuple[list[Note], int]:
        stmt = self._base(owner_id)
        if params.notebook_id:
            stmt = stmt.where(Note.notebook_id == params.notebook_id)
        if params.tag:
            stmt = stmt.where(
                Note.id.in_(
                    select(note_tags.c.note_id)
                    .join(Tag, Tag.id == note_tags.c.tag_id)
                    .where(Tag.owner_id == owner_id, Tag.name == params.tag.lower())
                )
            )
        if params.q:
            stmt = self._apply_keyword_filter(stmt, params.q)

        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        total = int((await self.db.execute(count_stmt)).scalar_one())

        ordering = {
            "updated_desc": Note.updated_at.desc(),
            "updated_asc": Note.updated_at.asc(),
            "created_desc": Note.created_at.desc(),
            "title_asc": func.lower(Note.title).asc(),
        }[params.sort]
        stmt = (
            stmt.order_by(ordering, Note.id.asc())
            .offset((params.page - 1) * params.page_size)
            .limit(params.page_size)
        )
        notes = list((await self.db.execute(stmt)).scalars().all())
        return notes, total

    async def recent(self, owner_id: str, limit: int = 6) -> list[Note]:
        stmt = self._base(owner_id).order_by(Note.updated_at.desc()).limit(limit)
        return list((await self.db.execute(stmt)).scalars().all())

    async def keyword_search(self, owner_id: str, q: str, limit: int) -> list[Note]:
        stmt = self._apply_keyword_filter(self._base(owner_id), q)
        stmt = stmt.order_by(Note.updated_at.desc()).limit(limit)
        return list((await self.db.execute(stmt)).scalars().all())

    async def all_with_embeddings(
        self, owner_id: str, notebook_id: str | None = None
    ) -> Sequence[Note]:
        stmt = self._base(owner_id).where(Note.embedding.is_not(None))
        if notebook_id:
            stmt = stmt.where(Note.notebook_id == notebook_id)
        return (await self.db.execute(stmt)).scalars().all()

    async def pgvector_search(
        self,
        owner_id: str,
        query_vector: list[float],
        limit: int,
        notebook_id: str | None = None,
    ) -> list[tuple[Note, float]]:
        """Cosine-distance ranking using the pgvector `<=>` operator (PostgreSQL only)."""
        from pgvector.sqlalchemy import Vector
        from sqlalchemy import bindparam, literal_column

        distance = literal_column("notes.embedding").op("<=>")(
            bindparam("qvec", value=query_vector, type_=Vector(len(query_vector)))
        )
        stmt = (
            select(Note, distance.label("distance"))
            .where(Note.owner_id == owner_id, Note.is_deleted.is_(False))
            .where(Note.embedding.is_not(None))
        )
        if notebook_id:
            stmt = stmt.where(Note.notebook_id == notebook_id)
        stmt = stmt.order_by(literal_column("distance").asc()).limit(limit)
        rows = (await self.db.execute(stmt)).all()
        return [(row[0], float(row[1])) for row in rows]

    async def create(self, owner_id: str, **fields: object) -> Note:
        note = Note(owner_id=owner_id, **fields)
        self.db.add(note)
        await self.db.flush()
        return note

    async def add_version(self, note: Note) -> NoteVersion:
        version = NoteVersion(
            note_id=note.id,
            version=note.version,
            title=note.title,
            content=note.content,
            summary=note.summary,
            tags=list(note.tags or []),
        )
        self.db.add(version)
        await self.db.flush()
        return version

    async def list_versions(self, note_id: str) -> list[NoteVersion]:
        stmt = (
            select(NoteVersion)
            .where(NoteVersion.note_id == note_id)
            .order_by(NoteVersion.version.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_version(self, note_id: str, version: int) -> NoteVersion | None:
        stmt = select(NoteVersion).where(
            NoteVersion.note_id == note_id, NoteVersion.version == version
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()
