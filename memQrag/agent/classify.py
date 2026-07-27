"""Query classification for agentic orchestration (Phase 6 PR 1).

Assigns each user query one of FACTUAL / COMPARATIVE / MULTI-HOP /
UNKNOWN so later Phase 6 steps can route retrieval and synthesis.
Classification is deterministic and LLM-free: `docs/ARCHITECTURE.md`
has not selected an LLM provider yet, and Phase 5's claim extraction
already established the "deterministic first" precedent for agent-path
routing logic. See docs/DECISIONS.md ("Query Classification Labels And
Deterministic Rules").
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

# Comparative cues are checked first — an explicit "compare A vs B" should
# route to comparative retrieval even when the sentence also has "and".
_COMPARATIVE_RE = re.compile(
    r"(?:"
    r"\bcompare\b|\bcomparison\b|\bversus\b|\bvs\.?\b|"
    r"\bdifference(?:s)?\s+between\b|\bcontrast\b|"
    r"\bbetter\s+than\b|\bworse\s+than\b|"
    r"\bwhich\s+(?:is|are|one)\s+(?:better|worse|preferred|best)\b|"
    r"\bsimilar(?:ities)?\s+and\s+difference(?:s)?\b|"
    r"\bhow\s+(?:does|do)\b.+\bdiffer\b"
    r")",
    re.IGNORECASE,
)

# Multi-hop cues: chained lookups or multiple distinct interrogatives.
_MULTI_HOP_RE = re.compile(
    r"(?:"
    r"\band\s+then\b|"
    r"\bafter\s+(?:that|finding|determining|knowing|identifying)\b|"
    r"\bbased\s+on\s+(?:that|this|the\s+(?:previous\s+|above\s+)?"
    r"(?:answer|result|response))\b|"
    r"\busing\s+(?:that|those|the\s+(?:previous|above)\s+"
    r"(?:answer|result))\b|"
    r"\bif\b.+\b(?:what|when|where|who|how|which)\b"
    r")",
    re.IGNORECASE,
)

_INTERROGATIVE_RE = re.compile(
    r"\b(?:what|when|where|who|why|how|which)\b",
    re.IGNORECASE,
)

# Single-hop fact seeking. Applied only after comparative/multi-hop miss.
_FACTUAL_RE = re.compile(
    r"(?:"
    r"^\s*(?:what|when|where|who|why|how|which|does|do|is|are|can|will|"
    r"tell\s+me)\b|"
    r"\bhow\s+(?:long|many|much|often)\b|"
    r"\b(?:what|when|where|who|why|how|which)\b.+\?\s*$"
    r")",
    re.IGNORECASE | re.DOTALL,
)

# Pure non-questions / noise that should not look like factual lookups.
_UNKNOWN_NOISE_RE = re.compile(
    r"^\s*(?:hi|hello|hey|thanks|thank\s+you|ok|okay|yo|sup)\s*[!.]*\s*$",
    re.IGNORECASE,
)


class QueryType(str, Enum):
    """Query routing labels from docs/ARCHITECTURE.md retrieval flow step 1."""

    FACTUAL = "factual"
    COMPARATIVE = "comparative"
    MULTI_HOP = "multi-hop"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class QueryClassification:
    """Result of classifying one user query.

    `normalized_query` is the stripped input used for matching. `query_type`
    is the single routing label later Phase 6 steps must branch on.
    """

    query_type: QueryType
    normalized_query: str


def _has_multiple_interrogatives(text: str) -> bool:
    """True when two+ interrogatives appear with a linking connector between them.

    Catches "What is X and when is Y?" without treating "What are return and
    shipping policies?" (one interrogative, compound noun) as multi-hop.
    """
    matches = list(_INTERROGATIVE_RE.finditer(text))
    if len(matches) < 2:
        return False
    between = text[matches[0].end() : matches[1].start()]
    return bool(re.search(r"\b(?:and|then|;)\b", between, re.IGNORECASE))


def classify_query(query: str) -> QueryClassification:
    """Classify `query` into FACTUAL / COMPARATIVE / MULTI-HOP / UNKNOWN.

    Priority: COMPARATIVE > MULTI-HOP > FACTUAL > UNKNOWN. Empty or
    whitespace-only input is UNKNOWN. Never calls an LLM.
    """
    normalized = query.strip()
    if not normalized:
        return QueryClassification(QueryType.UNKNOWN, normalized)

    if _COMPARATIVE_RE.search(normalized):
        return QueryClassification(QueryType.COMPARATIVE, normalized)

    if _MULTI_HOP_RE.search(normalized) or _has_multiple_interrogatives(normalized):
        return QueryClassification(QueryType.MULTI_HOP, normalized)

    if _UNKNOWN_NOISE_RE.match(normalized):
        return QueryClassification(QueryType.UNKNOWN, normalized)

    if _FACTUAL_RE.search(normalized):
        return QueryClassification(QueryType.FACTUAL, normalized)

    return QueryClassification(QueryType.UNKNOWN, normalized)
