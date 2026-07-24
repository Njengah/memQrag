"""Tests for memQrag.memory.long_term (SQLite long-term memory schema, Phase 4 PR 2/PR 3).

Uses an in-memory SQLite database (`connect(":memory:")`) so these tests
never touch disk. Uses a short hand-picked vector as the "embedding" for
every record — these tests exercise storage/round-tripping, not cosine
similarity, which `tests/test_memory_boost.py` covers instead.
"""

from datetime import UTC, datetime

import pytest

from memQrag.memory.long_term import (
    connect,
    get_all_long_term_memory,
    get_long_term_memory_by_id,
    record_long_term_memory,
    update_long_term_memory,
)

_EMBEDDING = [0.1, 0.2, 0.3]


@pytest.fixture
def conn():
    connection = connect(":memory:")
    yield connection
    connection.close()


def test_record_long_term_memory_returns_a_new_row_id(conn):
    long_term_memory_id = record_long_term_memory(
        conn, "What is the return policy?", _EMBEDDING, [1, 2]
    )

    assert isinstance(long_term_memory_id, int)


def test_recorded_memory_is_queryable_by_id(conn):
    long_term_memory_id = record_long_term_memory(
        conn, "What is the return policy?", _EMBEDDING, [1, 2]
    )

    record = get_long_term_memory_by_id(conn, long_term_memory_id)

    assert record.query == "What is the return policy?"
    assert record.best_document_ids == [1, 2]


def test_recorded_memory_round_trips_its_query_embedding(conn):
    long_term_memory_id = record_long_term_memory(conn, "query", [0.5, -0.25, 0.75], [1])

    record = get_long_term_memory_by_id(conn, long_term_memory_id)

    assert record.query_embedding == pytest.approx([0.5, -0.25, 0.75])


def test_new_record_starts_with_default_counters(conn):
    long_term_memory_id = record_long_term_memory(
        conn, "What is the return policy?", _EMBEDDING, [1]
    )

    record = get_long_term_memory_by_id(conn, long_term_memory_id)

    assert record.success_count == 0
    assert record.match_count == 0
    assert record.hit_rate == 0.0
    assert record.decay_weight == 1.0
    assert record.last_used is not None


def test_get_long_term_memory_by_id_returns_none_for_unknown_id(conn):
    assert get_long_term_memory_by_id(conn, 999) is None


def test_update_long_term_memory_sets_success_count(conn):
    long_term_memory_id = record_long_term_memory(conn, "query", _EMBEDDING, [1])

    update_long_term_memory(conn, long_term_memory_id, success_count=3)

    record = get_long_term_memory_by_id(conn, long_term_memory_id)
    assert record.success_count == 3


def test_update_long_term_memory_sets_match_count(conn):
    long_term_memory_id = record_long_term_memory(conn, "query", _EMBEDDING, [1])

    update_long_term_memory(conn, long_term_memory_id, match_count=4)

    record = get_long_term_memory_by_id(conn, long_term_memory_id)
    assert record.match_count == 4


def test_update_long_term_memory_sets_hit_rate(conn):
    long_term_memory_id = record_long_term_memory(conn, "query", _EMBEDDING, [1])

    update_long_term_memory(conn, long_term_memory_id, hit_rate=0.75)

    record = get_long_term_memory_by_id(conn, long_term_memory_id)
    assert record.hit_rate == pytest.approx(0.75)


def test_update_long_term_memory_sets_decay_weight(conn):
    long_term_memory_id = record_long_term_memory(conn, "query", _EMBEDDING, [1])

    update_long_term_memory(conn, long_term_memory_id, decay_weight=0.5)

    record = get_long_term_memory_by_id(conn, long_term_memory_id)
    assert record.decay_weight == pytest.approx(0.5)


def test_update_long_term_memory_sets_last_used(conn):
    long_term_memory_id = record_long_term_memory(conn, "query", _EMBEDDING, [1])
    new_last_used = datetime(2026, 1, 1, tzinfo=UTC)

    update_long_term_memory(conn, long_term_memory_id, last_used=new_last_used)

    record = get_long_term_memory_by_id(conn, long_term_memory_id)
    assert record.last_used == new_last_used


def test_update_long_term_memory_leaves_omitted_fields_unchanged(conn):
    long_term_memory_id = record_long_term_memory(conn, "query", _EMBEDDING, [1])
    update_long_term_memory(conn, long_term_memory_id, success_count=5, hit_rate=0.9)

    update_long_term_memory(conn, long_term_memory_id, decay_weight=0.2)

    record = get_long_term_memory_by_id(conn, long_term_memory_id)
    assert record.success_count == 5
    assert record.hit_rate == pytest.approx(0.9)
    assert record.decay_weight == pytest.approx(0.2)


def test_update_long_term_memory_raises_for_unknown_id(conn):
    with pytest.raises(ValueError, match="999"):
        update_long_term_memory(conn, 999, success_count=1)


def test_get_all_long_term_memory_returns_most_recently_used_first(conn):
    older_id = record_long_term_memory(conn, "older query", _EMBEDDING, [1])
    newer_id = record_long_term_memory(conn, "newer query", _EMBEDDING, [2])
    update_long_term_memory(conn, older_id, last_used=datetime(2020, 1, 1, tzinfo=UTC))
    update_long_term_memory(conn, newer_id, last_used=datetime(2026, 1, 1, tzinfo=UTC))

    records = get_all_long_term_memory(conn)

    assert [record.id for record in records] == [newer_id, older_id]


def test_get_all_long_term_memory_returns_empty_list_when_none_recorded(conn):
    assert get_all_long_term_memory(conn) == []


def test_best_document_ids_round_trips_empty_list(conn):
    long_term_memory_id = record_long_term_memory(conn, "no matches found", _EMBEDDING, [])

    record = get_long_term_memory_by_id(conn, long_term_memory_id)

    assert record.best_document_ids == []


def test_connect_also_creates_shared_ingestion_and_session_tables(conn):
    # memory.long_term.connect() must set up the shared database's
    # documents/chunks/session_memory tables too, not just
    # long_term_memory, since all four live in the same SQLite file; see
    # docs/DECISIONS.md ("SQLite Schema For Long-Term Memory Records").
    conn.execute("SELECT * FROM documents")
    conn.execute("SELECT * FROM chunks")
    conn.execute("SELECT * FROM session_memory")
    conn.execute("SELECT * FROM long_term_memory")
