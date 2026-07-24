"""Tests for memQrag.memory.session (SQLite session memory schema, Phase 4 PR 1).

Uses an in-memory SQLite database (`connect(":memory:")`) so these tests
never touch disk.
"""

import pytest

from memQrag.memory.session import (
    connect,
    get_session_memory,
    record_session_query,
    set_usefulness,
)


@pytest.fixture
def conn():
    connection = connect(":memory:")
    yield connection
    connection.close()


def test_record_session_query_returns_a_new_row_id(conn):
    session_memory_id = record_session_query(
        conn, "session-1", "What is the return policy?", [1, 2]
    )

    assert isinstance(session_memory_id, int)


def test_recorded_query_is_queryable_by_session_id(conn):
    record_session_query(conn, "session-1", "What is the return policy?", [1, 2])

    (record,) = get_session_memory(conn, "session-1")

    assert record.session_id == "session-1"
    assert record.query == "What is the return policy?"
    assert record.retrieved_chunk_ids == [1, 2]


def test_usefulness_flag_starts_unset(conn):
    record_session_query(conn, "session-1", "What is the return policy?", [1])

    (record,) = get_session_memory(conn, "session-1")

    assert record.usefulness_flag is None


def test_set_usefulness_marks_a_query_useful(conn):
    session_memory_id = record_session_query(conn, "session-1", "What is the return policy?", [1])

    set_usefulness(conn, session_memory_id, useful=True)

    (record,) = get_session_memory(conn, "session-1")
    assert record.usefulness_flag is True


def test_set_usefulness_marks_a_query_not_useful(conn):
    session_memory_id = record_session_query(conn, "session-1", "What is the return policy?", [1])

    set_usefulness(conn, session_memory_id, useful=False)

    (record,) = get_session_memory(conn, "session-1")
    assert record.usefulness_flag is False


def test_get_session_memory_returns_only_matching_session_oldest_first(conn):
    record_session_query(conn, "session-1", "first query", [1])
    record_session_query(conn, "session-2", "other session's query", [9])
    record_session_query(conn, "session-1", "second query", [2])

    records = get_session_memory(conn, "session-1")

    assert [record.query for record in records] == ["first query", "second query"]


def test_get_session_memory_returns_empty_list_for_unknown_session(conn):
    assert get_session_memory(conn, "unknown-session") == []


def test_retrieved_chunk_ids_round_trips_empty_list(conn):
    record_session_query(conn, "session-1", "no matches found", [])

    (record,) = get_session_memory(conn, "session-1")

    assert record.retrieved_chunk_ids == []


def test_created_at_is_recorded(conn):
    record_session_query(conn, "session-1", "What is the return policy?", [1])

    (record,) = get_session_memory(conn, "session-1")

    assert record.created_at is not None


def test_connect_also_creates_shared_ingestion_tables(conn):
    # memory.session.connect() must set up the shared database's
    # documents/chunks tables too, not just session_memory, since all three
    # live in the same SQLite file; see docs/DECISIONS.md ("SQLite Schema
    # For Session Memory Records").
    conn.execute("SELECT * FROM documents")
    conn.execute("SELECT * FROM chunks")
    conn.execute("SELECT * FROM session_memory")
