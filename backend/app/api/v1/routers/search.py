from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.schemas.search import SearchMode, SearchResponse
from app.services.search import SearchService

router = APIRouter()


@router.get("", response_model=SearchResponse, summary="Keyword, semantic or hybrid search")
async def search_notes(
    user: CurrentUser,
    db: DbSession,
    q: Annotated[str, Query(min_length=1, max_length=300)],
    mode: SearchMode = "keyword",
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> SearchResponse:
    return await SearchService(db).search(user, q.strip(), mode, limit)
