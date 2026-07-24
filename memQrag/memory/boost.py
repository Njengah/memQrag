"""Memory-informed retrieval boosts for similar past queries (Phase 4 PR 3).

Closes the loop `docs/ARCHITECTURE.md`'s retrieval flow describes: session
feedback (`memQrag.memory.session`) is promoted into long-term memory
(`memQrag.memory.long_term`), and a future query similar enough to a
successful past one gets its previously-useful documents boosted in the
current fused retrieval ranking. See docs/DECISIONS.md ("Memory-Informed
Retrieval Boosts For Similar Past Queries") for the threshold/formula
rationale.

Three pieces, matching the three places this plugs into the retrieval
flow:
- `promote_session_memory_to_long_term()` / `remember_query_outcome()`:
  the write path, turning session feedback into long-term memory (flow
  step 1, informally — feedback from a *previous* query's flow step 11).
- `find_similar_successful_memory()`: flow step 2, "check long-term memory
  for similar successful queries."
- `apply_memory_boost()`: flow step 6, "apply memory-informed boosts where
  appropriate," run on `memQrag.retrieval.fusion`'s output before
  `memQrag.retrieval.rerank`.
"""

from __future__ import annotations

import math
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from memQrag.ingestion.embeddings import embed_sentences
from memQrag.ingestion.storage import get_chunk_by_id
from memQrag.memory.long_term import (
    LongTermMemoryRecord,
    get_all_long_term_memory,
    record_long_term_memory,
    update_long_term_memory,
)
from memQrag.memory.session import get_session_memory
from memQrag.retrieval.fusion import FusedRetrievalResult

SIMILARITY_THRESHOLD = 0.90
MERGE_THRESHOLD = 0.95
MIN_HIT_RATE_TO_BOOST = 0.5
BOOST_AMOUNT = 0.05


def _cosine_similarity(vector_a: Sequence[float], vector_b: Sequence[float]) -> float:
    dot_product = sum(a * b for a, b in zip(vector_a, vector_b, strict=True))
    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def find_similar_successful_memory(
    conn: sqlite3.Connection,
    query: str,
    *,
    query_embedding: Sequence[float] | None = None,
    similarity_threshold: float = SIMILARITY_THRESHOLD,
    min_hit_rate: float = MIN_HIT_RATE_TO_BOOST,
) -> LongTermMemoryRecord | None:
    """Return the most similar past query's long-term memory record, if one
    both exceeds `similarity_threshold` and has a track record of being
    useful (`match_count > 0` and `hit_rate >= min_hit_rate`); else `None`.

    Pass `query_embedding` to reuse an embedding already computed for this
    query (e.g. the one `memQrag.retrieval.dense.dense_retrieve` computes
    for the same query text) instead of calling `embed_sentences` again.
    """
    if not query.strip():
        raise ValueError("query must not be empty.")

    embedding = query_embedding if query_embedding is not None else embed_sentences([query])[0]

    best_match: tuple[LongTermMemoryRecord, float] | None = None
    for record in get_all_long_term_memory(conn):
        if record.match_count == 0 or record.hit_rate < min_hit_rate:
            continue
        similarity = _cosine_similarity(embedding, record.query_embedding)
        if similarity < similarity_threshold:
            continue
        if best_match is None or similarity > best_match[1]:
            best_match = (record, similarity)

    return best_match[0] if best_match else None


