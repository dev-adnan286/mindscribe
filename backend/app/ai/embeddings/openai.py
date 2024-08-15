"""OpenAI embeddings, imported lazily. Vectors are truncated/padded to the configured dim
(text-embedding-3 models support `dimensions` natively, which we request directly)."""

from __future__ import annotations

import math
from typing import Any

from app.ai.embeddings.base import Embedder
from app.core.exceptions import ServiceUnavailableError


class OpenAIEmbedder(Embedder):
    name = "openai"

    def __init__(self, api_key: str, model: str = "text-embedding-3-small", dim: int = 256) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for the openai embedder")
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise ServiceUnavailableError("The 'openai' package is not installed") from exc
        self.model = model
        self.dim = dim
        self._client: Any = AsyncOpenAI(api_key=api_key)

    async def embed(self, text: str) -> list[float]:
        return (await self.embed_many([text]))[0]

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        from openai import APIError

        try:
            response = await self._client.embeddings.create(
                model=self.model, input=texts, dimensions=self.dim
            )
        except APIError as exc:
            raise ServiceUnavailableError("OpenAI embeddings request failed") from exc
        vectors: list[list[float]] = []
        for item in response.data:
            values = list(item.embedding)[: self.dim]
            values += [0.0] * (self.dim - len(values))
            norm = math.sqrt(sum(v * v for v in values)) or 1.0
            vectors.append([v / norm for v in values])
        return vectors
