"""Tests for memQrag.memory.staleness (staleness detection, Phase 4 PR 5).

Uses hand-picked `last_modified_date`/session_memory rows (via
`connect(":memory:")`) rather than waiting on real time, so these tests
are deterministic and never touch the real clock except through an
explicit `now=` argument.
"""

from datetime import UTC, datetime, timedelta

import pytest

from memQrag.ingestion.contracts import SupportedFileType
from memQrag.ingestion.extraction import ExtractedDocument
from memQrag.ingestion.storage import (
    DocumentStalenessStatus,
    get_document_by_filename,
    save_document,
)
from memQrag.memory.session import record_session_query
from memQrag.memory.staleness import (
    MIN_RETRIEVAL_COUNT,
    count_document_retrievals,
    detect_stale_documents,
    effective_document_date,
    is_stale,
)

_NOW = datetime(2026, 7, 24, tzinfo=UTC)


@pytest.fixture
def conn():
    from memQrag.memory.session import connect

    connection = connect(":memory:")
    yield connection
    connection.close()


def _document(
    filename: str,
    created_date: datetime | None = None,
    last_modified_date: datetime | None = None,
) -> ExtractedDocument:
    return ExtractedDocument(
        source_document=filename,
        file_type=SupportedFileType.TXT,
        created_date=created_date,
        last_modified_date=last_modified_date,
        segments=[],
    )


def _ingest(conn, filename, **date_kwargs):
    document_id = save_document(conn, _document(filename, **date_kwargs))
    conn.execute(
        "INSERT INTO chunks (document_id, page_number, section_heading, text, token_count) "
        "VALUES (?, NULL, NULL, 'text', 1)",
        (document_id,),
    )
    conn.commit()
    chunk_id = conn.execute(
        "SELECT id FROM chunks WHERE document_id = ?", (document_id,)
    ).fetchone()["id"]
    return document_id, chunk_id


def _retrieve(conn, chunk_id, times: int):
    for i in range(times):
        record_session_query(conn, f"session-{i}", "some query", [chunk_id])


# -- effective_document_date -----------------------------------------------


def test_effective_document_date_prefers_last_modified_date(conn):
    document_id, _ = _ingest(
        conn,
        "policy.txt",
        created_date=datetime(2020, 1, 1, tzinfo=UTC),
        last_modified_date=datetime(2024, 1, 1, tzinfo=UTC),
    )

    document = get_document_by_filename(conn, "policy.txt")
    assert effective_document_date(document) == datetime(2024, 1, 1, tzinfo=UTC)


def test_effective_document_date_falls_back_to_created_date(conn):
    _ingest(conn, "policy.txt", created_date=datetime(2020, 1, 1, tzinfo=UTC))

    document = get_document_by_filename(conn, "policy.txt")
    assert effective_document_date(document) == datetime(2020, 1, 1, tzinfo=UTC)


def test_effective_document_date_falls_back_to_ingested_at(conn):
    _ingest(conn, "policy.txt")

    document = get_document_by_filename(conn, "policy.txt")
    assert effective_document_date(document) == document.ingested_at


# -- count_document_retrievals ----------------------------------------------


def test_count_document_retrievals_counts_across_every_session(conn):
    document_id, chunk_id = _ingest(conn, "policy.txt")
    _retrieve(conn, chunk_id, times=3)

    assert count_document_retrievals(conn, document_id) == 3


def test_count_document_retrievals_is_zero_when_never_retrieved(conn):
    document_id, _ = _ingest(conn, "policy.txt")

    assert count_document_retrievals(conn, document_id) == 0


def test_count_document_retrievals_counts_a_query_once_even_with_repeated_chunks(conn):
    document_id, chunk_id = _ingest(conn, "policy.txt")
    record_session_query(conn, "session-1", "query", [chunk_id, chunk_id])

    assert count_document_retrievals(conn, document_id) == 1


# -- is_stale -----------------------------------------------------------------


