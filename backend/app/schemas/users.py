from __future__ import annotations

from datetime import datetime

from pydantic import EmailStr, Field, field_validator

from app.schemas.common import ORMModel


class UserRead(ORMModel):
    id: str
    email: EmailStr
    name: str
    created_at: datetime


class UserUpdate(ORMModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    current_password: str | None = Field(default=None, min_length=8, max_length=128)
    new_password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class UserStats(ORMModel):
    notes: int
    notebooks: int
    tags: int
    chat_sessions: int
    words: int
