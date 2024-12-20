from httpx import AsyncClient

from app.ai.embeddings.hashing import HashingEmbedder
from app.services.search import cosine_rank
from tests.conftest import create_note


async def _seed(client: AsyncClient, headers: dict[str, str]) -> None:
    await create_note(
        client,
        headers,
        title="Postgres indexing guide",
        content="B-tree indexes speed up lookups. Use EXPLAIN ANALYZE to inspect query plans.",
        tags=["postgres"],
    )
    await create_note(
        client,
        headers,
        title="Marathon training",
        content="Long runs on Sunday, tempo runs on Wednesday. Carbohydrate fuelling matters.",
        tags=["running"],
    )
    await create_note(
        client,
        headers,
        title="Sourdough starter",
        content="Feed the starter with equal parts flour and water every twelve hours.",
        tags=["baking"],
    )


async def test_keyword_search(client: AsyncClient, user_headers: dict[str, str]) -> None:
    await _seed(client, user_headers)
    response = await client.get("/api/v1/search?q=query plans&mode=keyword", headers=user_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "keyword"
    assert body["engine"] == "like"
    assert body["total"] == 1
    hit = body["hits"][0]
    assert hit["title"] == "Postgres indexing guide"
    assert "query plans" in hit["snippet"].lower()
    assert 0 < hit["score"] <= 1


async def test_semantic_search_ranks_related_note_first(
    client: AsyncClient, user_headers: dict[str, str]
) -> None:
    await _seed(client, user_headers)
    response = await client.get(
        "/api/v1/search?q=speed up database lookups with indexes&mode=semantic",
        headers=user_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["engine"] == "numpy-cosine"
    assert body["hits"][0]["title"] == "Postgres indexing guide"
    scores = [hit["score"] for hit in body["hits"]]
    assert scores == sorted(scores, reverse=True)


async def test_hybrid_search_merges_results(
    client: AsyncClient, user_headers: dict[str, str]
) -> None:
    await _seed(client, user_headers)
    response = await client.get(
        "/api/v1/search?q=tempo runs&mode=hybrid&limit=2", headers=user_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["hits"][0]["title"] == "Marathon training"
    assert len(body["hits"]) <= 2


async def test_search_is_scoped_to_owner(
    client: AsyncClient, user_headers: dict[str, str], other_headers: dict[str, str]
) -> None:
    await _seed(client, user_headers)
    response = await client.get("/api/v1/search?q=postgres&mode=semantic", headers=other_headers)
    assert response.json()["total"] == 0


async def test_search_requires_query(client: AsyncClient, user_headers: dict[str, str]) -> None:
    response = await client.get("/api/v1/search", headers=user_headers)
    assert response.status_code == 422


def test_hashing_embedder_is_deterministic_and_normalised() -> None:
    embedder = HashingEmbedder(dim=64)
    a = embedder.embed_sync("Distributed systems and event sourcing")
    b = embedder.embed_sync("Distributed systems and event sourcing")
    assert a == b
    assert abs(sum(x * x for x in a) - 1.0) < 1e-6
    assert embedder.embed_sync("") == [0.0] * 64


def test_cosine_rank_orders_by_similarity() -> None:
    class FakeNote:
        def __init__(self, name: str, embedding: list[float]) -> None:
            self.name = name
            self.embedding = embedding

    notes = [FakeNote("far", [0.0, 1.0]), FakeNote("near", [1.0, 0.1]), FakeNote("none", [])]
    ranked = cosine_rank([1.0, 0.0], notes, limit=5)  # type: ignore[arg-type]
    assert [n.name for n, _ in ranked] == ["near", "far"]
    assert ranked[0][1] > ranked[1][1]
