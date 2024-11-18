from httpx import AsyncClient

from app.core.security import create_access_token
from tests.conftest import AuthHelper


async def test_register_returns_tokens_and_user(auth: AuthHelper) -> None:
    data = await auth.register("alice@example.com", name="Alice")
    assert data["token_type"] == "bearer"
    assert data["access_token"] and data["refresh_token"]
    assert data["expires_in"] > 0
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["name"] == "Alice"
    assert "hashed_password" not in data["user"]


async def test_register_duplicate_email_conflicts(client: AsyncClient, auth: AuthHelper) -> None:
    await auth.register("dup@example.com")
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "Password123", "name": "Dup"},
    )
    assert response.status_code == 409
    body = response.json()
    assert body["title"] == "Conflict"
    assert body["type"].endswith("/conflict")


async def test_register_validates_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "password": "short", "name": "Weak"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["title"] == "Validation Failed"
    assert any("password" in err["loc"] for err in body["errors"])


async def test_login_success_and_failure(client: AsyncClient, auth: AuthHelper) -> None:
    await auth.register("bob@example.com", password="Secret123")
    ok = await client.post(
        "/api/v1/auth/login", json={"email": "bob@example.com", "password": "Secret123"}
    )
    assert ok.status_code == 200
    assert ok.json()["user"]["email"] == "bob@example.com"

    bad = await client.post(
        "/api/v1/auth/login", json={"email": "bob@example.com", "password": "Wrong1234"}
    )
    assert bad.status_code == 401
    assert bad.headers["WWW-Authenticate"] == "Bearer"


async def test_me_requires_valid_access_token(client: AsyncClient, auth: AuthHelper) -> None:
    data = await auth.register("carol@example.com")
    unauthenticated = await client.get("/api/v1/auth/me")
    assert unauthenticated.status_code == 401

    garbage = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer nope"})
    assert garbage.status_code == 401

    # A refresh token must not be accepted where an access token is expected.
    wrong_type = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {data['refresh_token']}"}
    )
    assert wrong_type.status_code == 401

    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["email"] == "carol@example.com"


async def test_refresh_rotates_and_detects_reuse(client: AsyncClient, auth: AuthHelper) -> None:
    data = await auth.register("dave@example.com")
    first_refresh = data["refresh_token"]

    rotated = await client.post("/api/v1/auth/refresh", json={"refresh_token": first_refresh})
    assert rotated.status_code == 200
    second = rotated.json()
    assert second["refresh_token"] != first_refresh
    assert second["access_token"]

    # The old token is revoked: reuse is rejected...
    reuse = await client.post("/api/v1/auth/refresh", json={"refresh_token": first_refresh})
    assert reuse.status_code == 401

    # ...and reuse revokes the whole family, so the new token no longer works either.
    family = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": second["refresh_token"]}
    )
    assert family.status_code == 401


async def test_refresh_rejects_access_token(client: AsyncClient, auth: AuthHelper) -> None:
    data = await auth.register("erin@example.com")
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": data["access_token"]}
    )
    assert response.status_code == 401


async def test_logout_revokes_refresh_token(client: AsyncClient, auth: AuthHelper) -> None:
    data = await auth.register("frank@example.com")
    response = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": data["refresh_token"]}
    )
    assert response.status_code == 204
    again = await client.post("/api/v1/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert again.status_code == 401


async def test_token_for_deleted_user_is_rejected(client: AsyncClient) -> None:
    token, _ = create_access_token("does-not-exist")
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


async def test_update_profile_and_password(client: AsyncClient, auth: AuthHelper) -> None:
    data = await auth.register("grace@example.com", password="Original1")
    headers = {"Authorization": f"Bearer {data['access_token']}"}

    renamed = await client.patch("/api/v1/auth/me", json={"name": "Grace H"}, headers=headers)
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Grace H"

    wrong = await client.patch(
        "/api/v1/auth/me",
        json={"current_password": "Nope12345", "new_password": "Changed123"},
        headers=headers,
    )
    assert wrong.status_code == 401

    changed = await client.patch(
        "/api/v1/auth/me",
        json={"current_password": "Original1", "new_password": "Changed123"},
        headers=headers,
    )
    assert changed.status_code == 200

    login = await client.post(
        "/api/v1/auth/login", json={"email": "grace@example.com", "password": "Changed123"}
    )
    assert login.status_code == 200


async def test_stats_endpoint(client: AsyncClient, user_headers: dict[str, str]) -> None:
    response = await client.get("/api/v1/auth/me/stats", headers=user_headers)
    assert response.status_code == 200
    assert response.json() == {
        "notes": 0,
        "notebooks": 0,
        "tags": 0,
        "chat_sessions": 0,
        "words": 0,
    }
