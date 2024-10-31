"""Keyword, semantic and hybrid search over a user's notes.

Semantic search uses pgvector's `<=>` cosine-distance operator on PostgreSQL and falls
back to an in-process numpy cosine similarity on SQLite (or any dialect without pgvector).
"""

from __future__ import annotations

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings.base import Embedder
from app.ai.factory import get_embedder
from app.ai.text import tokenize, truncate
from app.db.models import Note, User
from app.repositories.notes import NoteRepository
from app.schemas.search import SearchHit, SearchMode, SearchResponse


def _snippet(note: Note, query: str, width: int = 200) -> str:
    """Return a window of content around the first query term hit, else the head."""
    text = note.content.replace("\n", " ")
    lowered = text.lower()
    for term in tokenize(query):
        position = lowered.find(term)
        if position >= 0:
            start = max(0, position - width // 3)
            end = min(len(text), start + width)
            prefix = "..." if start > 0 else ""
            suffix = "..." if end < len(text) else ""
            return f"{prefix}{text[start:end].strip()}{suffix}"
    return truncate(note.content, width)


def cosine_rank(
    query_vector: list[float], notes: list[Note], limit: int
) -> list[tuple[Note, float]]:
    candidates = [n for n in notes if n.embedding]
    if not candidates:
        return []
    matrix = np.asarray([n.embedding for n in candidates], dtype=np.float32)
    query = np.asarray(query_vector, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1) * (np.linalg.norm(query) or 1.0)
    norms[norms == 0] = 1.0
    sims = matrix @ query / norms
    order = np.argsort(-sims)[:limit]
    return [(candidates[int(i)], float(sims[int(i)])) for i in order]


class SearchService:
    def __init__(self, db: AsyncSession, embedder: Embedder | None = None) -> None:
        self.db = db
        self.repo = NoteRepository(db)
        self.embedder = embedder or get_embedder()

    async def semantic(
        self, user: User, query: str, limit: int, notebook_id: str | None = None
    ) -> tuple[list[tuple[Note, float]], str]:
        vector = await self.embedder.embed(query)
        if self.repo.dialect == "postgresql":
            rows = await self.repo.pgvector_search(user.id, vector, limit, notebook_id)
            return [(note, 1.0 - distance) for note, distance in rows], "pgvector"
        notes = list(await self.repo.all_with_embeddings(user.id, notebook_id))
        return cosine_rank(vector, notes, limit), "numpy-cosine"

    async def keyword(self, user: User, query: str, limit: int) -> list[tuple[Note, float]]:
        notes = await self.repo.keyword_search(user.id, query, limit)
        terms = tokenize(query)
        ranked: list[tuple[Note, float]] = []
        for note in notes:
            haystack = f"{note.title} {note.content}".lower()
            title = note.title.lower()
            hits = sum(haystack.count(term) for term in terms) if terms else 1
            title_bonus = sum(2 for term in terms if term in title)
            score = min(1.0, (hits + title_bonus) / (4.0 + len(terms) * 2))
            ranked.append((note, score))
        ranked.sort(key=lambda item: -item[1])
        return ranked

    async def search(
        self, user: User, query: str, mode: SearchMode, limit: int = 10
    ) -> SearchResponse:
        engine = "like" if self.repo.dialect != "postgresql" else "tsvector"
        if mode == "keyword":
            results = await self.keyword(user, query, limit)
        elif mode == "semantic":
            results, engine = await self.semantic(user, query, limit)
        else:
            keyword_hits = await self.keyword(user, query, limit)
            semantic_hits, sem_engine = await self.semantic(user, query, limit)
            engine = f"{engine}+{sem_engine}"
            merged: dict[str, tuple[Note, float]] = {}
            for note, score in keyword_hits:
                merged[note.id] = (note, 0.5 * score)
            for note, score in semantic_hits:
                prev = merged.get(note.id)
                combined = 0.5 * score + (prev[1] if prev else 0.0)
                merged[note.id] = (note, combined)
            results = sorted(merged.values(), key=lambda item: -item[1])[:limit]

        hits = [
            SearchHit(
                note_id=note.id,
                title=note.title,
                snippet=_snippet(note, query),
                tags=list(note.tags or []),
                notebook_id=note.notebook_id,
                score=round(max(0.0, min(1.0, score)), 4),
                updated_at=note.updated_at.isoformat(),
            )
            for note, score in results
        ]
        return SearchResponse(query=query, mode=mode, engine=engine, total=len(hits), hits=hits)
