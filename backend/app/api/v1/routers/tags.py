from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.schemas.notes import TagRead
from app.services.notes import NoteService

router = APIRouter()


@router.get("", response_model=list[TagRead], summary="List the user's tags with counts")
async def list_tags(user: CurrentUser, db: DbSession) -> list[TagRead]:
    return await NoteService(db).list_tags(user)
