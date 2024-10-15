from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SearchMode = Literal["keyword", "semantic", "hybrid"]


class SearchHit(BaseModel):
    note_id: str
    title: str
    snippet: str
    tags: list[str]
    notebook_id: str | None
    score: float = Field(ge=0.0, le=1.0)
    updated_at: str


class SearchResponse(BaseModel):
    query: str
    mode: SearchMode
    engine: str
    total: int
    hits: list[SearchHit]