def test_is_stale_false_for_recent_frequently_retrieved_document(conn):
    document_id, chunk_id = _ingest(conn, "policy.txt", last_modified_date=_NOW - timedelta(days=1))
    _retrieve(conn, chunk_id, times=MIN_RETRIEVAL_COUNT)

    document = get_document_by_filename(conn, "policy.txt")
    assert is_stale(conn, document, now=_NOW) is False


def test_is_stale_false_for_old_rarely_retrieved_document(conn):
    document_id, chunk_id = _ingest(
        conn, "policy.txt", last_modified_date=_NOW - timedelta(days=200)
    )
    _retrieve(conn, chunk_id, times=1)

    document = get_document_by_filename(conn, "policy.txt")
    assert is_stale(conn, document, now=_NOW) is False


def test_is_stale_true_for_old_frequently_retrieved_document(conn):
    document_id, chunk_id = _ingest(
        conn, "policy.txt", last_modified_date=_NOW - timedelta(days=200)
    )
    _retrieve(conn, chunk_id, times=MIN_RETRIEVAL_COUNT)

    document = get_document_by_filename(conn, "policy.txt")
    assert is_stale(conn, document, now=_NOW) is True


def test_is_stale_true_exactly_at_the_age_threshold(conn):
    document_id, chunk_id = _ingest(
        conn, "policy.txt", last_modified_date=_NOW - timedelta(days=90)
    )
    _retrieve(conn, chunk_id, times=MIN_RETRIEVAL_COUNT)

    document = get_document_by_filename(conn, "policy.txt")
    assert is_stale(conn, document, now=_NOW) is True


def test_is_stale_respects_custom_thresholds(conn):
    document_id, chunk_id = _ingest(
        conn, "policy.txt", last_modified_date=_NOW - timedelta(days=10)
    )
    _retrieve(conn, chunk_id, times=2)

    document = get_document_by_filename(conn, "policy.txt")
    assert is_stale(conn, document, now=_NOW, age_days=5, min_retrieval_count=2) is True


# -- detect_stale_documents ---------------------------------------------------


def test_detect_stale_documents_flags_qualifying_documents(conn):
    stale_id, stale_chunk_id = _ingest(
        conn, "old.txt", last_modified_date=_NOW - timedelta(days=200)
    )
    _retrieve(conn, stale_chunk_id, times=MIN_RETRIEVAL_COUNT)
    fresh_id, fresh_chunk_id = _ingest(conn, "new.txt", last_modified_date=_NOW - timedelta(days=1))
    _retrieve(conn, fresh_chunk_id, times=MIN_RETRIEVAL_COUNT)

    stale_ids = detect_stale_documents(conn, now=_NOW)

    assert stale_ids == [stale_id]
    assert (
        get_document_by_filename(conn, "old.txt").staleness_status == DocumentStalenessStatus.STALE
    )
    assert (
        get_document_by_filename(conn, "new.txt").staleness_status == DocumentStalenessStatus.FRESH
    )


def test_detect_stale_documents_reverts_a_document_that_no_longer_qualifies(conn):
    document_id, chunk_id = _ingest(
        conn, "policy.txt", last_modified_date=_NOW - timedelta(days=200)
    )
    _retrieve(conn, chunk_id, times=MIN_RETRIEVAL_COUNT)
    detect_stale_documents(conn, now=_NOW)
    assert (
        get_document_by_filename(conn, "policy.txt").staleness_status
        == DocumentStalenessStatus.STALE
    )

    # Re-ingesting refreshes last_modified_date and resets staleness_status
    # to FRESH already (memQrag.ingestion.storage.save_document()); a
    # later sweep must not re-flag it from stale session_memory history.
    save_document(conn, _document("policy.txt", last_modified_date=_NOW))

    stale_ids = detect_stale_documents(conn, now=_NOW)

    assert stale_ids == []
    assert (
        get_document_by_filename(conn, "policy.txt").staleness_status
        == DocumentStalenessStatus.FRESH
    )


def test_detect_stale_documents_returns_empty_list_when_no_documents_ingested(conn):
    assert detect_stale_documents(conn, now=_NOW) == []
