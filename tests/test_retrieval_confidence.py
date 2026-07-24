"""Tests for memQrag.retrieval.confidence (Phase 3 PR 5).

Builds RerankedRetrievalResult objects directly (no Chroma, embeddings,
BM25, or cross-encoder involved) since confidence scoring only reads
`dense_score` off an already-built result; this keeps the tests fast,
exact, and fully network-free.
"""

import pytest

from memQrag.retrieval.confidence import (
    HIGH_CONFIDENCE_THRESHOLD,
    MEDIUM_CONFIDENCE_THRESHOLD,
    ConfidenceLevel,
    ScoredRetrievalResult,
    assign_confidence,
    confidence_for_dense_score,
)
from memQrag.retrieval.rerank import RerankedRetrievalResult


def _reranked(
    chunk_id: int,
    dense_score: float | None,
    sparse_rank: int | None = None,
    final_rank: int = 1,
) -> RerankedRetrievalResult:
    return RerankedRetrievalResult(
        chunk_id=chunk_id,
        document_id=1,
        text=f"chunk {chunk_id}",
        source_document="fixture.txt",
        page_number=None,
        section_heading=None,
        dense_score=dense_score,
        sparse_rank=sparse_rank,
        fused_rank=1,
        rerank_score=5.0,
        final_rank=final_rank,
    )


def test_score_above_high_threshold_is_high():
    assert confidence_for_dense_score(0.9) is ConfidenceLevel.HIGH


def test_score_just_above_high_threshold_is_high():
    assert confidence_for_dense_score(HIGH_CONFIDENCE_THRESHOLD + 0.0001) is ConfidenceLevel.HIGH


def test_score_exactly_at_high_threshold_is_medium():
    assert confidence_for_dense_score(HIGH_CONFIDENCE_THRESHOLD) is ConfidenceLevel.MEDIUM


def test_score_in_middle_of_medium_range_is_medium():
    assert confidence_for_dense_score(0.75) is ConfidenceLevel.MEDIUM


def test_score_exactly_at_medium_threshold_is_medium():
    assert confidence_for_dense_score(MEDIUM_CONFIDENCE_THRESHOLD) is ConfidenceLevel.MEDIUM


def test_score_just_below_medium_threshold_is_low():
    assert confidence_for_dense_score(MEDIUM_CONFIDENCE_THRESHOLD - 0.0001) is ConfidenceLevel.LOW


def test_score_well_below_medium_threshold_is_low():
    assert confidence_for_dense_score(0.1) is ConfidenceLevel.LOW


def test_negative_score_is_low():
    assert confidence_for_dense_score(-0.5) is ConfidenceLevel.LOW


def test_none_score_is_low_not_an_error():
    assert confidence_for_dense_score(None) is ConfidenceLevel.LOW


def test_assign_confidence_labels_each_result_in_order():
    reranked_results = [
        _reranked(1, dense_score=0.9, final_rank=1),
        _reranked(2, dense_score=0.7, final_rank=2),
        _reranked(3, dense_score=0.2, final_rank=3),
    ]

    scored = assign_confidence(reranked_results)

    assert [result.confidence_level for result in scored] == [
        ConfidenceLevel.HIGH,
        ConfidenceLevel.MEDIUM,
        ConfidenceLevel.LOW,
    ]


def test_assign_confidence_does_not_reorder_or_filter():
    reranked_results = [
        _reranked(1, dense_score=0.1, final_rank=1),
        _reranked(2, dense_score=0.95, final_rank=2),
    ]

    scored = assign_confidence(reranked_results)

    assert [result.chunk_id for result in scored] == [1, 2]
    assert len(scored) == 2


def test_assign_confidence_labels_sparse_only_chunk_low():
    reranked_results = [_reranked(1, dense_score=None, sparse_rank=3)]

    (result,) = assign_confidence(reranked_results)

    assert result.confidence_level is ConfidenceLevel.LOW
    assert result.dense_score is None
    assert result.sparse_rank == 3


def test_assign_confidence_returns_empty_list_for_empty_input():
    assert assign_confidence([]) == []


def test_assign_confidence_carries_forward_all_rerank_fields():
    reranked = RerankedRetrievalResult(
        chunk_id=1,
        document_id=7,
        text="Overview text.",
        source_document="handbook.docx",
        page_number=3,
        section_heading="Overview",
        dense_score=0.9,
        sparse_rank=2,
        fused_rank=1,
        rerank_score=6.5,
        final_rank=1,
    )

    (result,) = assign_confidence([reranked])

    assert result.chunk_id == 1
    assert result.document_id == 7
    assert result.text == "Overview text."
    assert result.source_document == "handbook.docx"
    assert result.page_number == 3
    assert result.section_heading == "Overview"
    assert result.sparse_rank == 2
    assert result.fused_rank == 1
    assert result.rerank_score == pytest.approx(6.5)
    assert result.final_rank == 1


def test_confidence_level_is_str_enum_for_serialization():
    assert ConfidenceLevel.HIGH == "high"
    assert ConfidenceLevel.MEDIUM == "medium"
    assert ConfidenceLevel.LOW == "low"


def test_scored_result_is_frozen_dataclass_instance():
    (result,) = assign_confidence([_reranked(1, dense_score=0.9)])

    assert isinstance(result, ScoredRetrievalResult)
    with pytest.raises(AttributeError):
        result.confidence_level = ConfidenceLevel.LOW
