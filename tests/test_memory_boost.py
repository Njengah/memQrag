"""Tests for memQrag.memory.boost (memory-informed retrieval boosts, Phase 4 PR 3).

`find_similar_successful_memory()` and `remember_query_outcome()` always
pass an explicit `query_embedding=` so these tests never call the real
`embed_sentences()` (no network/model dependency) — see
tests/test_memory_long_term.py for the same pattern. `apply_memory_boost()`
never touches embeddings at all, since it operates purely on already-fused
results and an already-resolved `LongTermMemoryRecord`.
"""

import pytest

from memQrag.ingestion.embeddings import embed_sentences
from memQrag.memory.boost import (
    BOOST_AMOUNT,
    apply_memory_boost,
    find_similar_successful_memory,
    promote_session_memory_to_long_term,
    remember_query_outcome,
)
from memQrag.memory.long_term import connect as connect_long_term
from memQrag.memory.long_term import (
    get_all_long_term_memory,
    get_long_term_memory_by_id,
    update_long_term_memory,
)
from memQrag.memory.session import record_session_query, set_usefulness
from memQrag.retrieval.fusion import FusedRetrievalResult

_RETURN_POLICY_EMBEDDING = [1.0, 0.0, 0.0]
_SHIPPING_EMBEDDING = [0.0, 1.0, 0.0]
_SIMILAR_RETURN_POLICY_EMBEDDING = [0.99, 0.05, 0.0]


@pytest.fixture
def conn():
    connection = connect_long_term(":memory:")
    yield connection
    connection.close()


def _fused_result(chunk_id: int, document_id: int, rrf_score: float) -> FusedRetrievalResult:
    return FusedRetrievalResult(
        chunk_id=chunk_id,
        document_id=document_id,
        text=f"chunk {chunk_id} text",
        source_document="policy.pdf",
        page_number=1,
        section_heading=None,
        dense_score=0.8,
        sparse_rank=1,
        fused_rank=chunk_id,
        rrf_score=rrf_score,
    )


# -- remember_query_outcome ---------------------------------------------------


def test_remember_query_outcome_creates_a_new_record_for_a_novel_query(conn):
    long_term_memory_id = remember_query_outcome(
        conn,
        "What is the return policy?",
        [1],
        was_successful=True,
        query_embedding=_RETURN_POLICY_EMBEDDING,
    )

    record = get_long_term_memory_by_id(conn, long_term_memory_id)
    assert record.success_count == 1
    assert record.match_count == 1
    assert record.hit_rate == pytest.approx(1.0)


def test_remember_query_outcome_records_a_failure_with_zero_hit_rate(conn):
    long_term_memory_id = remember_query_outcome(
        conn,
        "What is the return policy?",
        [1],
        was_successful=False,
        query_embedding=_RETURN_POLICY_EMBEDDING,
    )

    record = get_long_term_memory_by_id(conn, long_term_memory_id)
    assert record.success_count == 0
    assert record.match_count == 1
    assert record.hit_rate == pytest.approx(0.0)


def test_remember_query_outcome_reinforces_a_near_duplicate_query_instead_of_duplicating(conn):
    first_id = remember_query_outcome(
        conn,
        "What is the return policy?",
        [1],
        was_successful=True,
        query_embedding=_RETURN_POLICY_EMBEDDING,
    )

    second_id = remember_query_outcome(
        conn,
        "What's your return policy?",
        [1],
        was_successful=True,
        query_embedding=_SIMILAR_RETURN_POLICY_EMBEDDING,
    )

    assert second_id == first_id
    assert len(get_all_long_term_memory(conn)) == 1
    record = get_long_term_memory_by_id(conn, first_id)
    assert record.match_count == 2
    assert record.success_count == 2
    assert record.hit_rate == pytest.approx(1.0)


