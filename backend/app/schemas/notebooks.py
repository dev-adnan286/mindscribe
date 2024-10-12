from __future__ import annotations

import re
from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.common import ORMModel

HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


class NotebookBase(ORMModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    color: str = Field(default="#6366f1")

    @field_validator("name")
    @classmethod
    def _strip(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Notebook name cannot be blank")
        return stripped

    @field_validator("color")
    @classmethod
    def _color(cls, value: str) -> str:
        if not HEX_COLOR.match(value):
            raise ValueError("Color must be a hex value like #6366f1")
        return value.lower()


class NotebookCreate(NotebookBase):
    pass


class NotebookUpdate(ORMModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    color: str | None = None

    @field_validator("color")
    @classmethod
    def _color(cls, value: str | None) -> str | None:
        if value is not None and not HEX_COLOR.match(value):
            raise ValueError("Color must be a hex value like #6366f1")
        return value.lower() if value else value


class NotebookRead(NotebookBase):
    id: str
    owner_id: str
    note_count: int = 0
    created_at: datetime
    updated_at: datetime
