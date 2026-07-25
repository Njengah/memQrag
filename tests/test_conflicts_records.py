"""Tests for memQrag.conflicts.records (SQLite conflict schema, Phase 5 PR 1).

Uses an in-memory SQLite database (`connect(":memory:")`) so these tests
never touch disk.
"""

import pytest

from memQrag.conflicts.records import (
    ConflictReviewStatus,
    connect,
    get_all_conflicts,
    get_conflict_by_id,
    record_conflict,
    set_review_status,
)


@pytest.fixture
def conn():
    connection = connect(":memory:")
    yield connection
    connection.close()


def test_record_conflict_returns_a_new_row_id(conn):
    conflict_id = record_conflict(
        conn,
        entity="return window",
        claim_a="Returns accepted within 30 days.",
        claim_b="Returns accepted within 14 days.",
        claim_a_chunk_ids=[1],
        claim_b_chunk_ids=[2],
    )

    assert isinstance(conflict_id, int)


def test_recorded_conflict_is_queryable_by_id(conn):
    conflict_id = record_conflict(
        conn,
        entity="return window",
        claim_a="Returns accepted within 30 days.",
        claim_b="Returns accepted within 14 days.",
        claim_a_chunk_ids=[1, 3],
        claim_b_chunk_ids=[2],
    )

    record = get_conflict_by_id(conn, conflict_id)

    assert record.entity == "return window"
    assert record.claim_a == "Returns accepted within 30 days."
    assert record.claim_b == "Returns accepted within 14 days."
    assert record.claim_a_chunk_ids == [1, 3]
    assert record.claim_b_chunk_ids == [2]


def test_new_conflict_starts_unreviewed(conn):
    conflict_id = record_conflict(
        conn,
        entity="return window",
        claim_a="30 days",
        claim_b="14 days",
        claim_a_chunk_ids=[1],
        claim_b_chunk_ids=[2],
    )

    record = get_conflict_by_id(conn, conflict_id)

    assert record.review_status is ConflictReviewStatus.UNREVIEWED
    assert record.detected_at is not None


def test_get_conflict_by_id_returns_none_for_unknown_id(conn):
    assert get_conflict_by_id(conn, 999) is None


def test_set_review_status_marks_a_conflict_reviewed(conn):
    conflict_id = record_conflict(
        conn,
        entity="return window",
        claim_a="30 days",
        claim_b="14 days",
        claim_a_chunk_ids=[1],
        claim_b_chunk_ids=[2],
    )

    set_review_status(conn, conflict_id, ConflictReviewStatus.REVIEWED)

    record = get_conflict_by_id(conn, conflict_id)
    assert record.review_status is ConflictReviewStatus.REVIEWED


def test_set_review_status_raises_for_unknown_id(conn):
    with pytest.raises(ValueError, match="999"):
        set_review_status(conn, 999, ConflictReviewStatus.REVIEWED)


def test_get_all_conflicts_returns_most_recently_detected_first(conn):
    older_id = record_conflict(
        conn,
        entity="shipping",
        claim_a="2 days",
        claim_b="5 days",
        claim_a_chunk_ids=[1],
        claim_b_chunk_ids=[2],
    )
    newer_id = record_conflict(
        conn,
        entity="return window",
        claim_a="30 days",
        claim_b="14 days",
        claim_a_chunk_ids=[3],
        claim_b_chunk_ids=[4],
    )

    records = get_all_conflicts(conn)

    assert [record.id for record in records] == [newer_id, older_id]


def test_get_all_conflicts_returns_empty_list_when_none_recorded(conn):
    assert get_all_conflicts(conn) == []


def test_chunk_id_lists_round_trip_empty(conn):
    conflict_id = record_conflict(
        conn,
        entity="warranty",
        claim_a="1 year",
        claim_b="2 years",
        claim_a_chunk_ids=[],
        claim_b_chunk_ids=[],
    )

    record = get_conflict_by_id(conn, conflict_id)

    assert record.claim_a_chunk_ids == []
    assert record.claim_b_chunk_ids == []


def test_connect_also_creates_shared_ingestion_and_memory_tables(conn):
    # conflicts.connect() must set up the shared database's
    # documents/chunks/session_memory/long_term_memory tables too, not just
    # conflicts, since all live in the same SQLite file; see
    # docs/DECISIONS.md ("SQLite Schema For Contradiction Records").
    conn.execute("SELECT * FROM documents")
    conn.execute("SELECT * FROM chunks")
    conn.execute("SELECT * FROM session_memory")
    conn.execute("SELECT * FROM long_term_memory")
    conn.execute("SELECT * FROM conflicts")