def test_remember_query_outcome_averages_hit_rate_across_mixed_outcomes(conn):
    first_id = remember_query_outcome(
        conn,
        "What is the return policy?",
        [1],
        was_successful=True,
        query_embedding=_RETURN_POLICY_EMBEDDING,
    )
    remember_query_outcome(
        conn,
        "What is the return policy?",
        [1],
        was_successful=False,
        query_embedding=_RETURN_POLICY_EMBEDDING,
    )

    record = get_long_term_memory_by_id(conn, first_id)
    assert record.match_count == 2
    assert record.success_count == 1
    assert record.hit_rate == pytest.approx(0.5)


def test_remember_query_outcome_does_not_merge_dissimilar_queries(conn):
    first_id = remember_query_outcome(
        conn,
        "What is the return policy?",
        [1],
        was_successful=True,
        query_embedding=_RETURN_POLICY_EMBEDDING,
    )

    second_id = remember_query_outcome(
        conn,
        "How long does shipping take?",
        [2],
        was_successful=True,
        query_embedding=_SHIPPING_EMBEDDING,
    )

    assert second_id != first_id
    assert len(get_all_long_term_memory(conn)) == 2


def test_remember_query_outcome_rejects_blank_query(conn):
    with pytest.raises(ValueError, match="empty"):
        remember_query_outcome(conn, "   ", [1], was_successful=True, query_embedding=[0.0])


# -- find_similar_successful_memory ------------------------------------------


def test_find_similar_successful_memory_returns_none_when_memory_is_empty(conn):
    result = find_similar_successful_memory(
        conn, "What is the return policy?", query_embedding=_RETURN_POLICY_EMBEDDING
    )

    assert result is None


def test_find_similar_successful_memory_returns_none_below_similarity_threshold(conn):
    remember_query_outcome(
        conn,
        "How long does shipping take?",
        [2],
        was_successful=True,
        query_embedding=_SHIPPING_EMBEDDING,
    )

    result = find_similar_successful_memory(
        conn, "What is the return policy?", query_embedding=_RETURN_POLICY_EMBEDDING
    )

    assert result is None


def test_find_similar_successful_memory_returns_none_when_hit_rate_too_low(conn):
    remember_query_outcome(
        conn,
        "What is the return policy?",
        [1],
        was_successful=False,
        query_embedding=_RETURN_POLICY_EMBEDDING,
    )

    result = find_similar_successful_memory(
        conn, "What is the return policy?", query_embedding=_RETURN_POLICY_EMBEDDING
    )

    assert result is None


def test_find_similar_successful_memory_returns_a_matching_successful_record(conn):
    remember_query_outcome(
        conn,
        "What is the return policy?",
        [1],
        was_successful=True,
        query_embedding=_RETURN_POLICY_EMBEDDING,
    )

    result = find_similar_successful_memory(
        conn, "What's your return policy?", query_embedding=_SIMILAR_RETURN_POLICY_EMBEDDING
    )

    assert result is not None
    assert result.best_document_ids == [1]


def test_find_similar_successful_memory_rejects_blank_query(conn):
    with pytest.raises(ValueError, match="empty"):
        find_similar_successful_memory(conn, "  ", query_embedding=[0.0])


# -- apply_memory_boost -------------------------------------------------------


def test_apply_memory_boost_with_no_similar_memory_preserves_order_and_scores():
    fused = [
        _fused_result(1, document_id=10, rrf_score=0.05),
        _fused_result(2, document_id=20, rrf_score=0.03),
    ]

    boosted = apply_memory_boost(fused, similar_memory=None)

    assert [result.chunk_id for result in boosted] == [1, 2]
    assert [result.rrf_score for result in boosted] == pytest.approx([0.05, 0.03])
    assert all(result.applied_memory_boost == 0.0 for result in boosted)


def test_apply_memory_boost_boosts_matching_document_and_reorders(conn):
    long_term_memory_id = remember_query_outcome(
        conn,
        "What is the return policy?",
        [20],
        was_successful=True,
        query_embedding=_RETURN_POLICY_EMBEDDING,
    )
    similar_memory = get_long_term_memory_by_id(conn, long_term_memory_id)

    # Chunk 2 (document 20) starts behind chunk 1 (document 10) in fusion,
    # but document 20 is the boosted memory's best match.
    fused = [
        _fused_result(1, document_id=10, rrf_score=0.05),
        _fused_result(2, document_id=20, rrf_score=0.03),
    ]

    boosted = apply_memory_boost(fused, similar_memory)

    assert [result.chunk_id for result in boosted] == [2, 1]
    assert boosted[0].applied_memory_boost == pytest.approx(BOOST_AMOUNT)
    assert boosted[0].rrf_score == pytest.approx(0.03 + BOOST_AMOUNT)
    assert boosted[1].applied_memory_boost == pytest.approx(0.0)


