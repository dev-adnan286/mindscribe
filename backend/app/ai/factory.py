"""Build the configured LLM provider and embedder from settings."""

from __future__ import annotations

from functools import lru_cache

from app.ai.embeddings.base import Embedder
from app.ai.embeddings.hashing import HashingEmbedder
from app.ai.providers.base import LLMProvider
from app.ai.providers.mock import MockProvider
from app.core.config import Settings, get_settings
from app.db.models import EMBEDDING_DIM


def build_provider(settings: Settings) -> LLMProvider:
    if settings.ai_provider == "anthropic":
        from app.ai.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider(settings.anthropic_api_key or "", settings.anthropic_model)
    if settings.ai_provider == "openai":
        from app.ai.providers.openai_provider import OpenAIProvider

        return OpenAIProvider(settings.openai_api_key or "", settings.openai_model)
    return MockProvider()


def build_embedder(settings: Settings) -> Embedder:
    if settings.embedding_provider == "openai":
        from app.ai.embeddings.openai import OpenAIEmbedder

        return OpenAIEmbedder(
            settings.openai_api_key or "", settings.openai_embedding_model, EMBEDDING_DIM
        )
    return HashingEmbedder(EMBEDDING_DIM)


@lru_cache
def get_provider() -> LLMProvider:
    return build_provider(get_settings())


@lru_cache
def get_embedder() -> Embedder:
    return build_embedder(get_settings())
