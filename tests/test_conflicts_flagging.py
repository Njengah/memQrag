"""Tests for memQrag.conflicts.flagging (query-response conflict flags, Phase 5 PR 3)."""

from dataclasses import dataclass

import pytest

from memQrag.conflicts.flagging import flag_conflicting_claims
from memQrag.conflicts.records import ConflictReviewStatus, connect


@dataclass(frozen=True)
class _Chunk:
    chunk_id: int
    text: str


@pytest.fixture
def conn():
    connection = connect(":memory:")
    yield connection
    connection.close()


def test_flag_conflicting_claims_attaches_both_claims_without_picking_a_winner(conn):
    chunks = [
        _Chunk(1, "Fictional returns are accepted within 30 days of purchase."),
        _Chunk(2, "Fictional returns must be made within 14 days."),
    ]

    evidence = flag_conflicting_claims(conn, chunks)

    assert len(evidence.conflicts) == 1
    warning = evidence.conflicts[0]
    assert warning.entity == "return window"
    assert {warning.claim_a, warning.claim_b} == {chunks[0].text, chunks[1].text}
    assert warning.review_status is ConflictReviewStatus.UNREVIEWED
    # Both claims present — neither is dropped or preferred.
    assert warning.claim_a != warning.claim_b


def test_flag_conflicting_claims_preserves_chunk_order_and_identity(conn):
    chunks = [
        _Chunk(1, "Fictional returns are accepted within 30 days of purchase."),
        _Chunk(2, "Fictional returns must be made within 14 days."),
        _Chunk(3, "A fictional bakery introduced a new sourdough recipe."),
    ]

    evidence = flag_conflicting_claims(conn, chunks)

    assert evidence.chunks == tuple(chunks)
    assert [chunk.chunk_id for chunk in evidence.chunks] == [1, 2, 3]


def test_flag_conflicting_claims_marks_only_involved_chunks_as_conflicted(conn):
    chunks = [
        _Chunk(1, "Fictional returns are accepted within 30 days of purchase."),
        _Chunk(2, "Fictional returns must be made within 14 days."),
        _Chunk(3, "A fictional bakery introduced a new sourdough recipe."),
    ]

    evidence = flag_conflicting_claims(conn, chunks)

    assert evidence.conflicted_chunk_ids == frozenset({1, 2})
    assert evidence.chunk_is_conflicted(1) is True
    assert evidence.chunk_is_conflicted(2) is True
    assert evidence.chunk_is_conflicted(3) is False
    assert evidence.conflicts_for_chunk(1) == list(evidence.conflicts)
    assert evidence.conflicts_for_chunk(3) == []


def test_flag_conflicting_claims_returns_no_warnings_when_chunks_agree(conn):
    chunks = [
        _Chunk(1, "Fictional returns are accepted within 30 days of purchase."),
        _Chunk(2, "The fictional return window is 30 days."),
    ]

    evidence = flag_conflicting_claims(conn, chunks)

    assert evidence.conflicts == ()
    assert evidence.conflicted_chunk_ids == frozenset()
    assert evidence.chunks == tuple(chunks)


def test_flag_conflicting_claims_returns_empty_evidence_for_empty_input(conn):
    evidence = flag_conflicting_claims(conn, [])

    assert evidence.chunks == ()
    assert evidence.conflicts == ()
