"""Deterministic offline provider used by default and in tests.

It produces useful output with simple extractive heuristics: summaries pick the most
keyword-dense sentences, tags come from term frequency, and chat answers quote the most
relevant sentences from the retrieved notes with bracketed citations.
"""

from __future__ import annotations

from app.ai.providers.base import ContextNote, LLMProvider
from app.ai.text import extract_keywords, score_sentences, split_sentences, tokenize


class MockProvider(LLMProvider):
    name = "mock"
    model = "mindscribe-heuristics-v1"

    async def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        sentences = split_sentences(user)
        return " ".join(sentences[:2]) if sentences else "I could not produce a completion."

    async def summarize(self, text: str, max_sentences: int = 3) -> str:
        sentences = split_sentences(text)
        if not sentences:
            return "This note is empty."
        if len(sentences) <= max_sentences:
            return " ".join(sentences)
        scores = score_sentences(sentences)
        top = sorted(range(len(sentences)), key=lambda i: -scores[i])[:max_sentences]
        return " ".join(sentences[i] for i in sorted(top))

    async def generate_tags(self, text: str, max_tags: int = 5) -> list[str]:
        return extract_keywords(text, limit=max_tags)

    async def answer(
        self, question: str, contexts: list[ContextNote], history: list[tuple[str, str]]
    ) -> str:
        if not contexts:
            return (
                "I couldn't find any notes related to your question. "
                "Try adding notes on this topic first."
            )
        question_terms = set(tokenize(question))
        picked: list[tuple[float, str, int]] = []
        for ctx in contexts:
            for sentence in split_sentences(ctx.content):
                overlap = len(question_terms & set(tokenize(sentence)))
                if overlap:
                    picked.append((overlap + ctx.score, sentence, ctx.index))
        picked.sort(key=lambda item: -item[0])
        lines: list[str] = []
        used_indexes: list[int] = []
        for _score, sentence, index in picked[:3]:
            lines.append(f"{sentence} [{index}]")
            if index not in used_indexes:
                used_indexes.append(index)
        if not lines:
            first = contexts[0]
            snippet = " ".join(split_sentences(first.content)[:2]) or first.title
            lines.append(f'The closest match is "{first.title}": {snippet} [{first.index}]')
            used_indexes.append(first.index)
        cited = ", ".join(f"[{i}]" for i in used_indexes)
        return "Based on your notes: " + " ".join(lines) + f"\n\nSources: {cited}"
