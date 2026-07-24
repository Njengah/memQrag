"""Cross-encoder reranking down to the final top-5 (Phase 3 PR 4).

Scores `memQrag.retrieval.fusion.reciprocal_rank_fusion`'s output against
the query with a cross-encoder (`memQrag.retrieval.cross_encoder.score_pairs`)
and returns the top-k, per docs/ARCHITECTURE.md's retrieval flow steps 7-8
("Rerank top candidates with a cross-encoder" / "Select final top-5
chunks"). See docs/DECISIONS.md ("Cross-Encoder Reranking Model And Final
Top-5 Selection") for why this step truncates its output while fusion does
not.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from memQrag.retrieval.cross_encoder import score_pairs
from memQrag.retrieval.fusion import FusedRetrievalResult

RERANK_TOP_K = 5


@dataclass(frozen=True)
class RerankedRetrievalResult:
    """One reranked hit, carrying its full dense/sparse/fusion history."""

    chunk_id: int
    document_id: int
    text: str
    source_document: str
    page_number: int | None
    section_heading: str | None
    dense_score: float | None
    sparse_rank: int | None
    fused_rank: int
    rerank_score: float
    final_rank: int


def rerank(
    fused_results: Sequence[FusedRetrievalResult],
    query: str,
    top_k: int = RERANK_TOP_K,
) -> list[RerankedRetrievalResult]:
    """Return the top `top_k` fused chunks, reranked by cross-encoder score.

    Unlike `reciprocal_rank_fusion`, this truncates its output — this is
    where the retrieval funnel narrows to its final candidate count.
    """
    if not query.strip():
        raise ValueError("query must not be empty.")
    if not fused_results:
        return []

    scores = score_pairs(query, [result.text for result in fused_results])
    ranked = sorted(zip(fused_results, scores, strict=True), key=lambda pair: pair[1], reverse=True)

    return [
        RerankedRetrievalResult(
            chunk_id=fused.chunk_id,
            document_id=fused.document_id,
            text=fused.text,
            source_document=fused.source_document,
            page_number=fused.page_number,
            section_heading=fused.section_heading,
            dense_score=fused.dense_score,
            sparse_rank=fused.sparse_rank,
            fused_rank=fused.fused_rank,
            rerank_score=score,
            final_rank=final_rank,
        )
        for final_rank, (fused, score) in enumerate(ranked[:top_k], start=1)
    ]
