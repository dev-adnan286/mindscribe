"""Anthropic Claude provider. The SDK is imported lazily so it stays optional."""

from __future__ import annotations

from typing import Any

from app.ai.providers.base import LLMProvider
from app.core.exceptions import ServiceUnavailableError


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-sonnet-5") -> None:
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for the anthropic provider")
        try:
            from anthropic import AsyncAnthropic
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise ServiceUnavailableError(
                "The 'anthropic' package is not installed. Install with "
                "`pip install 'mindscribe-backend[anthropic]'`."
            ) from exc
        self.model = model
        self._client: Any = AsyncAnthropic(api_key=api_key)

    async def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        from anthropic import APIConnectionError, APIStatusError, RateLimitError

        try:
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        except RateLimitError as exc:
            raise ServiceUnavailableError("Anthropic rate limit reached, retry shortly") from exc
        except APIStatusError as exc:
            raise ServiceUnavailableError(f"Anthropic API error: {exc.status_code}") from exc
        except APIConnectionError as exc:
            raise ServiceUnavailableError("Could not reach the Anthropic API") from exc
        if getattr(response, "stop_reason", None) == "refusal":
            return "The assistant declined to answer this request."
        parts = [block.text for block in response.content if getattr(block, "type", "") == "text"]
        return "".join(parts)
