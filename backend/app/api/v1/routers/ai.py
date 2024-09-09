from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.core.deps import CurrentUser, DbSession
from app.core.rate_limit import rate_limit
from app.schemas.ai import (
    AIStatus,
    SummarizeRequest,
    SummarizeResponse,
    TagSuggestRequest,
    TagSuggestResponse,
)
from app.schemas.chat import AskRequest, AskResponse, ChatMessageRead, ChatSessionRead
from app.services.ai import AIService

router = APIRouter()
_ai_limit = rate_limit("ai")


@router.get("/status", response_model=AIStatus, summary="Active AI provider information")
async def ai_status(user: CurrentUser, db: DbSession) -> AIStatus:
    return AIService(db).status()


@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    dependencies=[Depends(_ai_limit)],
    summary="Summarise a note or arbitrary text",
)
async def summarize(
    payload: SummarizeRequest, user: CurrentUser, db: DbSession
) -> SummarizeResponse:
    return await AIService(db).summarize(payload, user)


@router.post(
    "/tags",
    response_model=TagSuggestResponse,
    dependencies=[Depends(_ai_limit)],
    summary="Suggest tags for a note or text",
)
async def suggest_tags(
    payload: TagSuggestRequest, user: CurrentUser, db: DbSession
) -> TagSuggestResponse:
    return await AIService(db).suggest_tags(payload, user)


@router.post(
    "/ask",
    response_model=AskResponse,
    dependencies=[Depends(_ai_limit)],
    summary="Chat with your notes (retrieval-augmented, with citations)",
)
async def ask(payload: AskRequest, user: CurrentUser, db: DbSession) -> AskResponse:
    return await AIService(db).ask(payload, user)


@router.get("/sessions", response_model=list[ChatSessionRead], summary="List chat sessions")
async def list_sessions(user: CurrentUser, db: DbSession) -> list[ChatSessionRead]:
    return await AIService(db).list_sessions(user)


@router.get(
    "/sessions/{session_id}/messages",
    response_model=list[ChatMessageRead],
    summary="Messages in a chat session",
)
async def list_messages(session_id: str, user: CurrentUser, db: DbSession) -> list[ChatMessageRead]:
    return await AIService(db).list_messages(session_id, user)


@router.delete(
    "/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a session"
)
async def delete_session(session_id: str, user: CurrentUser, db: DbSession) -> None:
    await AIService(db).delete_session(session_id, user)
