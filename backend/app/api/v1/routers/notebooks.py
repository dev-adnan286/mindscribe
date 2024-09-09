from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DbSession
from app.schemas.notebooks import NotebookCreate, NotebookRead, NotebookUpdate
from app.services.notebooks import NotebookService

router = APIRouter()


@router.get("", response_model=list[NotebookRead], summary="List notebooks with note counts")
async def list_notebooks(user: CurrentUser, db: DbSession) -> list[NotebookRead]:
    return await NotebookService(db).list_all(user)


@router.post("", response_model=NotebookRead, status_code=status.HTTP_201_CREATED, summary="Create")
async def create_notebook(
    payload: NotebookCreate, user: CurrentUser, db: DbSession
) -> NotebookRead:
    return await NotebookService(db).create(payload, user)


@router.get("/{notebook_id}", response_model=NotebookRead, summary="Get one notebook")
async def get_notebook(notebook_id: str, user: CurrentUser, db: DbSession) -> NotebookRead:
    return await NotebookService(db).get(notebook_id, user)


@router.patch("/{notebook_id}", response_model=NotebookRead, summary="Update a notebook")
async def update_notebook(
    notebook_id: str, payload: NotebookUpdate, user: CurrentUser, db: DbSession
) -> NotebookRead:
    return await NotebookService(db).update(notebook_id, payload, user)


@router.delete(
    "/{notebook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a notebook (its notes are kept and detached)",
)
async def delete_notebook(notebook_id: str, user: CurrentUser, db: DbSession) -> None:
    await NotebookService(db).delete(notebook_id, user)
