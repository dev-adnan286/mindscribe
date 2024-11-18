"""Test fixtures: an isolated SQLite database per test and an async HTTP client."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.update(
    {
        "ENVIRONMENT": "test",
        "SECRET_KEY": "test-secret-key-that-is-long-enough-for-tests",
        "RATE_LIMIT_ENABLED": "false",
        "AI_PROVIDER": "mock",
        "EMBEDDING_PROVIDER": "hashing",
        "BCRYPT_ROUNDS": "4",
        "LOG_LEVEL": "WARNING",
    }
)

from app.core.config import get_settings  # noqa: E402
from app.db.session import create_engine, create_session_factory, init_db  # noqa: E402
from app.main import create_app  # noqa: E402

get_settings.cache_clear()


@pytest_asyncio.fixture
async def client(tmp_path: Path) -> AsyncIterator[AsyncClient]:
    db_path = (tmp_path / "test.db").as_posix()
    url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_engine(url)
    await init_db(engine)
    app = create_app()
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    await engine.dispose()


class AuthHelper:
    def __init__(self, client: AsyncClient) -> None:
        self.client = client
        self.counter = 0

    async def register(
        self, email: str | None = None, password: str = "Password123", name: str = "Test User"
    ) -> dict:
        self.counter += 1
        email = email or f"user{self.counter}@example.com"
        response = await self.client.post(
            "/api/v1/auth/register", json={"email": email, "password": password, "name": name}
        )
        assert response.status_code == 201, response.text
        return response.json()

    async def headers(self, email: str | None = None) -> dict[str, str]:
        data = await self.register(email)
        return {"Authorization": f"Bearer {data['access_token']}"}


@pytest.fixture
def auth(client: AsyncClient) -> AuthHelper:
    return AuthHelper(client)


@pytest_asyncio.fixture
async def user_headers(auth: AuthHelper) -> dict[str, str]:
    return await auth.headers("owner@example.com")


@pytest_asyncio.fixture
async def other_headers(auth: AuthHelper) -> dict[str, str]:
    return await auth.headers("intruder@example.com")


async def create_note(
    client: AsyncClient,
    headers: dict[str, str],
    title: str = "Test note",
    content: str = "Some content about testing.",
    tags: list[str] | None = None,
    notebook_id: str | None = None,
) -> dict:
    payload: dict = {"title": title, "content": content, "tags": tags or []}
    if notebook_id:
        payload["notebook_id"] = notebook_id
    response = await client.post("/api/v1/notes", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()
