from __future__ import annotations

from abc import ABC, abstractmethod


class Embedder(ABC):
    name: str = "base"
    dim: int = 0

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Return a unit-length embedding vector for `text`."""

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(text) for text in texts]
