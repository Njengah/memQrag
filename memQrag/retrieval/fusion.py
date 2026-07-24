"""Reciprocal Rank Fusion for dense and sparse retrieval (Phase 3 PR 3).

Fuses `memQrag.retrieval.dense.dense_retrieve`'s and
`memQrag.retrieval.sparse.sparse_retrieve`'s ranked lists into one ranked
list, using Reciprocal Rank Fusion (Cormack, Clarke & Buettcher, 2009).
Fusing by rank position (not raw score) is what lets a bounded cosine
similarity and an unbounded BM25 score combine without normalizing them
against each other; see docs/DECISIONS.md ("Reciprocal Rank Fusion For
Dense And Sparse Results").
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from memQrag.retrieval.dense import DenseRetrievalResult
from memQrag.retrieval.sparse import SparseRetrievalResult

RRF_K = 60


@dataclass(frozen=True)
class FusedRetrievalResult:
    """One fused hit, ranked by combined dense+sparse rank position.

    `dense_score` and `sparse_rank` are `None` when the chunk did not
    appear in that ranking at all (a sparse-only or dense-only match).
    """

    chunk_id: int
    document_id: int
    text: str
    source_document: str
    page_number: int | None
    section_heading: str | None
    dense_score: float | None
    sparse_rank: int | None
    fused_rank: int
    rrf_score: float


def reciprocal_rank_fusion(
    dense_results: Sequence[DenseRetrievalResult],
    sparse_results: Sequence[SparseRetrievalResult],
    k: int = RRF_K,
) -> list[FusedRetrievalResult]:
    """Fuse two ranked lists into one, ordered by descending RRF score.

    A chunk's RRF score is `sum(1 / (k + rank))` over every input ranking
    that contains it (1-indexed rank within that ranking). Returns every
    chunk found in either input, deduplicated by `chunk_id`; callers
    truncate to whatever candidate count they need downstream (this
    function does not assume a top-N).
    """
    rrf_scores: dict[int, float] = {}
    dense_score_by_chunk_id: dict[int, float] = {}
    sparse_rank_by_chunk_id: dict[int, int] = {}
    chunk_by_id: dict[int, DenseRetrievalResult | SparseRetrievalResult] = {}

    for rank, result in enumerate(dense_results, start=1):
        rrf_scores[result.chunk_id] = rrf_scores.get(result.chunk_id, 0.0) + 1 / (k + rank)
        dense_score_by_chunk_id[result.chunk_id] = result.score
        chunk_by_id[result.chunk_id] = result

    for rank, result in enumerate(sparse_results, start=1):
        rrf_scores[result.chunk_id] = rrf_scores.get(result.chunk_id, 0.0) + 1 / (k + rank)
        sparse_rank_by_chunk_id[result.chunk_id] = rank
        chunk_by_id.setdefault(result.chunk_id, result)

    ranked_chunk_ids = sorted(rrf_scores, key=lambda chunk_id: rrf_scores[chunk_id], reverse=True)

    return [
        FusedRetrievalResult(
            chunk_id=chunk_id,
            document_id=chunk_by_id[chunk_id].document_id,
            text=chunk_by_id[chunk_id].text,
            source_document=chunk_by_id[chunk_id].source_document,
            page_number=chunk_by_id[chunk_id].page_number,
            section_heading=chunk_by_id[chunk_id].section_heading,
            dense_score=dense_score_by_chunk_id.get(chunk_id),
            sparse_rank=sparse_rank_by_chunk_id.get(chunk_id),
            fused_rank=fused_rank,
            rrf_score=rrf_scores[chunk_id],
        )
        for fused_rank, chunk_id in enumerate(ranked_chunk_ids, start=1)
    ]
