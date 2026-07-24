"""Tests for memQrag.retrieval.fusion (Reciprocal Rank Fusion, Phase 3 PR 3).

Builds DenseRetrievalResult/SparseRetrievalResult lists directly (no
Chroma, no embeddings, no BM25) since fusion only operates on already
-ranked lists; this keeps the tests fast, exact, and fully network-free.
"""

import pytest

from memQrag.retrieval.dense import DenseRetrievalResult
from memQrag.retrieval.fusion import RRF_K, FusedRetrievalResult, reciprocal_rank_fusion
from memQrag.retrieval.sparse import SparseRetrievalResult


def _dense(chunk_id: int, score: float = 0.9, document_id: int = 1) -> DenseRetrievalResult:
    return DenseRetrievalResult(
        chunk_id=chunk_id,
        document_id=document_id,
        score=score,
        text=f"chunk {chunk_id}",
        source_document="fixture.txt",
        page_number=None,
        section_heading=None,
    )


def _sparse(chunk_id: int, score: float = 5.0, document_id: int = 1) -> SparseRetrievalResult:
    return SparseRetrievalResult(
        chunk_id=chunk_id,
        document_id=document_id,
        score=score,
        text=f"chunk {chunk_id}",
        source_document="fixture.txt",
        page_number=None,
        section_heading=None,
    )


def test_chunk_ranked_first_in_both_lists_is_fused_first():
    dense_results = [_dense(1), _dense(2), _dense(3)]
    sparse_results = [_sparse(1), _sparse(3), _sparse(2)]

    fused = reciprocal_rank_fusion(dense_results, sparse_results)

    assert fused[0].chunk_id == 1
    assert fused[0].fused_rank == 1


def test_chunk_appearing_in_both_lists_outranks_chunk_in_only_one():
    # chunk 1 is #2 in dense and #2 in sparse; chunk 2 is #1 in dense only.
    # RRF's "two votes beat one vote near the top" property should surface
    # chunk 1 ahead of chunk 2, even though chunk 2 was ranked #1 somewhere.
    dense_results = [_dense(2), _dense(1)]
    sparse_results = [_sparse(3), _sparse(1)]

    fused = reciprocal_rank_fusion(dense_results, sparse_results)

    fused_by_id = {result.chunk_id: result for result in fused}
    assert fused_by_id[1].rrf_score > fused_by_id[2].rrf_score
    assert fused[0].chunk_id == 1


def test_result_carries_dense_score_and_sparse_rank_when_present_in_both():
    dense_results = [_dense(1, score=0.87)]
    sparse_results = [_sparse(1, score=3.5)]

    (result,) = reciprocal_rank_fusion(dense_results, sparse_results)

    assert result.dense_score == pytest.approx(0.87)
    assert result.sparse_rank == 1
    assert result.fused_rank == 1
    assert result.rrf_score == pytest.approx(2 / (RRF_K + 1))


def test_dense_only_chunk_has_no_sparse_rank():
    dense_results = [_dense(1)]
    sparse_results = []

    (result,) = reciprocal_rank_fusion(dense_results, sparse_results)

    assert result.dense_score is not None
    assert result.sparse_rank is None
    assert result.rrf_score == pytest.approx(1 / (RRF_K + 1))


def test_sparse_only_chunk_has_no_dense_score():
    dense_results = []
    sparse_results = [_sparse(1)]

    (result,) = reciprocal_rank_fusion(dense_results, sparse_results)

    assert result.dense_score is None
    assert result.sparse_rank == 1
    assert result.rrf_score == pytest.approx(1 / (RRF_K + 1))


def test_returns_empty_list_for_two_empty_inputs():
    assert reciprocal_rank_fusion([], []) == []


def test_result_is_deduplicated_by_chunk_id():
    dense_results = [_dense(1), _dense(2)]
    sparse_results = [_sparse(2), _sparse(1)]

    fused = reciprocal_rank_fusion(dense_results, sparse_results)

    assert sorted(result.chunk_id for result in fused) == [1, 2]
    assert len(fused) == 2


def test_result_carries_shared_chunk_metadata():
    dense_results = [
        DenseRetrievalResult(
            chunk_id=1,
            document_id=7,
            score=0.9,
            text="Overview text.",
            source_document="handbook.docx",
            page_number=3,
            section_heading="Overview",
        )
    ]

    (result,) = reciprocal_rank_fusion(dense_results, [])

    assert result.chunk_id == 1
    assert result.document_id == 7
    assert result.text == "Overview text."
    assert result.source_document == "handbook.docx"
    assert result.page_number == 3
    assert result.section_heading == "Overview"


def test_fused_rank_is_one_indexed_and_contiguous():
    dense_results = [_dense(1), _dense(2), _dense(3)]

    fused = reciprocal_rank_fusion(dense_results, [])

    assert [result.fused_rank for result in fused] == [1, 2, 3]


def test_does_not_truncate_union_of_inputs():
    dense_results = [_dense(i) for i in range(20)]
    sparse_results = [_sparse(i) for i in range(20, 40)]

    fused = reciprocal_rank_fusion(dense_results, sparse_results)

    assert len(fused) == 40


def test_custom_k_changes_fusion_weighting():
    dense_results = [_dense(1)]
    sparse_results = [_sparse(1)]

    default_fused = reciprocal_rank_fusion(dense_results, sparse_results)
    custom_fused = reciprocal_rank_fusion(dense_results, sparse_results, k=1)

    assert default_fused[0].rrf_score != custom_fused[0].rrf_score
    assert custom_fused[0].rrf_score == pytest.approx(2 / (1 + 1))


def test_fused_result_is_frozen_dataclass_instance():
    (result,) = reciprocal_rank_fusion([_dense(1)], [])

    assert isinstance(result, FusedRetrievalResult)
    with pytest.raises(AttributeError):
        result.fused_rank = 99
