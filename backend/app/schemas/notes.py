from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator

from app.schemas.common import ORMModel

TAG_RE = re.compile(r"^[a-z0-9][a-z0-9\-_ ]{0,48}$")
MAX_TAGS = 20


def normalise_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for raw in tags:
        tag = re.sub(r"\s+", "-", raw.strip().lower())
        if not tag:
            continue
        if not TAG_RE.match(tag):
            raise ValueError(f"Invalid tag: {raw!r}")
        if tag not in seen:
            seen.add(tag)
            result.append(tag)
    if len(result) > MAX_TAGS:
        raise ValueError(f"A note can have at most {MAX_TAGS} tags")
    return result


class NoteCreate(ORMModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(default="", max_length=100_000)
    notebook_id: str | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def _strip_title(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Title cannot be blank")
        return stripped

    @field_validator("tags")
    @classmethod
    def _tags(cls, value: list[str]) -> list[str]:
        return normalise_tags(value)


class NoteUpdate(ORMModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, max_length=100_000)
    notebook_id: str | None = None
    clear_notebook: bool = False
    tags: list[str] | None = None
    summary: str | None = Field(default=None, max_length=5000)

    @field_validator("title")
    @classmethod
    def _strip_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Title cannot be blank")
        return stripped

    @field_validator("tags")
    @classmethod
    def _tags(cls, value: list[str] | None) -> list[str] | None:
        return normalise_tags(value) if value is not None else None


class NoteRead(ORMModel):
    id: str
    owner_id: str
    notebook_id: str | None
    title: str
    content: str
    summary: str | None
    tags: list[str]
    version: int
    has_embedding: bool = False
    created_at: datetime
    updated_at: datetime


class NoteSummary(ORMModel):
    """Lightweight representation for lists."""

    id: str
    notebook_id: str | None
    title: str
    excerpt: str
    summary: str | None
    tags: list[str]
    version: int
    created_at: datetime
    updated_at: datetime


class NoteVersionRead(ORMModel):
    id: str
    note_id: str
    version: int
    title: str
    content: str
    summary: str | None
    tags: list[str]
    created_at: datetime


class NoteListParams(ORMModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    notebook_id: str | None = None
    tag: str | None = None
    q: str | None = Field(default=None, max_length=200)
    sort: Literal["updated_desc", "updated_asc", "created_desc", "title_asc"] = "updated_desc"


class TagRead(ORMModel):
    id: str
    name: str
    note_count: int = 0