@dataclass(frozen=True)
class BoostedRetrievalResult:
    """A `FusedRetrievalResult` with a memory-informed boost applied (or not).

    `fused_rank` and `rrf_score` reflect the *post-boost* order/score, not
    the fusion-only values carried on the input `FusedRetrievalResult`.
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
    applied_memory_boost: float


def apply_memory_boost(
    fused_results: Sequence[FusedRetrievalResult],
    similar_memory: LongTermMemoryRecord | None,
    boost_amount: float = BOOST_AMOUNT,
) -> list[BoostedRetrievalResult]:
    """Boost every fused result whose document was one of `similar_memory`'s
    best matches, then re-rank by the boosted score.

    Passing `similar_memory=None` (no qualifying past query found by
    `find_similar_successful_memory`) leaves every score unchanged and
    preserves the original fusion order — this is the common case, and
    callers are expected to pass `None` straight through rather than
    special-casing it themselves.
    """
    boosted_document_ids = set(similar_memory.best_document_ids) if similar_memory else set()

    def boost_for(result: FusedRetrievalResult) -> float:
        return boost_amount if result.document_id in boosted_document_ids else 0.0

    ranked = sorted(
        fused_results, key=lambda result: result.rrf_score + boost_for(result), reverse=True
    )

    return [
        BoostedRetrievalResult(
            chunk_id=result.chunk_id,
            document_id=result.document_id,
            text=result.text,
            source_document=result.source_document,
            page_number=result.page_number,
            section_heading=result.section_heading,
            dense_score=result.dense_score,
            sparse_rank=result.sparse_rank,
            fused_rank=new_rank,
            rrf_score=result.rrf_score + boost_for(result),
            applied_memory_boost=boost_for(result),
        )
        for new_rank, result in enumerate(ranked, start=1)
    ]


def remember_query_outcome(
    conn: sqlite3.Connection,
    query: str,
    best_document_ids: list[int],
    was_successful: bool,
    *,
    query_embedding: Sequence[float] | None = None,
    merge_threshold: float = MERGE_THRESHOLD,
) -> int:
    """Record one query's outcome into long-term memory.

    Reinforces an existing near-duplicate record (cosine similarity
    `>= merge_threshold`) instead of creating one, so that a query asked
    many times in slightly different words accumulates into one row's
    `success_count`/`match_count`/`hit_rate` rather than fragmenting across
    near-identical rows. Returns the id of the record created or
    reinforced.
    """
    if not query.strip():
        raise ValueError("query must not be empty.")

    embedding = query_embedding if query_embedding is not None else embed_sentences([query])[0]
    existing_records = get_all_long_term_memory(conn)

    best_match: tuple[LongTermMemoryRecord, float] | None = None
    for record in existing_records:
        similarity = _cosine_similarity(embedding, record.query_embedding)
        if similarity >= merge_threshold and (best_match is None or similarity > best_match[1]):
            best_match = (record, similarity)

    if best_match is None:
        long_term_memory_id = record_long_term_memory(conn, query, embedding, best_document_ids)
        update_long_term_memory(
            conn,
            long_term_memory_id,
            success_count=1 if was_successful else 0,
            match_count=1,
            hit_rate=1.0 if was_successful else 0.0,
        )
        return long_term_memory_id

    record, _ = best_match
    new_match_count = record.match_count + 1
    new_success_count = record.success_count + (1 if was_successful else 0)
    update_long_term_memory(
        conn,
        record.id,
        success_count=new_success_count,
        match_count=new_match_count,
        hit_rate=new_success_count / new_match_count,
        last_used=datetime.now(UTC),
    )
    return record.id


def promote_session_memory_to_long_term(
    conn: sqlite3.Connection,
    session_id: str,
    merge_threshold: float = MERGE_THRESHOLD,
) -> list[int]:
    """Promote every session query with feedback into long-term memory.

    Reads `memQrag.memory.session.get_session_memory()` for one session and
    calls `remember_query_outcome()` for each row whose `usefulness_flag`
    has been set (skipping rows with no feedback yet — `usefulness_flag is
    None`), mapping each row's `retrieved_chunk_ids` to their owning
    document ids along the way (`session_memory` only stores chunk ids, per
    docs/DECISIONS.md's "SQLite Schema For Session Memory Records").
    Returns the long_term_memory ids created or reinforced, one per
    promoted session row, in the same order as `get_session_memory()`.
    """
    promoted_ids = []
    for session_record in get_session_memory(conn, session_id):
        if session_record.usefulness_flag is None:
            continue
        document_ids = _document_ids_for_chunks(conn, session_record.retrieved_chunk_ids)
        promoted_ids.append(
            remember_query_outcome(
                conn,
                session_record.query,
                document_ids,
                was_successful=session_record.usefulness_flag,
                merge_threshold=merge_threshold,
            )
        )
    return promoted_ids


def _document_ids_for_chunks(conn: sqlite3.Connection, chunk_ids: list[int]) -> list[int]:
    document_ids: list[int] = []
    for chunk_id in chunk_ids:
        chunk = get_chunk_by_id(conn, chunk_id)
        if chunk is not None and chunk.document_id not in document_ids:
            document_ids.append(chunk.document_id)
    return document_ids
