from httpx import AsyncClient

from app.ai.providers.base import _parse_tag_list
from app.ai.providers.mock import MockProvider
from tests.conftest import create_note

LONG_NOTE = """Event-driven architecture decouples producers from consumers.
Events are immutable facts about something that happened in the system.
Consumers must be idempotent because delivery is at-least-once.
Use an outbox table to publish events atomically with database writes.
Eventual consistency makes debugging harder, so invest in tracing early."""


async def test_ai_status(client: AsyncClient, user_headers: dict[str, str]) -> None:
    response = await client.get("/api/v1/ai/status", headers=user_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert body["embedding_provider"] == "hashing"
    assert body["embedding_dim"] == 256


async def test_summarize_text_and_apply_to_note(
    client: AsyncClient, user_headers: dict[str, str]
) -> None:
    raw = await client.post(
        "/api/v1/ai/summarize",
        json={"content": LONG_NOTE, "max_sentences": 2},
        headers=user_headers,
    )
    assert raw.status_code == 200
    body = raw.json()
    assert body["provider"] == "mock"
    assert body["applied"] is False
    assert 1 <= body["summary"].count(".") <= 2

    note = await create_note(client, user_headers, title="EDA", content=LONG_NOTE)
    applied = await client.post(
        "/api/v1/ai/summarize", json={"note_id": note["id"], "apply": True}, headers=user_headers
    )
    assert applied.status_code == 200
    assert applied.json()["applied"] is True
    fetched = await client.get(f"/api/v1/notes/{note['id']}", headers=user_headers)
    assert fetched.json()["summary"] == applied.json()["summary"]


async def test_summarize_validation(client: AsyncClient, user_headers: dict[str, str]) -> None:
    neither = await client.post("/api/v1/ai/summarize", json={}, headers=user_headers)
    assert neither.status_code == 422
    apply_without_note = await client.post(
        "/api/v1/ai/summarize", json={"content": "x y z", "apply": True}, headers=user_headers
    )
    assert apply_without_note.status_code == 422


async def test_suggest_tags_and_apply(client: AsyncClient, user_headers: dict[str, str]) -> None:
    note = await create_note(client, user_headers, title="EDA", content=LONG_NOTE, tags=["arch"])
    response = await client.post(
        "/api/v1/ai/tags",
        json={"note_id": note["id"], "max_tags": 3, "apply": True},
        headers=user_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert 1 <= len(body["tags"]) <= 3
    assert "events" in body["tags"]
    fetched = await client.get(f"/api/v1/notes/{note['id']}", headers=user_headers)
    assert fetched.json()["tags"][0] == "arch"
    assert set(body["tags"]).issubset(set(fetched.json()["tags"]))


async def test_ai_endpoints_respect_ownership(
    client: AsyncClient, user_headers: dict[str, str], other_headers: dict[str, str]
) -> None:
    note = await create_note(client, user_headers, content=LONG_NOTE)
    response = await client.post(
        "/api/v1/ai/summarize", json={"note_id": note["id"]}, headers=other_headers
    )
    assert response.status_code == 403


async def test_chat_with_notes_returns_citations_and_persists_session(
    client: AsyncClient, user_headers: dict[str, str]
) -> None:
    await create_note(client, user_headers, title="Event-driven architecture", content=LONG_NOTE)
    await create_note(
        client, user_headers, title="Coffee", content="Pour-over uses a 1:16 ratio of coffee."
    )

    first = await client.post(
        "/api/v1/ai/ask",
        json={"question": "Why must consumers be idempotent?", "top_k": 2},
        headers=user_headers,
    )
    assert first.status_code == 200
    body = first.json()
    assert body["provider"] == "mock"
    assert body["user_message"]["role"] == "user"
    assistant = body["assistant_message"]
    assert assistant["role"] == "assistant"
    assert "idempotent" in assistant["content"].lower()
    assert assistant["citations"]
    assert assistant["citations"][0]["title"] == "Event-driven architecture"
    assert "[1]" in assistant["content"]

    session_id = body["session_id"]
    follow_up = await client.post(
        "/api/v1/ai/ask",
        json={"question": "What about the outbox table?", "session_id": session_id},
        headers=user_headers,
    )
    assert follow_up.status_code == 200
    assert follow_up.json()["session_id"] == session_id

    sessions = await client.get("/api/v1/ai/sessions", headers=user_headers)
    assert sessions.status_code == 200
    assert sessions.json()[0]["id"] == session_id
    assert sessions.json()[0]["message_count"] == 4

    messages = await client.get(f"/api/v1/ai/sessions/{session_id}/messages", headers=user_headers)
    assert [m["role"] for m in messages.json()] == ["user", "assistant", "user", "assistant"]

    deleted = await client.delete(f"/api/v1/ai/sessions/{session_id}", headers=user_headers)
    assert deleted.status_code == 204
    assert (await client.get("/api/v1/ai/sessions", headers=user_headers)).json() == []


async def test_chat_without_notes_says_so(
    client: AsyncClient, user_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/ai/ask", json={"question": "Anything?"}, headers=user_headers
    )
    assert response.status_code == 200
    assert response.json()["assistant_message"]["citations"] == []
    assert "couldn't find" in response.json()["assistant_message"]["content"]


async def test_chat_session_ownership(
    client: AsyncClient, user_headers: dict[str, str], other_headers: dict[str, str]
) -> None:
    created = await client.post("/api/v1/ai/ask", json={"question": "Hello"}, headers=user_headers)
    session_id = created.json()["session_id"]
    assert (
        await client.get(f"/api/v1/ai/sessions/{session_id}/messages", headers=other_headers)
    ).status_code == 403
    assert (
        await client.post(
            "/api/v1/ai/ask",
            json={"question": "Hi", "session_id": session_id},
            headers=other_headers,
        )
    ).status_code == 403


async def test_mock_provider_helpers() -> None:
    provider = MockProvider()
    assert await provider.summarize("") == "This note is empty."
    assert await provider.summarize("One sentence only.") == "One sentence only."
    tags = await provider.generate_tags(LONG_NOTE, max_tags=4)
    assert len(tags) == 4 and all(tag == tag.lower() for tag in tags)


def test_parse_tag_list_handles_json_and_plain_text() -> None:
    assert _parse_tag_list('Sure! ["Machine Learning", "python", "python"]', 5) == [
        "machine-learning",
        "python",
    ]
    assert _parse_tag_list("- Alpha\n- beta, Gamma", 2) == ["alpha", "beta"]
