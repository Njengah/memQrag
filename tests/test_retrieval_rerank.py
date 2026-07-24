"""Tests for memQrag.retrieval.rerank (cross-encoder reranking, Phase 3 PR 4).

Most tests substitute a fake `score_pairs` (matching the fake embedder
pattern in tests/test_ingestion_chunking.py and tests/test_retrieval_dense.py)
instead of downloading the real fastembed cross-encoder model, keeping
ranking assertions exact and the tests network-free. One integration test
at the end uses the real `memQrag.retrieval.cross_encoder.score_pairs`,
skipping (not failing) if the model cannot be loaded.
"""

import pytest

from memQrag.retrieval.cross_encoder import score_pairs
from memQrag.retrieval.fusion import FusedRetrievalResult
from memQrag.retrieval.rerank import RERANK_TOP_K, RerankedRetrievalResult, rerank


def _fused(
    chunk_id: int,
    text: str = "some chunk text",
    dense_score: float | None = 0.8,
    sparse_rank: int | None = 1,
    fused_rank: int = 1,
    document_id: int = 1,
) -> FusedRetrievalResult:
    return FusedRetrievalResult(
        chunk_id=chunk_id,
        document_id=document_id,
        text=text,
        source_document="fixture.txt",
        page_number=None,
        section_heading=None,
        dense_score=dense_score,
        sparse_rank=sparse_rank,
        fused_rank=fused_rank,
        rrf_score=1.0,
    )


def test_rerank_orders_by_descending_cross_encoder_score(monkeypatch):
    fused_results = [_fused(1), _fused(2), _fused(3)]
    monkeypatch.setattr(
        "memQrag.retrieval.rerank.score_pairs",
        lambda query, documents: [0.1, 9.5, 3.0],
    )

    reranked = rerank(fused_results, "some query")

    assert [result.chunk_id for result in reranked] == [2, 3, 1]


def test_rerank_assigns_one_indexed_contiguous_final_rank(monkeypatch):
    fused_results = [_fused(1), _fused(2), _fused(3)]
    monkeypatch.setattr(
        "memQrag.retrieval.rerank.score_pairs",
        lambda query, documents: [0.1, 9.5, 3.0],
    )

    reranked = rerank(fused_results, "some query")

    assert [result.final_rank for result in reranked] == [1, 2, 3]


def test_rerank_truncates_to_default_top_5(monkeypatch):
    fused_results = [_fused(i) for i in range(10)]
    monkeypatch.setattr(
        "memQrag.retrieval.rerank.score_pairs",
        lambda query, documents: list(range(len(documents))),
    )

    reranked = rerank(fused_results, "some query")

    assert len(reranked) == RERANK_TOP_K == 5


def test_rerank_respects_custom_top_k(monkeypatch):
    fused_results = [_fused(i) for i in range(10)]
    monkeypatch.setattr(
        "memQrag.retrieval.rerank.score_pairs",
        lambda query, documents: list(range(len(documents))),
    )

    reranked = rerank(fused_results, "some query", top_k=2)

    assert len(reranked) == 2


def test_rerank_returns_fewer_than_top_k_when_input_is_smaller(monkeypatch):
    fused_results = [_fused(1), _fused(2)]
    monkeypatch.setattr(
        "memQrag.retrieval.rerank.score_pairs",
        lambda query, documents: [1.0, 2.0],
    )

    reranked = rerank(fused_results, "some query")

    assert len(reranked) == 2


def test_rerank_carries_forward_fusion_history(monkeypatch):
    fused_results = [_fused(1, dense_score=0.72, sparse_rank=4, fused_rank=3)]
    monkeypatch.setattr("memQrag.retrieval.rerank.score_pairs", lambda query, documents: [5.0])

    (result,) = rerank(fused_results, "some query")

    assert result.dense_score == pytest.approx(0.72)
    assert result.sparse_rank == 4
    assert result.fused_rank == 3
    assert result.rerank_score == pytest.approx(5.0)


def test_rerank_carries_shared_chunk_metadata(monkeypatch):
    fused_results = [
        FusedRetrievalResult(
            chunk_id=1,
            document_id=7,
            text="Overview text.",
            source_document="handbook.docx",
            page_number=3,
            section_heading="Overview",
            dense_score=0.9,
            sparse_rank=None,
            fused_rank=1,
            rrf_score=0.5,
        )
    ]
    monkeypatch.setattr("memQrag.retrieval.rerank.score_pairs", lambda query, documents: [1.0])

    (result,) = rerank(fused_results, "some query")

    assert result.chunk_id == 1
    assert result.document_id == 7
    assert result.text == "Overview text."
    assert result.source_document == "handbook.docx"
    assert result.page_number == 3
    assert result.section_heading == "Overview"


def test_rerank_handles_dense_only_and_sparse_only_inputs(monkeypatch):
    fused_results = [
        _fused(1, dense_score=0.9, sparse_rank=None),
        _fused(2, dense_score=None, sparse_rank=1),
    ]
    monkeypatch.setattr("memQrag.retrieval.rerank.score_pairs", lambda query, documents: [1.0, 2.0])

    reranked = rerank(fused_results, "some query")

    by_id = {result.chunk_id: result for result in reranked}
    assert by_id[1].sparse_rank is None
    assert by_id[2].dense_score is None


def test_rerank_returns_empty_list_for_empty_input():
    assert rerank([], "some query") == []


def test_rerank_rejects_blank_query():
    with pytest.raises(ValueError, match="must not be empty"):
        rerank([_fused(1)], "   ")


def test_reranked_result_is_frozen_dataclass_instance(monkeypatch):
    monkeypatch.setattr("memQrag.retrieval.rerank.score_pairs", lambda query, documents: [1.0])

    (result,) = rerank([_fused(1)], "some query")

    assert isinstance(result, RerankedRetrievalResult)
    with pytest.raises(AttributeError):
        result.final_rank = 99


def test_rerank_end_to_end_with_real_cross_encoder():
    try:
        score_pairs("warm up", ["warm up document"])
    except Exception as exc:
        pytest.skip(f"Could not load the cross-encoder model: {exc}")

    fused_results = [
        _fused(1, text="Fictional lighthouse logs are kept for a decade."),
        _fused(2, text="Fictional stock markets fell sharply on Tuesday."),
    ]

    reranked = rerank(fused_results, "How long are lighthouse logs kept?")

    assert reranked[0].chunk_id == 1
    assert len(reranked) == 2
