"""Entity and claim comparison over retrieved chunks (Phase 5 PR 2).

Extracts quantitative factual claims from chunk text with a small,
deterministic pattern set (no LLM), groups them by normalized entity, and
persists a `conflicts` row whenever two chunks assert different values for
the same entity. Both claims are kept side by side — this module never
picks a winner (see AGENTS.md / PROJECT_BLUEPRINT).
`memQrag.conflicts.flagging.flag_conflicting_claims` consumes the returned
`ConflictRecord`s for query-response surfacing; this module only detects
and stores. See docs/DECISIONS.md ("Entity And Claim Comparison For
Retrieved Chunks").
"""

from __future__ import annotations

import re
import sqlite3
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from memQrag.conflicts.records import (
    ConflictRecord,
    get_all_conflicts,
    get_conflict_by_id,
    record_conflict,
)

# Sentence split matches memQrag.ingestion.chunking's boundary idea closely
# enough for claim extraction without importing that module's internals.
_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")

# Value patterns cover the quantitative policy facts the demo corpus uses
# (return windows, shipping times, warranties). Kept deliberately small and
# explicit — expanding the unit list later is a decision, not a silent change.
_VALUE_RE = re.compile(
    r"(?P<number>\d+(?:\.\d+)?)\s*(?P<unit>days?|hours?|years?|months?|percent|%)",
    re.IGNORECASE,
)

# Entity labels are the Conflict.entity values humans will review. Patterns
# are tried in order; first match wins so more-specific phrases beat bare
# keywords (e.g. "return window" before a bare "return").
_ENTITY_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\breturn\s+(?:window|policy|period)\b", re.IGNORECASE), "return window"),
    (re.compile(r"\breturns?\b", re.IGNORECASE), "return window"),
    (re.compile(r"\bshipping\b|\bdelivery\b", re.IGNORECASE), "shipping time"),
    (re.compile(r"\bwarranty\b", re.IGNORECASE), "warranty"),
)


class ChunkLike(Protocol):
    """Minimum shape needed from a retrieved chunk (e.g. ScoredRetrievalResult)."""

    chunk_id: int
    text: str


@dataclass(frozen=True)
class ExtractedClaim:
    """One quantitative factual claim pulled from a single chunk."""

    entity: str
    value: str
    claim_text: str
    chunk_id: int


@dataclass(frozen=True)
class ConflictingClaimPair:
    """Two claims about the same entity with different values — not yet persisted."""

    entity: str
    claim_a: ExtractedClaim
    claim_b: ExtractedClaim


def _normalize_unit(unit: str) -> str:
    lowered = unit.lower()
    if lowered == "%":
        return "percent"
    if lowered.endswith("s"):
        return lowered
    return f"{lowered}s"


def _normalize_value(number: str, unit: str) -> str:
    # Strip trailing .0 so "30.0 days" and "30 days" compare equal.
    normalized_number = number.rstrip("0").rstrip(".") if "." in number else number
    return f"{normalized_number} {_normalize_unit(unit)}"


def _entity_for_sentence(sentence: str) -> str | None:
    for pattern, entity in _ENTITY_PATTERNS:
        if pattern.search(sentence):
            return entity
    return None


def extract_claims_from_text(chunk_id: int, text: str) -> list[ExtractedClaim]:
    """Extract quantitative entity claims from one chunk's text.

    A claim is emitted only when a sentence both (a) matches a known entity
    pattern and (b) contains a numeric value with a recognized unit. Sentences
    with numbers but no known entity are ignored — better to miss a conflict
    than invent an entity label the demo cannot explain.
    """
    if not text.strip():
        return []

    claims: list[ExtractedClaim] = []
    sentences = _SENTENCE_BOUNDARY_RE.split(text.strip())
    for sentence in sentences:
        entity = _entity_for_sentence(sentence)
        if entity is None:
            continue
        for match in _VALUE_RE.finditer(sentence):
            value = _normalize_value(match.group("number"), match.group("unit"))
            claims.append(
                ExtractedClaim(
                    entity=entity,
                    value=value,
                    claim_text=sentence.strip(),
                    chunk_id=chunk_id,
                )
            )
    return claims


def extract_claims(chunks: Sequence[ChunkLike]) -> list[ExtractedClaim]:
    """Extract claims from every chunk, in input order."""
    claims: list[ExtractedClaim] = []
    for chunk in chunks:
        claims.extend(extract_claims_from_text(chunk.chunk_id, chunk.text))
    return claims


def find_conflicting_claim_pairs(claims: Sequence[ExtractedClaim]) -> list[ConflictingClaimPair]:
    """Return one pair per unordered (entity, value_a, value_b) conflict.

    Claims from the same chunk never conflict with each other (a single
    source restating itself is not a cross-source contradiction). When more
    than two distinct values appear for one entity, every unordered value
    pair is reported — each is a separate conflict humans may need to review.
    """
    by_entity: dict[str, dict[str, list[ExtractedClaim]]] = defaultdict(lambda: defaultdict(list))
    for claim in claims:
        by_entity[claim.entity][claim.value].append(claim)

    pairs: list[ConflictingClaimPair] = []
    for entity, values in by_entity.items():
        distinct_values = sorted(values)
        for i, value_a in enumerate(distinct_values):
            for value_b in distinct_values[i + 1 :]:
                claim_a = values[value_a][0]
                claim_b = values[value_b][0]
                if claim_a.chunk_id == claim_b.chunk_id:
                    continue
                pairs.append(ConflictingClaimPair(entity=entity, claim_a=claim_a, claim_b=claim_b))
    return pairs


def _claims_match_existing(pair: ConflictingClaimPair, existing: ConflictRecord) -> bool:
    if existing.entity != pair.entity:
        return False
    existing_claims = {existing.claim_a, existing.claim_b}
    return pair.claim_a.claim_text in existing_claims and pair.claim_b.claim_text in existing_claims


def detect_conflicts(
    conn: sqlite3.Connection,
    chunks: Sequence[ChunkLike],
) -> list[ConflictRecord]:
    """Extract claims from `chunks`, persist new conflicts, return every conflict
    found in this call (newly recorded or already present).

    Idempotent for identical claim text pairs: a second call with the same
    opposing claims does not insert a duplicate row. Does not filter or alter
    `chunks` — detection is observational, not a retrieval filter.
    """
    claims = extract_claims(chunks)
    pairs = find_conflicting_claim_pairs(claims)
    existing = get_all_conflicts(conn)

    results: list[ConflictRecord] = []
    for pair in pairs:
        already = next((row for row in existing if _claims_match_existing(pair, row)), None)
        if already is not None:
            results.append(already)
            continue

        # Collect every chunk id that asserted each value, not just the first.
        claim_a_chunk_ids = sorted(
            {
                claim.chunk_id
                for claim in claims
                if claim.entity == pair.entity and claim.value == pair.claim_a.value
            }
        )
        claim_b_chunk_ids = sorted(
            {
                claim.chunk_id
                for claim in claims
                if claim.entity == pair.entity and claim.value == pair.claim_b.value
            }
        )
        conflict_id = record_conflict(
            conn,
            entity=pair.entity,
            claim_a=pair.claim_a.claim_text,
            claim_b=pair.claim_b.claim_text,
            claim_a_chunk_ids=claim_a_chunk_ids,
            claim_b_chunk_ids=claim_b_chunk_ids,
        )
        record = get_conflict_by_id(conn, conflict_id)
        assert record is not None
        results.append(record)
        existing.append(record)

    return results