def test_apply_memory_boost_scales_by_the_memorys_decay_weight(conn):
    long_term_memory_id = remember_query_outcome(
        conn,
        "What is the return policy?",
        [20],
        was_successful=True,
        query_embedding=_RETURN_POLICY_EMBEDDING,
    )
    update_long_term_memory(conn, long_term_memory_id, decay_weight=0.5)
    similar_memory = get_long_term_memory_by_id(conn, long_term_memory_id)

    fused = [_fused_result(2, document_id=20, rrf_score=0.03)]

    boosted = apply_memory_boost(fused, similar_memory)

    assert boosted[0].applied_memory_boost == pytest.approx(BOOST_AMOUNT * 0.5)


def test_apply_memory_boost_leaves_non_matching_documents_unboosted(conn):
    long_term_memory_id = remember_query_outcome(
        conn,
        "What is the return policy?",
        [999],
        was_successful=True,
        query_embedding=_RETURN_POLICY_EMBEDDING,
    )
    similar_memory = get_long_term_memory_by_id(conn, long_term_memory_id)

    fused = [
        _fused_result(1, document_id=10, rrf_score=0.05),
        _fused_result(2, document_id=20, rrf_score=0.03),
    ]

    boosted = apply_memory_boost(fused, similar_memory)

    assert [result.chunk_id for result in boosted] == [1, 2]
    assert all(result.applied_memory_boost == 0.0 for result in boosted)


# -- promote_session_memory_to_long_term --------------------------------------


def test_promote_session_memory_to_long_term_skips_rows_without_feedback(conn):
    record_session_query(conn, "session-1", "What is the return policy?", [1])

    promoted_ids = promote_session_memory_to_long_term(conn, "session-1")

    assert promoted_ids == []
    assert get_all_long_term_memory(conn) == []


def test_promote_session_memory_to_long_term_promotes_useful_queries(conn):
    # promote_session_memory_to_long_term() doesn't accept a pre-computed
    # embedding (each promoted row's query text differs), so this one test
    # needs the real embedding model; skip rather than fail if it can't be
    # loaded, matching tests/test_retrieval_pipeline.py's pattern.
    try:
        embed_sentences(["warm up"])
    except Exception as exc:
        pytest.skip(f"Could not load the sentence embedding model: {exc}")

    # Insert a document and one chunk directly (raw SQL) rather than going
    # through the full ingestion pipeline, since this test only needs a
    # real chunk_id -> document_id mapping for
    # promote_session_memory_to_long_term() to resolve.
    conn.execute(
        "INSERT INTO documents (filename, file_type, ingested_at) VALUES (?, 'pdf', '2026-01-01')",
        ("policy.pdf",),
    )
    document_id = conn.execute(
        "SELECT id FROM documents WHERE filename = ?", ("policy.pdf",)
    ).fetchone()["id"]
    conn.execute(
        "INSERT INTO chunks (document_id, page_number, section_heading, text, token_count) "
        "VALUES (?, NULL, NULL, 'text', 1)",
        (document_id,),
    )
    conn.commit()
    chunk_id = conn.execute(
        "SELECT id FROM chunks WHERE document_id = ?", (document_id,)
    ).fetchone()["id"]

    session_memory_id = record_session_query(
        conn, "session-1", "What is the return policy?", [chunk_id]
    )
    set_usefulness(conn, session_memory_id, useful=True)

    promoted_ids = promote_session_memory_to_long_term(conn, "session-1")

    assert len(promoted_ids) == 1
    record = get_long_term_memory_by_id(conn, promoted_ids[0])
    assert record.best_document_ids == [document_id]
    assert record.success_count == 1
