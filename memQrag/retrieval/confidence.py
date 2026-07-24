"""Confidence scoring for the final top-5 (Phase 3 PR 5).

Assigns a HIGH/MEDIUM/LOW confidence level to each of
`memQrag.retrieval.rerank.rerank`'s output chunks, from the cosine
similarity thresholds docs/ARCHITECTURE.md's retrieval flow step 9 already
specifies. See docs/DECISIONS.md ("Confidence Scoring Thresholds And
Sparse-Only Handling") for why a chunk with no `dense_score` (a
sparse-only match) is always LOW rather than falling back to
`rerank_score` or some other signal.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from memQrag.retrieval.rerank import RerankedRetrievalResult

HIGH_CONFIDENCE_THRESHOLD = 0.85
MEDIUM_CONFIDENCE_THRESHOLD = 0.65


class ConfidenceLevel(str, Enum):
    """Per docs/ARCHITECTURE.md's retrieval flow step 9."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class ScoredRetrievalResult:
    """One final retrieval result, carrying its full history plus confidence."""

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
    confidence_level: ConfidenceLevel


def confidence_for_dense_score(dense_score: float | None) -> ConfidenceLevel:
    """Return the confidence level for one cosine similarity score.

    A `None` score (no dense match at all — a sparse-only chunk) is
    always LOW: there is no cosine similarity evidence to call it
    anything higher, and doing otherwise would hide a real gap in
    evidence behind a confident label (see AGENTS.md's "do not hide low
    confidence retrieval behind confident answer wording").
    """
    if dense_score is None:
        return ConfidenceLevel.LOW
    if dense_score > HIGH_CONFIDENCE_THRESHOLD:
        return ConfidenceLevel.HIGH
    if dense_score >= MEDIUM_CONFIDENCE_THRESHOLD:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def assign_confidence(
    reranked_results: Sequence[RerankedRetrievalResult],
) -> list[ScoredRetrievalResult]:
    """Attach a confidence level to each reranked chunk, in order.

    Does not filter or reorder: confidence is a label on the existing
    final-top-5 ranking, not another ranking signal at this stage.
    """
    return [
        ScoredRetrievalResult(
            chunk_id=result.chunk_id,
            document_id=result.document_id,
            text=result.text,
            source_document=result.source_document,
            page_number=result.page_number,
            section_heading=result.section_heading,
            dense_score=result.dense_score,
            sparse_rank=result.sparse_rank,
            fused_rank=result.fused_rank,
            rerank_score=result.rerank_score,
            final_rank=result.final_rank,
            confidence_level=confidence_for_dense_score(result.dense_score),
        )
        for result in reranked_results
    ]
