"""Tests for memQrag.retrieval.sparse (BM25 sparse retrieval, Phase 3 PR 2).

Builds the Chroma collection fixture directly with small, distinct-vocabulary
fictional chunk text, so BM25 ranking is easy to reason about exactly. No
embeddings are needed here (BM25 is lexical, not vector-based), so these
tests are fast and fully network-free, unlike the embedding-dependent
integration test in tests/test_retrieval_dense.py.
"""

import uuid

import chromadb
import pytest

from memQrag.retrieval.sparse import SPARSE_TOP_K, sparse_retrieve


@pytest.fixture
def collection():
    # chromadb.EphemeralClient() instances share underlying state within a
    # process, so each test uses a uniquely named collection; see
    # tests/test_ingestion_vector_store.py for the same pattern.
    client = chromadb.EphemeralClient()
    return client.get_or_create_collection(f"test-sparse-{uuid.uuid4().hex}")


def _seed(collection, rows: list[tuple[str, str, dict]]) -> None:
    ids, documents, metadatas = [], [], []
    for chunk_id, text, extra_metadata in rows:
        ids.append(chunk_id)
        documents.append(text)
        metadatas.append({"document_id": 1, "source_document": "fixture.txt", **extra_metadata})
    # BM25 does not use vectors, but Chroma requires one per upserted row.
    collection.upsert(
        ids=ids,
        embeddings=[[0.0, 0.0] for _ in ids],
        documents=documents,
        metadatas=metadatas,
    )


def test_sparse_retrieve_ranks_by_lexical_overlap(collection):
    _seed(
        collection,
        [
            ("1", "Fictional lighthouse logs are kept for a decade.", {}),
            ("2", "Lighthouse keepers rotate every lighthouse season.", {}),
            ("3", "Fictional stock markets fell sharply on Tuesday.", {}),
        ],
    )

    results = sparse_retrieve(collection, "lighthouse logs")

    # Doc 1 matches both query terms ("lighthouse" and "logs"); doc 2 only
    # matches "lighthouse" (even though it repeats it); doc 3 matches
    # neither and must be excluded entirely.
    assert [result.chunk_id for result in results] == [1, 2]


def test_sparse_retrieve_excludes_chunks_with_no_query_term_overlap(collection):
    _seed(
        collection,
        [
            ("1", "Fictional couriers deliver packages on Tuesdays.", {}),
            ("2", "Fictional stock markets fell sharply on Tuesday.", {}),
        ],
    )

    results = sparse_retrieve(collection, "lighthouse")

    assert results == []


def test_sparse_retrieve_returns_empty_list_for_empty_collection(collection):
    assert sparse_retrieve(collection, "anything") == []


def test_sparse_retrieve_rejects_blank_query(collection):
    with pytest.raises(ValueError, match="must not be empty"):
        sparse_retrieve(collection, "   ")


def test_sparse_retrieve_defaults_to_top_20(collection):
    _seed(
        collection,
        [(str(i), f"Fictional lighthouse log entry number {i}.", {}) for i in range(25)],
    )

    results = sparse_retrieve(collection, "lighthouse log")

    assert len(results) == SPARSE_TOP_K


def test_sparse_retrieve_respects_custom_top_k(collection):
    _seed(
        collection,
        [(str(i), f"Fictional lighthouse log entry number {i}.", {}) for i in range(10)],
    )

    results = sparse_retrieve(collection, "lighthouse log", top_k=3)

    assert len(results) == 3


def test_sparse_retrieve_result_carries_self_contained_metadata(collection):
    _seed(
        collection,
        [
            (
                "42",
                "Fictional handbook overview about lighthouse maintenance.",
                {"page_number": 3, "section_heading": "Overview"},
            )
        ],
    )

    (result,) = sparse_retrieve(collection, "lighthouse maintenance")

    assert result.chunk_id == 42
    assert result.document_id == 1
    assert result.source_document == "fixture.txt"
    assert result.page_number == 3
    assert result.section_heading == "Overview"
    assert isinstance(result.score, float)


def test_sparse_retrieve_defaults_absent_page_number_and_heading_to_none(collection):
    _seed(collection, [("1", "Fictional lighthouse maintenance notes.", {})])

    (result,) = sparse_retrieve(collection, "lighthouse maintenance")

    assert result.page_number is None
    assert result.section_heading is None


def test_sparse_retrieve_includes_matches_with_negative_bm25_score(collection):
    # BM25's IDF term goes negative for a token appearing in every document
    # in the corpus (uninformative token). With a single-document corpus,
    # every token in that document appears in 100% of the corpus, so a
    # perfectly overlapping query still yields a negative raw score; the
    # chunk must still be returned, since score > 0 is not the overlap test.
    _seed(collection, [("1", "Fictional lighthouse maintenance notes.", {})])

    (result,) = sparse_retrieve(collection, "lighthouse maintenance")

    assert result.chunk_id == 1
    assert result.score < 0


def test_sparse_retrieve_is_case_insensitive(collection):
    _seed(collection, [("1", "LIGHTHOUSE logs are kept for a decade.", {})])

    results = sparse_retrieve(collection, "lighthouse")

    assert len(results) == 1
