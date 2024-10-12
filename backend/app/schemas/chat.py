from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class Citation(BaseModel):
    index: int = Field(ge=1)
    note_id: str
    title: str
    snippet: str
    score: float = Field(ge=0.0, le=1.0)


class ChatMessageRead(ORMModel):
    id: str
    session_id: str
    role: Literal["user", "assistant"]
    content: str
    citations: list[Citation] = Field(default_factory=list)
    created_at: datetime


class ChatSessionRead(ORMModel):
    id: str
    title: str
    message_count: int = 0
    created_at: datetime
    updated_at: datetime


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None
    notebook_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=10)


class AskResponse(BaseModel):
    session_id: str
    user_message: ChatMessageRead
    assistant_message: ChatMessageRead
    provider: str
