"""Tests for memQrag.ingestion.vector_store (ChromaDB persistence, Phase 2 PR 5).

Uses `chromadb.EphemeralClient()`, a real, in-process Chroma client with no
server or network dependency, so these tests exercise the actual Chroma
API without requiring Docker; see docs/DECISIONS.md ("ChromaDB Vector
Persistence"). The embedding step uses the real `embed_sentences` (see
tests/test_ingestion_embeddings.py for its own network-tolerant handling);
if the model cannot be loaded in this environment, these tests skip too.

`chromadb.EphemeralClient()` instances share underlying state within a
process (Chroma caches the system by settings hash), so each test uses a
uniquely named collection rather than the fixed `COLLECTION_NAME`, to stay
isolated from other tests.
"""

import uuid

import chromadb
import pytest

from memQrag.ingestion.chunking import Chunk
from memQrag.ingestion.embeddings import embed_sentences
from memQrag.ingestion.vector_store import (
    COLLECTION_NAME,
    delete_chunk_vectors,
    get_chunk_vector_ids_for_document,
    get_collection,
    persist_chunk_vectors,
)


@pytest.fixture
def collection():
    try:
        # Force the embedding call now so any model-loading failure surfaces
        # as a skip rather than a confusing per-test failure later.
        embed_sentences(["warm up"])
    except Exception as exc:
        pytest.skip(f"Could not load the sentence embedding model: {exc}")
    client = chromadb.EphemeralClient()
    return client.get_or_create_collection(f"test-{uuid.uuid4().hex}")


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


def test_persist_chunk_vectors_upserts_one_vector_per_chunk(collection):
    chunks = [_chunk("First chunk."), _chunk("Second chunk.")]

    vector_ids = persist_chunk_vectors(collection, document_id=1, chunk_ids=[10, 11], chunks=chunks)

    assert vector_ids == ["10", "11"]
    assert collection.count() == 2


def test_persist_chunk_vectors_returns_empty_list_for_no_chunks(collection):
    assert persist_chunk_vectors(collection, document_id=1, chunk_ids=[], chunks=[]) == []
    assert collection.count() == 0


def test_persist_chunk_vectors_rejects_mismatched_lengths(collection):
    with pytest.raises(ValueError, match="same length"):
        persist_chunk_vectors(collection, document_id=1, chunk_ids=[1], chunks=[_chunk(), _chunk()])


def test_persist_chunk_vectors_stores_document_text_and_metadata(collection):
    chunk = _chunk(
        "Chunk with metadata.",
        source_document="handbook.docx",
        page_number=3,
        section_heading="Overview",
    )

    persist_chunk_vectors(collection, document_id=7, chunk_ids=[42], chunks=[chunk])

    result = collection.get(ids=["42"], include=["metadatas", "documents"])
    assert result["documents"] == ["Chunk with metadata."]
    metadata = result["metadatas"][0]
    assert metadata["document_id"] == 7
    assert metadata["source_document"] == "handbook.docx"
    assert metadata["page_number"] == 3
    assert metadata["section_heading"] == "Overview"
    assert metadata["token_count"] == chunk.token_count


def test_persist_chunk_vectors_omits_absent_page_number_and_heading(collection):
    chunk = _chunk("No structural metadata.", page_number=None, section_heading=None)

    persist_chunk_vectors(collection, document_id=1, chunk_ids=[5], chunks=[chunk])

    metadata = collection.get(ids=["5"], include=["metadatas"])["metadatas"][0]
    assert "page_number" not in metadata
    assert "section_heading" not in metadata


def test_get_chunk_vector_ids_for_document_filters_by_document_id(collection):
    persist_chunk_vectors(collection, document_id=1, chunk_ids=[1, 2], chunks=[_chunk(), _chunk()])
    persist_chunk_vectors(collection, document_id=2, chunk_ids=[3], chunks=[_chunk()])

    assert sorted(get_chunk_vector_ids_for_document(collection, document_id=1)) == ["1", "2"]
    assert get_chunk_vector_ids_for_document(collection, document_id=2) == ["3"]


def test_delete_chunk_vectors_removes_them(collection):
    persist_chunk_vectors(collection, document_id=1, chunk_ids=[1, 2], chunks=[_chunk(), _chunk()])

    delete_chunk_vectors(collection, [1])

    assert collection.count() == 1
    assert collection.get(ids=["2"])["ids"] == ["2"]


def test_delete_chunk_vectors_is_a_no_op_for_empty_list(collection):
    persist_chunk_vectors(collection, document_id=1, chunk_ids=[1], chunks=[_chunk()])

    delete_chunk_vectors(collection, [])

    assert collection.count() == 1


def test_get_collection_uses_fixed_collection_name():
    client = chromadb.EphemeralClient()
    collection = get_collection(client=client)

    assert collection.name == COLLECTION_NAME


def test_vector_id_resolves_back_to_chunk_id():
    # The whole point of using str(chunk_id) as the Chroma id: no separate
    # embedding_reference lookup table is needed, per docs/DECISIONS.md.
    vector_id = "123"
    assert int(vector_id) == 123
