"""OpenAI chat-completions provider. The SDK is imported lazily so it stays optional."""

from __future__ import annotations

from typing import Any

from app.ai.providers.base import LLMProvider
from app.core.exceptions import ServiceUnavailableError


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for the openai provider")
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise ServiceUnavailableError(
                "The 'openai' package is not installed. Install with "
                "`pip install 'mindscribe-backend[openai]'`."
            ) from exc
        self.model = model
        self._client: Any = AsyncOpenAI(api_key=api_key)

    async def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        from openai import APIConnectionError, APIStatusError, RateLimitError

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except RateLimitError as exc:
            raise ServiceUnavailableError("OpenAI rate limit reached, retry shortly") from exc
        except APIStatusError as exc:
            raise ServiceUnavailableError(f"OpenAI API error: {exc.status_code}") from exc
        except APIConnectionError as exc:
            raise ServiceUnavailableError("Could not reach the OpenAI API") from exc
        choice = response.choices[0] if response.choices else None
        return (choice.message.content or "") if choice else ""
