from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import CurrentUser, DbSession
from app.schemas.common import Page
from app.schemas.notes import (
    NoteCreate,
    NoteListParams,
    NoteRead,
    NoteSummary,
    NoteUpdate,
    NoteVersionRead,
)
from app.services.notes import NoteService

router = APIRouter()


def list_params(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    notebook_id: str | None = None,
    tag: str | None = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
    sort: str = "updated_desc",
) -> NoteListParams:
    return NoteListParams(
        page=page, page_size=page_size, notebook_id=notebook_id, tag=tag, q=q, sort=sort
    )


@router.get("", response_model=Page[NoteSummary], summary="List notes (paginated, filterable)")
async def list_notes(
    params: Annotated[NoteListParams, Depends(list_params)], user: CurrentUser, db: DbSession
) -> Page[NoteSummary]:
    return await NoteService(db).list_notes(params, user)


@router.get("/recent", response_model=list[NoteSummary], summary="Most recently updated notes")
async def recent_notes(
    user: CurrentUser, db: DbSession, limit: Annotated[int, Query(ge=1, le=20)] = 6
) -> list[NoteSummary]:
    return await NoteService(db).recent(user, limit)


@router.post("", response_model=NoteRead, status_code=status.HTTP_201_CREATED, summary="Create")
async def create_note(payload: NoteCreate, user: CurrentUser, db: DbSession) -> NoteRead:
    return await NoteService(db).create(payload, user)


@router.get("/{note_id}", response_model=NoteRead, summary="Get a note")
async def get_note(note_id: str, user: CurrentUser, db: DbSession) -> NoteRead:
    return await NoteService(db).get(note_id, user)


@router.patch("/{note_id}", response_model=NoteRead, summary="Update a note (creates a version)")
async def update_note(
    note_id: str, payload: NoteUpdate, user: CurrentUser, db: DbSession
) -> NoteRead:
    return await NoteService(db).update(note_id, payload, user)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Soft-delete")
async def delete_note(note_id: str, user: CurrentUser, db: DbSession) -> None:
    await NoteService(db).delete(note_id, user)


@router.get("/{note_id}/versions", response_model=list[NoteVersionRead], summary="History")
async def list_versions(note_id: str, user: CurrentUser, db: DbSession) -> list[NoteVersionRead]:
    return await NoteService(db).versions(note_id, user)


@router.post(
    "/{note_id}/versions/{version}/restore",
    response_model=NoteRead,
    summary="Restore a previous version (as a new version)",
)
async def restore_version(note_id: str, version: int, user: CurrentUser, db: DbSession) -> NoteRead:
    return await NoteService(db).restore_version(note_id, version, user)
