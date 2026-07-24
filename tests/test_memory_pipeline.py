"""End-to-end memory and staleness tests (Phase 4 PR 6).

Stitches Phase 4's modules together against one shared SQLite fixture and
asserts the three Phase 4 exit criteria from docs/PRODUCT_TIMELINE.md
directly:

- Similar queries can boost previously successful documents.
- Stale frequently retrieved documents are surfaced for review.
- Old low-value memory has reduced retrieval influence.

Each module already has its own focused unit tests
(test_memory_session/long_term/boost/decay/staleness.py); this file only
proves they compose correctly together. Hand-picked query embeddings keep
the boost/decay path free of model downloads; the session -> long-term
promotion path uses the real embedder and skips (not fails) if it can't
load, matching tests/test_memory_boost.py. See docs/DECISIONS.md
("End-To-End Memory And Staleness Fixture Tests").
"""

from datetime import UTC, datetime, timedelta

import pytest

from memQrag.ingestion.contracts import SupportedFileType
from memQrag.ingestion.embeddings import embed_sentences
from memQrag.ingestion.extraction import ExtractedDocument
from memQrag.ingestion.storage import (
    DocumentStalenessStatus,
    get_document_by_filename,
    save_document,
)
from memQrag.memory.boost import (
    BOOST_AMOUNT,
    apply_memory_boost,
    find_similar_successful_memory,
    promote_session_memory_to_long_term,
    remember_query_outcome,
)
from memQrag.memory.decay import DECAY_FACTOR, apply_memory_decay
from memQrag.memory.long_term import connect, get_long_term_memory_by_id, update_long_term_memory
from memQrag.memory.session import record_session_query, set_usefulness
from memQrag.memory.staleness import MIN_RETRIEVAL_COUNT, detect_stale_documents
from memQrag.retrieval.fusion import FusedRetrievalResult

_NOW = datetime(2026, 7, 24, tzinfo=UTC)
_RETURN_POLICY_EMBEDDING = [1.0, 0.0, 0.0]
_SIMILAR_RETURN_POLICY_EMBEDDING = [0.99, 0.05, 0.0]


@pytest.fixture
def conn():
    connection = connect(":memory:")
    yield connection
    connection.close()


def _document(
    filename: str,
    *,
    last_modified_date: datetime | None = None,
) -> ExtractedDocument:
    return ExtractedDocument(
        source_document=filename,
        file_type=SupportedFileType.TXT,
        created_date=None,
        last_modified_date=last_modified_date,
        segments=[],
    )


def _ingest(conn, filename: str, *, last_modified_date: datetime | None = None) -> tuple[int, int]:
    document_id = save_document(conn, _document(filename, last_modified_date=last_modified_date))
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


def _fused_result(
    chunk_id: int,
    document_id: int,
    rrf_score: float,
    source_document: str,
) -> FusedRetrievalResult:
    return FusedRetrievalResult(
        chunk_id=chunk_id,
        document_id=document_id,
        text=f"chunk {chunk_id} text",
        source_document=source_document,
        page_number=1,
        section_heading=None,
        dense_score=0.8,
        sparse_rank=1,
        fused_rank=chunk_id,
        rrf_score=rrf_score,
    )


def test_similar_queries_boost_previously_successful_documents(conn):
    """Exit criterion: Similar queries can boost previously successful documents."""
    return_policy_id, return_chunk_id = _ingest(conn, "return-policy.txt")
    shipping_id, shipping_chunk_id = _ingest(conn, "shipping.txt")

    # Past useful retrieval of the return-policy document becomes long-term memory
    # (session -> promote path is covered separately below with the real embedder).
    remember_query_outcome(
        conn,
        "What is the return policy?",
        [return_policy_id],
        was_successful=True,
        query_embedding=_RETURN_POLICY_EMBEDDING,
    )

    # A later similar query's fused ranking currently prefers shipping over returns.
    fused = [
        _fused_result(shipping_chunk_id, shipping_id, 0.05, "shipping.txt"),
        _fused_result(return_chunk_id, return_policy_id, 0.03, "return-policy.txt"),
    ]
    similar_memory = find_similar_successful_memory(
        conn,
        "What's your return policy?",
        query_embedding=_SIMILAR_RETURN_POLICY_EMBEDDING,
    )

    boosted = apply_memory_boost(fused, similar_memory)

    assert similar_memory is not None
    assert similar_memory.best_document_ids == [return_policy_id]
    assert [result.document_id for result in boosted] == [return_policy_id, shipping_id]
    assert boosted[0].applied_memory_boost == pytest.approx(BOOST_AMOUNT)
    assert boosted[0].source_document == "return-policy.txt"


