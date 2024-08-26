"""LLM provider interface.

A provider only needs to implement `complete()`; the higher-level helpers build prompts
and parse responses. The mock provider overrides the helpers with deterministic
heuristics so the whole application works offline.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.ai.text import extract_keywords, split_sentences


@dataclass(frozen=True)
class ContextNote:
    index: int
    note_id: str
    title: str
    content: str
    score: float


SUMMARY_SYSTEM = (
    "You are MindScribe, an assistant that writes concise, faithful summaries of a "
    "user's personal notes. Respond with the summary only - no preamble."
)
TAGS_SYSTEM = (
    "You extract short topical tags from notes. Respond with a JSON array of lowercase "
    "strings (1-3 words each, hyphen-separated) and nothing else."
)
CHAT_SYSTEM = (
    "You are MindScribe, an assistant that answers questions using only the user's notes "
    "provided as context. Cite notes inline using their bracketed numbers like [1]. If the "
    "notes do not contain the answer, say so plainly instead of guessing."
)


class LLMProvider(ABC):
    name: str = "base"
    model: str = "n/a"

    @abstractmethod
    async def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        """Return the model's text completion for a system + user prompt."""

    async def summarize(self, text: str, max_sentences: int = 3) -> str:
        prompt = (
            f"Summarise the following note in at most {max_sentences} sentences.\n\n"
            f"<note>\n{text}\n</note>"
        )
        result = await self.complete(SUMMARY_SYSTEM, prompt, max_tokens=400)
        return result.strip()

    async def generate_tags(self, text: str, max_tags: int = 5) -> list[str]:
        prompt = f"Extract up to {max_tags} tags from this note.\n\n<note>\n{text}\n</note>"
        raw = await self.complete(TAGS_SYSTEM, prompt, max_tokens=200)
        return _parse_tag_list(raw, max_tags)

    async def answer(
        self, question: str, contexts: list[ContextNote], history: list[tuple[str, str]]
    ) -> str:
        blocks = [f"[{ctx.index}] {ctx.title}\n{ctx.content[:2000]}" for ctx in contexts]
        history_text = "\n".join(f"{role}: {content}" for role, content in history[-6:])
        prompt = (
            "Context notes:\n\n"
            + "\n\n".join(blocks)
            + "\n\n"
            + (f"Conversation so far:\n{history_text}\n\n" if history_text else "")
            + f"Question: {question}"
        )
        result = await self.complete(CHAT_SYSTEM, prompt, max_tokens=800)
        return result.strip()


def _parse_tag_list(raw: str, max_tags: int) -> list[str]:
    candidates: list[str] = []
    match = re.search(r"\[.*?\]", raw, flags=re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, list):
                candidates = [str(item) for item in parsed]
        except json.JSONDecodeError:
            candidates = []
    if not candidates:
        candidates = [part.strip(" -*#\"'") for part in re.split(r"[,\n]", raw)]
    cleaned: list[str] = []
    for tag in candidates:
        slug = re.sub(r"[^a-z0-9\- ]", "", tag.lower().strip()).strip()
        slug = re.sub(r"\s+", "-", slug)
        if slug and slug not in cleaned and len(slug) <= 50:
            cleaned.append(slug)
        if len(cleaned) >= max_tags:
            break
    return cleaned


__all__ = [
    "ContextNote",
    "LLMProvider",
    "extract_keywords",
    "split_sentences",
]
