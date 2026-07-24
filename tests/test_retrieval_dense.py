"""Tests for memQrag.retrieval.dense (ChromaDB dense retrieval, Phase 3 PR 1).

Most tests build the Chroma collection fixture directly with a small
deterministic one-hot "topic" embedding (matching the fake embedder
pattern in tests/test_ingestion_chunking.py) instead of the real
fastembed-backed embedder, keeping ranking assertions exact and the tests
network-free. One integration test at the end uses the real
`embed_sentences` + `memQrag.ingestion.vector_store.persist_chunk_vectors`
to prove the real wiring works end to end; it skips (not fails) if the
embedding model cannot be loaded, matching tests/test_ingestion_pipeline.py.
"""

import uuid

import chromadb
import pytest

from memQrag.ingestion.chunking import Chunk
from memQrag.ingestion.embeddings import embed_sentences
from memQrag.ingestion.vector_store import get_collection, persist_chunk_vectors
from memQrag.retrieval.dense import DENSE_TOP_K, dense_retrieve

_TOPIC_VECTORS = {
    "cat": [1.0, 0.0, 0.0],
    "car": [0.0, 1.0, 0.0],
    "moon": [0.0, 0.0, 1.0],
}


def _seed(collection, topic: str, count: int, document_id: int = 1, start_id: int = 1) -> None:
    ids = [str(start_id + i) for i in range(count)]
    collection.upsert(
        ids=ids,
        embeddings=[_TOPIC_VECTORS[topic] for _ in ids],
        metadatas=[
            {"document_id": document_id, "source_document": "fixture.txt", "token_count": 5}
            for _ in ids
        ],
        documents=[f"{topic} sentence {i}." for i in range(count)],
    )


@pytest.fixture
def collection():
    # chromadb.EphemeralClient() instances share underlying state within a
    # process, so each test uses a uniquely named collection; see
    # tests/test_ingestion_vector_store.py for the same pattern.
    client = chromadb.EphemeralClient()
    return client.get_or_create_collection(
        f"test-dense-{uuid.uuid4().hex}", metadata={"hnsw:space": "cosine"}
    )


def test_dense_retrieve_ranks_exact_topic_match_first(collection, monkeypatch):
    _seed(collection, "cat", count=1, start_id=1)
    _seed(collection, "car", count=1, start_id=2)
    _seed(collection, "moon", count=1, start_id=3)
    monkeypatch.setattr(
        "memQrag.retrieval.dense.embed_sentences", lambda sentences: [_TOPIC_VECTORS["cat"]]
    )

    results = dense_retrieve(collection, "anything about cats")

    # car/moon are equally (orthogonally) dissimilar from the query, so only
    # the top match's position is guaranteed; their relative order is not.
    assert results[0].chunk_id == 1
    assert results[0].score == pytest.approx(1.0)
    assert {result.chunk_id for result in results[1:]} == {2, 3}
    assert all(result.score == pytest.approx(0.0) for result in results[1:])


def test_dense_retrieve_defaults_to_top_20(collection, monkeypatch):
    _seed(collection, "cat", count=25, start_id=1)
    monkeypatch.setattr(
        "memQrag.retrieval.dense.embed_sentences", lambda sentences: [_TOPIC_VECTORS["cat"]]
    )

    results = dense_retrieve(collection, "cats")

    assert len(results) == DENSE_TOP_K


def test_dense_retrieve_respects_custom_top_k(collection, monkeypatch):
    _seed(collection, "cat", count=10, start_id=1)
    monkeypatch.setattr(
        "memQrag.retrieval.dense.embed_sentences", lambda sentences: [_TOPIC_VECTORS["cat"]]
    )

    results = dense_retrieve(collection, "cats", top_k=3)

    assert len(results) == 3


def test_dense_retrieve_returns_fewer_than_top_k_when_collection_is_smaller(
    collection, monkeypatch
):
    _seed(collection, "cat", count=2, start_id=1)
    monkeypatch.setattr(
        "memQrag.retrieval.dense.embed_sentences", lambda sentences: [_TOPIC_VECTORS["cat"]]
    )

    results = dense_retrieve(collection, "cats")

    assert len(results) == 2


def test_dense_retrieve_result_carries_self_contained_metadata(collection, monkeypatch):
    collection.upsert(
        ids=["42"],
        embeddings=[_TOPIC_VECTORS["cat"]],
        metadatas=[
            {
                "document_id": 7,
                "source_document": "handbook.docx",
                "token_count": 12,
                "page_number": 3,
                "section_heading": "Overview",
            }
        ],
        documents=["Chunk with metadata."],
    )
    monkeypatch.setattr(
        "memQrag.retrieval.dense.embed_sentences", lambda sentences: [_TOPIC_VECTORS["cat"]]
    )

    (result,) = dense_retrieve(collection, "cats")

    assert result.chunk_id == 42
    assert result.document_id == 7
    assert result.text == "Chunk with metadata."
    assert result.source_document == "handbook.docx"
    assert result.page_number == 3
    assert result.section_heading == "Overview"


def test_dense_retrieve_defaults_absent_page_number_and_heading_to_none(collection, monkeypatch):
    collection.upsert(
        ids=["1"],
        embeddings=[_TOPIC_VECTORS["cat"]],
        metadatas=[{"document_id": 1, "source_document": "fixture.txt", "token_count": 5}],
        documents=["No structural metadata."],
    )
    monkeypatch.setattr(
        "memQrag.retrieval.dense.embed_sentences", lambda sentences: [_TOPIC_VECTORS["cat"]]
    )

    (result,) = dense_retrieve(collection, "cats")

    assert result.page_number is None
    assert result.section_heading is None


def test_dense_retrieve_rejects_blank_query(collection):
    with pytest.raises(ValueError, match="must not be empty"):
        dense_retrieve(collection, "   ")


def test_dense_retrieve_end_to_end_with_real_embeddings():
    try:
        embed_sentences(["warm up"])
    except Exception as exc:
        pytest.skip(f"Could not load the sentence embedding model: {exc}")

    client = chromadb.EphemeralClient()
    collection = get_collection(client=client)

    lighthouse_chunk = Chunk(
        text="Fictional lighthouse logs are kept for a decade.",
        token_count=8,
        source_document="lighthouse-log.pdf",
        page_number=1,
        section_heading=None,
    )
    market_chunk = Chunk(
        text="Fictional stock markets fell sharply on Tuesday.",
        token_count=8,
        source_document="market-report.txt",
        page_number=None,
        section_heading=None,
    )
    persist_chunk_vectors(
        collection, document_id=1, chunk_ids=[101, 102], chunks=[lighthouse_chunk, market_chunk]
    )

    results = dense_retrieve(collection, "How long are lighthouse logs kept?")

    assert results[0].chunk_id == 101
    assert results[0].source_document == "lighthouse-log.pdf"
    assert -1.0 <= results[0].score <= 1.0
