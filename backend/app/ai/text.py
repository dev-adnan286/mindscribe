"""Small, dependency-free text utilities shared by the mock provider and embedder."""

from __future__ import annotations

import math
import re
from collections import Counter

STOPWORDS: frozenset[str] = frozenset(
    """
    a about above after again against all am an and any are as at be because been before
    being below between both but by can could did do does doing down during each few for
    from further had has have having he her here hers herself him himself his how i if in
    into is it its itself just let me more most my myself no nor not now of off on once
    only or other our ours ourselves out over own same she should so some such than that
    the their theirs them themselves then there these they this those through to too under
    until up very was we were what when where which while who whom why will with would you
    your yours yourself yourselves also however thus therefore might may shall us
    """.split()
)

_WORD_RE = re.compile(r"[a-z0-9][a-z0-9'\-]*")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])|\n{2,}")
_MARKDOWN_NOISE = re.compile(r"[#*_`>\[\]()|~]+")


def strip_markdown(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = _MARKDOWN_NOISE.sub(" ", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def tokenize(text: str) -> list[str]:
    return [tok for tok in _WORD_RE.findall(text.lower()) if tok not in STOPWORDS and len(tok) > 1]


def split_sentences(text: str) -> list[str]:
    cleaned = strip_markdown(text)
    parts = [part.strip() for part in _SENTENCE_RE.split(cleaned) if part and part.strip()]
    return [part for part in parts if len(part) > 2]


def extract_keywords(text: str, limit: int = 5) -> list[str]:
    """Frequency-and-length weighted unigrams plus frequent bigrams."""
    tokens = tokenize(strip_markdown(text))
    if not tokens:
        return []
    unigram_counts = Counter(tokens)
    bigram_counts = Counter(f"{a}-{b}" for a, b in zip(tokens, tokens[1:], strict=False) if a != b)
    scores: dict[str, float] = {}
    for word, count in unigram_counts.items():
        if word.isdigit():
            continue
        scores[word] = count * (1 + math.log(1 + len(word)) / 3)
    for bigram, count in bigram_counts.items():
        if count >= 2:
            scores[bigram] = count * 2.2
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    result: list[str] = []
    for word, _score in ranked:
        # skip unigrams that are already part of a chosen bigram
        if any(word != chosen and word in chosen.split("-") for chosen in result):
            continue
        result.append(word)
        if len(result) >= limit:
            break
    return result


def score_sentences(sentences: list[str]) -> list[float]:
    """Score sentences by keyword density relative to the whole document."""
    doc_counts = Counter(tok for sentence in sentences for tok in tokenize(sentence))
    scores: list[float] = []
    for index, sentence in enumerate(sentences):
        tokens = tokenize(sentence)
        if not tokens:
            scores.append(0.0)
            continue
        density = sum(doc_counts[tok] for tok in tokens) / math.sqrt(len(tokens))
        position_bonus = 1.15 if index == 0 else 1.0
        scores.append(density * position_bonus)
    return scores


def truncate(text: str, limit: int = 160) -> str:
    cleaned = strip_markdown(text).replace("\n", " ")
    if len(cleaned) <= limit:
        return cleaned
    cut = cleaned[:limit].rsplit(" ", 1)[0]
    return f"{cut}..."
