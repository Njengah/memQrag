"""Semantic chunking for memQrag document ingestion (Phase 2 PR 3).

Turns an `ExtractedDocument`'s segments into `Chunk`s:

1. Split each segment's text into sentences.
2. Embed the sentences and start a new group wherever cosine similarity
   between adjacent sentence embeddings drops below a threshold (a semantic
   breakpoint).
3. Merge any group under `MIN_CHUNK_TOKENS` into a neighboring group.
4. Split any group over `MAX_CHUNK_TOKENS` back into multiple chunks at
   sentence boundaries.

Chunks never span more than one segment, so each chunk's inherited
`page_number`/`section_heading` stays accurate.

The embedding step is injected via `EmbeddingFunction` so this algorithm is
deterministically unit-testable without downloading a model or calling a
network; see tests/test_ingestion_chunking.py, which uses a fake embedder.
The default production embedder is
`memQrag.ingestion.embeddings.embed_sentences`. See docs/DECISIONS.md
("Semantic Chunking Algorithm") for the full rationale, including why token
counts are a whitespace-based approximation rather than a specific LLM
tokenizer.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from math import sqrt

from memQrag.ingestion.extraction import ExtractedDocument, ExtractedSegment

MIN_CHUNK_TOKENS = 200
MAX_CHUNK_TOKENS = 800
_SIMILARITY_BREAKPOINT = 0.5

EmbeddingFunction = Callable[[Sequence[str]], Sequence[Sequence[float]]]

_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")


@dataclass(frozen=True)
class Chunk:
    """A chunk ready for persistence (Phase 2 PRs 4-5).

    Omits `chunk_id`, `document_id`, and an embedding reference from
    docs/ARCHITECTURE.md's planned Chunk entity; those only become
    meaningful once persistence assigns real identifiers.
    """

    text: str
    token_count: int
    source_document: str
    page_number: int | None
    section_heading: str | None


def estimate_token_count(text: str) -> int:
    """Approximate token count via whitespace word count.

    A deliberate approximation, not a specific LLM tokenizer; see
    docs/DECISIONS.md ("Semantic Chunking Algorithm").
    """
    return len(text.split())


def split_sentences(text: str) -> list[str]:
    """Split text into sentences using a punctuation-based heuristic.

    Lightweight and dependency-free (no NLTK/spaCy); sufficient for the
    demo's fictional documents.
    """
    stripped = text.strip()
    if not stripped:
        return []
    return [s.strip() for s in _SENTENCE_BOUNDARY_RE.split(stripped) if s.strip()]


def chunk_document(document: ExtractedDocument, embed: EmbeddingFunction) -> list[Chunk]:
    """Chunk every segment of an extracted document independently."""
    chunks: list[Chunk] = []
    for segment in document.segments:
        chunks.extend(_chunk_segment(segment, document.source_document, embed))
    return chunks


def _chunk_segment(
    segment: ExtractedSegment, source_document: str, embed: EmbeddingFunction
) -> list[Chunk]:
    sentences = split_sentences(segment.text)
    if not sentences:
        return []

    if len(sentences) == 1:
        groups = [sentences]
    else:
        embeddings = embed(sentences)
        groups = _group_by_similarity(sentences, embeddings)

    groups = _merge_undersized_groups(groups)
    groups = [split_group for group in groups for split_group in _split_if_oversized(group)]

    chunks = []
    for group in groups:
        text = " ".join(group)
        chunks.append(
            Chunk(
                text=text,
                token_count=estimate_token_count(text),
                source_document=source_document,
                page_number=segment.page_number,
                section_heading=segment.section_heading,
            )
        )
    return chunks


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sqrt(sum(x * x for x in a))
    norm_b = sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _group_by_similarity(
    sentences: list[str], embeddings: Sequence[Sequence[float]]
) -> list[list[str]]:
    groups: list[list[str]] = [[sentences[0]]]
    for index in range(1, len(sentences)):
        similarity = _cosine_similarity(embeddings[index - 1], embeddings[index])
        if similarity < _SIMILARITY_BREAKPOINT:
            groups.append([sentences[index]])
        else:
            groups[-1].append(sentences[index])
    return groups


def _group_token_count(group: list[str]) -> int:
    return sum(estimate_token_count(sentence) for sentence in group)


def _merge_undersized_groups(groups: list[list[str]]) -> list[list[str]]:
    """Merge groups under MIN_CHUNK_TOKENS forward; fix up a trailing runt.

    This is a pure token-count pass: once a group is undersized, it merges
    into its neighbor regardless of semantic similarity.
    """
    if not groups:
        return groups

    merged: list[list[str]] = [list(groups[0])]
    for group in groups[1:]:
        if _group_token_count(merged[-1]) < MIN_CHUNK_TOKENS:
            merged[-1].extend(group)
        else:
            merged.append(list(group))

    if len(merged) > 1 and _group_token_count(merged[-1]) < MIN_CHUNK_TOKENS:
        merged[-2].extend(merged.pop())

    return merged


def _split_if_oversized(group: list[str]) -> list[list[str]]:
    """Split a group back under MAX_CHUNK_TOKENS, greedily by sentence."""
    if _group_token_count(group) <= MAX_CHUNK_TOKENS:
        return [group]

    result: list[list[str]] = []
    current: list[str] = []
    current_tokens = 0
    for sentence in group:
        sentence_tokens = estimate_token_count(sentence)
        if current and current_tokens + sentence_tokens > MAX_CHUNK_TOKENS:
            result.append(current)
            current = []
            current_tokens = 0
        current.append(sentence)
        current_tokens += sentence_tokens
    if current:
        result.append(current)
    return result
