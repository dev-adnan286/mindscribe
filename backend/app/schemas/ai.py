from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class SummarizeRequest(BaseModel):
    note_id: str | None = None
    content: str | None = Field(default=None, max_length=100_000)
    apply: bool = Field(default=False, description="Persist the summary on the note")
    max_sentences: int = Field(default=3, ge=1, le=10)

    @model_validator(mode="after")
    def _one_of(self) -> SummarizeRequest:
        if not self.note_id and not (self.content and self.content.strip()):
            raise ValueError("Provide either note_id or content")
        if self.apply and not self.note_id:
            raise ValueError("apply=true requires note_id")
        return self


class SummarizeResponse(BaseModel):
    note_id: str | None
    summary: str
    provider: str
    applied: bool


class TagSuggestRequest(BaseModel):
    note_id: str | None = None
    content: str | None = Field(default=None, max_length=100_000)
    apply: bool = False
    max_tags: int = Field(default=5, ge=1, le=15)

    @model_validator(mode="after")
    def _one_of(self) -> TagSuggestRequest:
        if not self.note_id and not (self.content and self.content.strip()):
            raise ValueError("Provide either note_id or content")
        if self.apply and not self.note_id:
            raise ValueError("apply=true requires note_id")
        return self


class TagSuggestResponse(BaseModel):
    note_id: str | None
    tags: list[str]
    provider: str
    applied: bool


class AIStatus(BaseModel):
    provider: str
    model: str
    embedding_provider: str
    embedding_dim: int
