"""End-to-end ingestion tests using small fixture documents (Phase 2 PR 6).

Exercises the whole Phase 2 chain against one small, fictional fixture per
supported file type (intake -> extraction -> chunking -> SQLite ->
ChromaDB), and asserts the three Phase 2 exit criteria from
docs/PRODUCT_TIMELINE.md directly:

- Supported files ingest successfully.
- Chunk metadata can be queried from SQLite.
- Vector references resolve back to stored chunk metadata.

Each module already has its own focused unit tests (test_ingestion_*.py);
this file only proves the modules compose correctly together, so it stays
deliberately small. There is still no orchestration module wiring
`storage.py` and `vector_store.py` together (see docs/DECISIONS.md,
"ChromaDB Vector Persistence"); each test performs that wiring itself.

Fixture content is small, fictional prose (well under the 200-token merge
threshold), so each document lands as a single chunk, keeping the
assertions simple; see tests/fixtures.py for the shared PDF/DOCX builders.
"""

import uuid

import chromadb
import pytest
from fixtures import build_minimal_docx, build_minimal_pdf

from memQrag.ingestion.chunking import chunk_document
from memQrag.ingestion.contracts import intake_document
from memQrag.ingestion.embeddings import embed_sentences
from memQrag.ingestion.extraction import extract_text
from memQrag.ingestion.storage import (
    connect,
    get_chunks_for_document,
    get_document_by_filename,
    persist_ingested_document,
)
from memQrag.ingestion.vector_store import (
    get_chunk_vector_ids_for_document,
    persist_chunk_vectors,
)

_TXT_FIXTURE = b"The archive room closes for inventory every autumn."
_MARKDOWN_FIXTURE = b"# Storage Policy\nFictional crates rotate stock twice a year."
_DOCX_FIXTURE = build_minimal_docx([("Fictional couriers deliver on Tuesdays.", None)])
_PDF_FIXTURE = build_minimal_pdf(["Fictional lighthouse logs are kept for a decade."])

FIXTURES = pytest.mark.parametrize(
    "filename,content",
    [
        pytest.param("storage-notes.txt", _TXT_FIXTURE, id="txt"),
        pytest.param("storage-policy.md", _MARKDOWN_FIXTURE, id="markdown"),
        pytest.param("courier-schedule.docx", _DOCX_FIXTURE, id="docx"),
        pytest.param("lighthouse-log.pdf", _PDF_FIXTURE, id="pdf"),
    ],
)


@pytest.fixture
def sqlite_conn():
    conn = connect(":memory:")
    yield conn
    conn.close()


@pytest.fixture
def chroma_collection():
    try:
        embed_sentences(["warm up"])
    except Exception as exc:
        pytest.skip(f"Could not load the sentence embedding model: {exc}")
    # chromadb.EphemeralClient() instances share underlying state within a
    # process (Chroma caches the system by settings hash), so each test uses
    # a uniquely named collection to stay isolated from other tests; see
    # tests/test_ingestion_vector_store.py for the same pattern.
    client = chromadb.EphemeralClient()
    return client.get_or_create_collection(f"test-pipeline-{uuid.uuid4().hex}")


@FIXTURES
def test_fixture_document_ingests_successfully(filename, content, sqlite_conn, chroma_collection):
    """Exit criterion: supported files ingest successfully."""
    raw_document = intake_document(filename, content)
    extracted = extract_text(raw_document)
    chunks = chunk_document(extracted, embed=embed_sentences)
    assert len(chunks) >= 1

    document_id, chunk_ids = persist_ingested_document(sqlite_conn, extracted, chunks)
    vector_ids = persist_chunk_vectors(chroma_collection, document_id, chunk_ids, chunks)

    assert len(chunk_ids) == len(chunks)
    assert len(vector_ids) == len(chunks)


@FIXTURES
def test_chunk_metadata_is_queryable_from_sqlite(filename, content, sqlite_conn, chroma_collection):
    """Exit criterion: chunk metadata can be queried from SQLite."""
    raw_document = intake_document(filename, content)
    extracted = extract_text(raw_document)
    chunks = chunk_document(extracted, embed=embed_sentences)
    document_id, chunk_ids = persist_ingested_document(sqlite_conn, extracted, chunks)

    document_record = get_document_by_filename(sqlite_conn, filename)
    chunk_records = get_chunks_for_document(sqlite_conn, document_id)

    assert document_record is not None
    assert document_record.filename == filename
    assert [record.id for record in chunk_records] == chunk_ids
    assert [record.text for record in chunk_records] == [chunk.text for chunk in chunks]


@FIXTURES
def test_vector_references_resolve_back_to_stored_chunk_metadata(
    filename, content, sqlite_conn, chroma_collection
):
    """Exit criterion: vector references resolve back to stored chunk metadata."""
    raw_document = intake_document(filename, content)
    extracted = extract_text(raw_document)
    chunks = chunk_document(extracted, embed=embed_sentences)
    document_id, chunk_ids = persist_ingested_document(sqlite_conn, extracted, chunks)
    persist_chunk_vectors(chroma_collection, document_id, chunk_ids, chunks)

    vector_ids = get_chunk_vector_ids_for_document(chroma_collection, document_id)
    assert sorted(int(vector_id) for vector_id in vector_ids) == sorted(chunk_ids)

    # A vector id (as a retrieval result would return) resolves back to the
    # exact chunk row that was persisted, with no separate mapping table.
    resolved_chunk_id = int(vector_ids[0])
    stored_chunk = next(
        record
        for record in get_chunks_for_document(sqlite_conn, document_id)
        if record.id == resolved_chunk_id
    )
    vector = chroma_collection.get(ids=[str(resolved_chunk_id)], include=["metadatas", "documents"])
    assert vector["documents"][0] == stored_chunk.text
    assert vector["metadatas"][0]["source_document"] == filename
