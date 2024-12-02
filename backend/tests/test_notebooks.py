from httpx import AsyncClient

from tests.conftest import create_note


async def test_notebook_crud(client: AsyncClient, user_headers: dict[str, str]) -> None:
    created = await client.post(
        "/api/v1/notebooks",
        json={"name": "Work", "description": "Work stuff", "color": "#10B981"},
        headers=user_headers,
    )
    assert created.status_code == 201
    notebook = created.json()
    assert notebook["name"] == "Work"
    assert notebook["color"] == "#10b981"
    assert notebook["note_count"] == 0

    await create_note(client, user_headers, notebook_id=notebook["id"])

    listed = await client.get("/api/v1/notebooks", headers=user_headers)
    assert listed.status_code == 200
    assert listed.json()[0]["note_count"] == 1

    updated = await client.patch(
        f"/api/v1/notebooks/{notebook['id']}", json={"name": "Work 2"}, headers=user_headers
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Work 2"

    deleted = await client.delete(f"/api/v1/notebooks/{notebook['id']}", headers=user_headers)
    assert deleted.status_code == 204

    # Notes survive notebook deletion and are detached.
    notes = await client.get("/api/v1/notes", headers=user_headers)
    assert notes.json()["total"] == 1
    assert notes.json()["items"][0]["notebook_id"] is None


async def test_notebook_name_unique_per_user(
    client: AsyncClient, user_headers: dict[str, str], other_headers: dict[str, str]
) -> None:
    first = await client.post("/api/v1/notebooks", json={"name": "Ideas"}, headers=user_headers)
    assert first.status_code == 201
    duplicate = await client.post("/api/v1/notebooks", json={"name": "Ideas"}, headers=user_headers)
    assert duplicate.status_code == 409
    other_user = await client.post(
        "/api/v1/notebooks", json={"name": "Ideas"}, headers=other_headers
    )
    assert other_user.status_code == 201


async def test_notebook_validation(client: AsyncClient, user_headers: dict[str, str]) -> None:
    blank = await client.post("/api/v1/notebooks", json={"name": "   "}, headers=user_headers)
    assert blank.status_code == 422
    bad_color = await client.post(
        "/api/v1/notebooks", json={"name": "X", "color": "red"}, headers=user_headers
    )
    assert bad_color.status_code == 422


async def test_notebook_ownership_isolation(
    client: AsyncClient, user_headers: dict[str, str], other_headers: dict[str, str]
) -> None:
    created = await client.post("/api/v1/notebooks", json={"name": "Private"}, headers=user_headers)
    notebook_id = created.json()["id"]

    assert (
        await client.get(f"/api/v1/notebooks/{notebook_id}", headers=other_headers)
    ).status_code == 403
    assert (
        await client.patch(
            f"/api/v1/notebooks/{notebook_id}", json={"name": "Hacked"}, headers=other_headers
        )
    ).status_code == 403
    assert (
        await client.delete(f"/api/v1/notebooks/{notebook_id}", headers=other_headers)
    ).status_code == 403
    assert (await client.get("/api/v1/notebooks", headers=other_headers)).json() == []
