from httpx import AsyncClient

from tests.conftest import create_note


async def test_create_and_get_note(client: AsyncClient, user_headers: dict[str, str]) -> None:
    note = await create_note(
        client,
        user_headers,
        title="  Hello world  ",
        content="Body text",
        tags=["Python", "python", "Web Dev"],
    )
    assert note["title"] == "Hello world"
    assert note["tags"] == ["python", "web-dev"]
    assert note["version"] == 1
    assert note["has_embedding"] is True

    fetched = await client.get(f"/api/v1/notes/{note['id']}", headers=user_headers)
    assert fetched.status_code == 200
    assert fetched.json()["content"] == "Body text"


async def test_note_validation(client: AsyncClient, user_headers: dict[str, str]) -> None:
    blank = await client.post(
        "/api/v1/notes", json={"title": "  ", "content": "x"}, headers=user_headers
    )
    assert blank.status_code == 422
    bad_tag = await client.post(
        "/api/v1/notes", json={"title": "T", "tags": ["bad!tag"]}, headers=user_headers
    )
    assert bad_tag.status_code == 422
    missing_notebook = await client.post(
        "/api/v1/notes", json={"title": "T", "notebook_id": "nope"}, headers=user_headers
    )
    assert missing_notebook.status_code == 404


async def test_update_creates_versions_and_restore(
    client: AsyncClient, user_headers: dict[str, str]
) -> None:
    note = await create_note(client, user_headers, title="v1", content="first")
    updated = await client.patch(
        f"/api/v1/notes/{note['id']}",
        json={"title": "v2", "content": "second"},
        headers=user_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["version"] == 2

    # Updating only the summary does not bump the version.
    summary_only = await client.patch(
        f"/api/v1/notes/{note['id']}", json={"summary": "S"}, headers=user_headers
    )
    assert summary_only.json()["version"] == 2
    assert summary_only.json()["summary"] == "S"

    versions = await client.get(f"/api/v1/notes/{note['id']}/versions", headers=user_headers)
    assert versions.status_code == 200
    history = versions.json()
    assert [v["version"] for v in history] == [2, 1]
    assert history[1]["title"] == "v1"

    restored = await client.post(
        f"/api/v1/notes/{note['id']}/versions/1/restore", headers=user_headers
    )
    assert restored.status_code == 200
    assert restored.json()["title"] == "v1"
    assert restored.json()["content"] == "first"
    assert restored.json()["version"] == 3

    missing = await client.post(
        f"/api/v1/notes/{note['id']}/versions/99/restore", headers=user_headers
    )
    assert missing.status_code == 404


async def test_soft_delete_hides_note(client: AsyncClient, user_headers: dict[str, str]) -> None:
    note = await create_note(client, user_headers, tags=["gone"])
    deleted = await client.delete(f"/api/v1/notes/{note['id']}", headers=user_headers)
    assert deleted.status_code == 204
    assert (
        await client.get(f"/api/v1/notes/{note['id']}", headers=user_headers)
    ).status_code == 404
    listing = await client.get("/api/v1/notes", headers=user_headers)
    assert listing.json()["total"] == 0
    tags = await client.get("/api/v1/tags", headers=user_headers)
    assert tags.json() == []


async def test_list_pagination_filters_and_sorting(
    client: AsyncClient, user_headers: dict[str, str]
) -> None:
    nb = (await client.post("/api/v1/notebooks", json={"name": "NB"}, headers=user_headers)).json()
    for i in range(5):
        await create_note(
            client,
            user_headers,
            title=f"Note {i}",
            content=f"content number {i}" + (" special" if i % 2 else ""),
            tags=["odd"] if i % 2 else ["even"],
            notebook_id=nb["id"] if i < 3 else None,
        )

    page = await client.get("/api/v1/notes?page=1&page_size=2", headers=user_headers)
    body = page.json()
    assert body["total"] == 5 and body["pages"] == 3 and len(body["items"]) == 2

    by_notebook = await client.get(f"/api/v1/notes?notebook_id={nb['id']}", headers=user_headers)
    assert by_notebook.json()["total"] == 3

    by_tag = await client.get("/api/v1/notes?tag=odd", headers=user_headers)
    assert by_tag.json()["total"] == 2

    by_query = await client.get("/api/v1/notes?q=special", headers=user_headers)
    assert by_query.json()["total"] == 2

    titles = await client.get("/api/v1/notes?sort=title_asc", headers=user_headers)
    assert [n["title"] for n in titles.json()["items"]] == [f"Note {i}" for i in range(5)]

    tags = await client.get("/api/v1/tags", headers=user_headers)
    counts = {t["name"]: t["note_count"] for t in tags.json()}
    assert counts == {"even": 3, "odd": 2}

    recent = await client.get("/api/v1/notes/recent?limit=2", headers=user_headers)
    assert len(recent.json()) == 2


async def test_note_ownership_isolation(
    client: AsyncClient, user_headers: dict[str, str], other_headers: dict[str, str]
) -> None:
    note = await create_note(client, user_headers)
    other_nb = (
        await client.post("/api/v1/notebooks", json={"name": "Theirs"}, headers=other_headers)
    ).json()

    assert (
        await client.get(f"/api/v1/notes/{note['id']}", headers=other_headers)
    ).status_code == 403
    assert (
        await client.patch(
            f"/api/v1/notes/{note['id']}", json={"title": "pwned"}, headers=other_headers
        )
    ).status_code == 403
    assert (
        await client.delete(f"/api/v1/notes/{note['id']}", headers=other_headers)
    ).status_code == 403
    assert (
        await client.get(f"/api/v1/notes/{note['id']}/versions", headers=other_headers)
    ).status_code == 403
    # Cannot move my note into someone else's notebook.
    moved = await client.patch(
        f"/api/v1/notes/{note['id']}", json={"notebook_id": other_nb["id"]}, headers=user_headers
    )
    assert moved.status_code == 403
    assert (await client.get("/api/v1/notes", headers=other_headers)).json()["total"] == 0
