"""Tests for memQrag.ingestion.storage (SQLite persistence, Phase 2 PR 4).

Uses an in-memory SQLite database (`connect(":memory:")`) so these tests
never touch disk.
"""

from datetime import datetime, timezone

import pytest

from memQrag.ingestion.chunking import Chunk
from memQrag.ingestion.contracts import SupportedFileType
from memQrag.ingestion.extraction import ExtractedDocument
from memQrag.ingestion.storage import (
    connect,
    get_chunks_for_document,
    get_document_by_filename,
    persist_ingested_document,
    replace_chunks,
    save_document,
)


@pytest.fixture
def conn():
    connection = connect(":memory:")
    yield connection
    connection.close()


def _document(
    filename: str = "policy.txt",
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


def _chunk(text: str = "Some chunk text.", **overrides) -> Chunk:
    defaults = {
        "text": text,
        "token_count": len(text.split()),
        "source_document": "policy.txt",
        "page_number": None,
        "section_heading": None,
    }
    defaults.update(overrides)
    return Chunk(**defaults)


def test_connect_creates_documents_and_chunks_tables(conn):
    tables = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    }
    assert {"documents", "chunks"}.issubset(tables)


def test_save_document_inserts_new_row_and_returns_id(conn):
    document_id = save_document(conn, _document("policy.txt"))

    record = get_document_by_filename(conn, "policy.txt")
    assert record is not None
    assert record.id == document_id
    assert record.filename == "policy.txt"
    assert record.file_type == "txt"
    assert isinstance(record.ingested_at, datetime)


def test_save_document_captures_created_and_modified_dates(conn):
    created = datetime(2024, 1, 1, tzinfo=timezone.utc)
    modified = datetime(2024, 6, 1, tzinfo=timezone.utc)
    save_document(conn, _document("dated.txt", created_date=created, last_modified_date=modified))

    record = get_document_by_filename(conn, "dated.txt")
    assert record.created_date == created
    assert record.last_modified_date == modified


def test_save_document_allows_missing_dates(conn):
    save_document(conn, _document("undated.txt"))

    record = get_document_by_filename(conn, "undated.txt")
    assert record.created_date is None
    assert record.last_modified_date is None


def test_save_document_upserts_by_filename_reusing_same_id(conn):
    first_id = save_document(conn, _document("policy.txt", created_date=None))
    second_id = save_document(
        conn, _document("policy.txt", created_date=datetime(2025, 1, 1, tzinfo=timezone.utc))
    )

    assert first_id == second_id
    record = get_document_by_filename(conn, "policy.txt")
    assert record.created_date == datetime(2025, 1, 1, tzinfo=timezone.utc)


def test_get_document_by_filename_returns_none_for_unknown_filename(conn):
    assert get_document_by_filename(conn, "missing.txt") is None


def test_replace_chunks_inserts_chunks_for_document(conn):
    document_id = save_document(conn, _document("policy.txt"))
    chunk_ids = replace_chunks(conn, document_id, [_chunk("First chunk."), _chunk("Second chunk.")])

    assert len(chunk_ids) == 2
    records = get_chunks_for_document(conn, document_id)
    assert [r.text for r in records] == ["First chunk.", "Second chunk."]
    assert all(r.document_id == document_id for r in records)


def test_replace_chunks_removes_previous_chunks_for_same_document(conn):
    document_id = save_document(conn, _document("policy.txt"))
    replace_chunks(conn, document_id, [_chunk("Old chunk one."), _chunk("Old chunk two.")])

    replace_chunks(conn, document_id, [_chunk("New chunk.")])

    records = get_chunks_for_document(conn, document_id)
    assert [r.text for r in records] == ["New chunk."]


def test_replace_chunks_preserves_page_number_and_section_heading(conn):
    document_id = save_document(conn, _document("policy.txt"))
    replace_chunks(
        conn,
        document_id,
        [_chunk("Chunk with metadata.", page_number=3, section_heading="Overview")],
    )

    record = get_chunks_for_document(conn, document_id)[0]
    assert record.page_number == 3
    assert record.section_heading == "Overview"


def test_get_chunks_for_document_returns_empty_list_when_none_exist(conn):
    document_id = save_document(conn, _document("policy.txt"))
    assert get_chunks_for_document(conn, document_id) == []


def test_persist_ingested_document_saves_document_and_chunks_together(conn):
    document = _document("handbook.txt")
    chunks = [_chunk("Alpha chunk."), _chunk("Beta chunk.")]

    document_id, chunk_ids = persist_ingested_document(conn, document, chunks)

    assert get_document_by_filename(conn, "handbook.txt").id == document_id
    assert len(chunk_ids) == 2
    stored = get_chunks_for_document(conn, document_id)
    assert [r.text for r in stored] == ["Alpha chunk.", "Beta chunk."]


def test_persist_ingested_document_reingestion_replaces_chunks(conn):
    document = _document("handbook.txt")
    persist_ingested_document(conn, document, [_chunk("Old content.")])

    document_id, _ = persist_ingested_document(conn, document, [_chunk("Updated content.")])

    stored = get_chunks_for_document(conn, document_id)
    assert [r.text for r in stored] == ["Updated content."]


def test_deleting_document_cascades_to_delete_its_chunks(conn):
    document_id = save_document(conn, _document("policy.txt"))
    replace_chunks(conn, document_id, [_chunk("Chunk one."), _chunk("Chunk two.")])

    conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
    conn.commit()

    assert get_chunks_for_document(conn, document_id) == []
