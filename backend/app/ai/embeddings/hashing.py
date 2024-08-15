"""Deterministic hashing-trick embedder (no external services, no model weights).

Each unigram and bigram is hashed into one of `dim` buckets with a hashed sign, weighted
by sub-linear term frequency. The resulting vector is L2-normalised so cosine similarity
is a plain dot product. It is not a neural embedding, but it captures lexical overlap
well enough for a useful offline semantic search and is fully reproducible.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter

from app.ai.embeddings.base import Embedder
from app.ai.text import strip_markdown, tokenize


def _bucket(token: str, dim: int) -> tuple[int, float]:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    index = int.from_bytes(digest[:4], "big") % dim
    sign = 1.0 if digest[4] & 1 else -1.0
    return index, sign


class HashingEmbedder(Embedder):
    name = "hashing"

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    async def embed(self, text: str) -> list[float]:
        return self.embed_sync(text)

    def embed_sync(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        tokens = tokenize(strip_markdown(text))
        if not tokens:
            return vector
        counts: dict[str, float] = {tok: float(n) for tok, n in Counter(tokens).items()}
        for a, b in zip(tokens, tokens[1:], strict=False):
            counts[f"{a}_{b}"] = counts.get(f"{a}_{b}", 0.0) + 0.5
        for token, count in counts.items():
            index, sign = _bucket(token, self.dim)
            vector[index] += sign * (1.0 + math.log(count))
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]
