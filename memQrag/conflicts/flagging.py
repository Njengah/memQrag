"""Flag conflicting factual claims on query-response evidence (Phase 5 PR 3).

Takes the final retrieved chunks for a query, runs
`memQrag.conflicts.compare.detect_conflicts`, and returns a response-shaped
bundle that keeps every chunk unchanged while attaching conflict warnings
that carry **both** opposing claims. Callers (Phase 7's `POST /api/query`,
Phase 8's contradiction alert) must surface those warnings rather than
synthesizing a single resolved claim — see AGENTS.md / PROJECT_BLUEPRINT.
See docs/DECISIONS.md ("Flag Conflicting Factual Claims In Query Responses").
"""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass

from memQrag.conflicts.compare import ChunkLike, detect_conflicts
from memQrag.conflicts.records import ConflictRecord, ConflictReviewStatus


@dataclass(frozen=True)
class ConflictWarning:
    """One conflict to surface on a query response — both claims, no winner."""

    conflict_id: int
    entity: str
    claim_a: str
    claim_b: str
    claim_a_chunk_ids: tuple[int, ...]
    claim_b_chunk_ids: tuple[int, ...]
    review_status: ConflictReviewStatus

    @property
    def involved_chunk_ids(self) -> frozenset[int]:
        return frozenset(self.claim_a_chunk_ids) | frozenset(self.claim_b_chunk_ids)


@dataclass(frozen=True)
class ConflictFlaggedQueryEvidence:
    """Retrieval evidence for a query response, with conflicts flagged.

    `chunks` are the same objects passed in (order preserved, nothing
    filtered or re-ranked). `conflicts` are the warnings that must appear
    alongside any answer synthesized from those chunks.
    """

    chunks: tuple[ChunkLike, ...]
    conflicts: tuple[ConflictWarning, ...]

    @property
    def conflicted_chunk_ids(self) -> frozenset[int]:
        ids: set[int] = set()
        for warning in self.conflicts:
            ids.update(warning.involved_chunk_ids)
        return frozenset(ids)

    def chunk_is_conflicted(self, chunk_id: int) -> bool:
        """True when `chunk_id` supports at least one side of a flagged conflict."""
        return chunk_id in self.conflicted_chunk_ids

    def conflicts_for_chunk(self, chunk_id: int) -> list[ConflictWarning]:
        """Return every warning that involves `chunk_id`, in the same order as
        `conflicts`."""
        return [warning for warning in self.conflicts if chunk_id in warning.involved_chunk_ids]


def _warning_from_record(record: ConflictRecord) -> ConflictWarning:
    return ConflictWarning(
        conflict_id=record.id,
        entity=record.entity,
        claim_a=record.claim_a,
        claim_b=record.claim_b,
        claim_a_chunk_ids=tuple(record.claim_a_chunk_ids),
        claim_b_chunk_ids=tuple(record.claim_b_chunk_ids),
        review_status=record.review_status,
    )


def flag_conflicting_claims(
    conn: sqlite3.Connection,
    chunks: Sequence[ChunkLike],
) -> ConflictFlaggedQueryEvidence:
    """Detect conflicts among `chunks` and return them flagged for a query response.

    Runs `detect_conflicts` (which persists new rows) then wraps the results
    as `ConflictWarning`s. Does not generate answer text, does not drop or
    reorder chunks, and does not choose between `claim_a` and `claim_b`.
    """
    records = detect_conflicts(conn, chunks)
    return ConflictFlaggedQueryEvidence(
        chunks=tuple(chunks),
        conflicts=tuple(_warning_from_record(record) for record in records),
    )