def test_old_low_value_memory_has_reduced_retrieval_influence(conn):
    """Exit criterion: Old low-value memory has reduced retrieval influence."""
    return_policy_id, return_chunk_id = _ingest(conn, "return-policy.txt")
    shipping_id, shipping_chunk_id = _ingest(conn, "shipping.txt")

    # Mixed outcomes leave hit_rate at 1/3 — below both the decay threshold and
    # find_similar_successful_memory's default min_hit_rate (both 0.5).
    memory_id = remember_query_outcome(
        conn,
        "What is the return policy?",
        [return_policy_id],
        was_successful=True,
        query_embedding=_RETURN_POLICY_EMBEDDING,
    )
    remember_query_outcome(
        conn,
        "What is the return policy?",
        [return_policy_id],
        was_successful=False,
        query_embedding=_RETURN_POLICY_EMBEDDING,
    )
    remember_query_outcome(
        conn,
        "What is the return policy?",
        [return_policy_id],
        was_successful=False,
        query_embedding=_RETURN_POLICY_EMBEDDING,
    )
    update_long_term_memory(conn, memory_id, last_used=_NOW - timedelta(days=60))

    changed_ids = apply_memory_decay(conn, now=_NOW)
    assert changed_ids == [memory_id]
    decayed = get_long_term_memory_by_id(conn, memory_id)
    assert decayed.decay_weight == pytest.approx(DECAY_FACTOR**2)

    fused = [
        _fused_result(shipping_chunk_id, shipping_id, 0.05, "shipping.txt"),
        _fused_result(return_chunk_id, return_policy_id, 0.03, "return-policy.txt"),
    ]

    # Default pipeline: low-value memory is not selected for boosting at all.
    assert (
        find_similar_successful_memory(
            conn,
            "What's your return policy?",
            query_embedding=_SIMILAR_RETURN_POLICY_EMBEDDING,
        )
        is None
    )
    assert all(
        result.applied_memory_boost == 0.0
        for result in apply_memory_boost(fused, similar_memory=None)
    )

    # If the decayed record is applied anyway, boost is scaled by decay_weight
    # (the wiring apply_memory_boost uses — see memory-decay decision).
    scaled = apply_memory_boost(fused, decayed)
    assert scaled[0].document_id == shipping_id
    assert scaled[1].applied_memory_boost == pytest.approx(BOOST_AMOUNT * (DECAY_FACTOR**2))
    assert scaled[1].rrf_score < scaled[0].rrf_score


def test_stale_frequently_retrieved_documents_are_surfaced_for_review(conn):
    """Exit criterion: Stale frequently retrieved documents are surfaced for review."""
    stale_id, stale_chunk_id = _ingest(
        conn, "old-policy.txt", last_modified_date=_NOW - timedelta(days=200)
    )
    fresh_id, fresh_chunk_id = _ingest(
        conn, "new-policy.txt", last_modified_date=_NOW - timedelta(days=1)
    )

    for i in range(MIN_RETRIEVAL_COUNT):
        record_session_query(conn, f"session-{i}", "policy question", [stale_chunk_id])
        record_session_query(conn, f"session-fresh-{i}", "policy question", [fresh_chunk_id])

    stale_ids = detect_stale_documents(conn, now=_NOW)

    assert stale_ids == [stale_id]
    assert (
        get_document_by_filename(conn, "old-policy.txt").staleness_status
        == DocumentStalenessStatus.STALE
    )
    assert (
        get_document_by_filename(conn, "new-policy.txt").staleness_status
        == DocumentStalenessStatus.FRESH
    )
    # Staleness is a review signal, not a retrieval filter — both docs remain readable.
    assert get_document_by_filename(conn, "old-policy.txt").id == stale_id
    assert fresh_id is not None


def test_session_feedback_promotes_into_long_term_then_boosts(conn):
    """Composition check: session -> usefulness -> promote -> find -> boost."""
    try:
        embed_sentences(["warm up"])
    except Exception as exc:
        pytest.skip(f"Could not load the sentence embedding model: {exc}")

    return_policy_id, return_chunk_id = _ingest(conn, "return-policy.txt")
    shipping_id, shipping_chunk_id = _ingest(conn, "shipping.txt")

    session_memory_id = record_session_query(
        conn, "session-1", "What is the return policy?", [return_chunk_id]
    )
    set_usefulness(conn, session_memory_id, useful=True)
    promoted_ids = promote_session_memory_to_long_term(conn, "session-1")

    assert len(promoted_ids) == 1
    record = get_long_term_memory_by_id(conn, promoted_ids[0])
    assert record.best_document_ids == [return_policy_id]
    assert record.success_count == 1

    similar_memory = find_similar_successful_memory(conn, "What is the return policy?")
    fused = [
        _fused_result(shipping_chunk_id, shipping_id, 0.05, "shipping.txt"),
        _fused_result(return_chunk_id, return_policy_id, 0.03, "return-policy.txt"),
    ]
    boosted = apply_memory_boost(fused, similar_memory)

    assert similar_memory is not None
    assert [result.document_id for result in boosted] == [return_policy_id, shipping_id]
