"""Configurable staleness detection for frequently retrieved documents
(Phase 4 PR 5).

Flags a document `STALE` once it is both old (no fresher content in over
`STALENESS_AGE_DAYS` days) and frequently retrieved (its chunks have shown
up in at least `MIN_RETRIEVAL_COUNT` recorded `session_memory` queries,
across every session), per `docs/PRODUCT_TIMELINE.md`'s "Implement
configurable staleness detection for frequently retrieved documents older
than 90 days." See docs/DECISIONS.md ("Configurable Staleness Detection
For Frequently Retrieved Documents") for why both conditions are required
together, and why the result is a plain `documents.staleness_status`
column rather than a separate review-workflow table.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

from memQrag.ingestion.storage import (
    DocumentRecord,
    DocumentStalenessStatus,
    get_all_documents,
    get_chunk_by_id,
    update_document_staleness_status,
)
from memQrag.memory.session import get_all_session_memory

STALENESS_AGE_DAYS = 90
MIN_RETRIEVAL_COUNT = 5


def effective_document_date(document: DocumentRecord) -> datetime:
    """The date staleness age is measured from.

    Prefers `last_modified_date` (the actual content freshness signal),
    falling back to `created_date`, and finally `ingested_at` — the only
    one of the three every document is guaranteed to have, since PDF/DOCX
    extraction can supply all three but plain TXT/Markdown files often
    supply neither `created_date` nor `last_modified_date` (see
    docs/DECISIONS.md, "Text Extraction Adapter Behavior").
    """
    return document.last_modified_date or document.created_date or document.ingested_at


def count_document_retrievals(conn: sqlite3.Connection, document_id: int) -> int:
    """Count how many recorded queries (across every session) retrieved at
    least one chunk belonging to `document_id`.

    A query that retrieves several of the same document's chunks still
    counts once — this counts *how often the document was retrieved*, not
    how many of its chunks were retrieved in total.
    """
    count = 0
    for session_record in get_all_session_memory(conn):
        retrieved_document_ids = {
            chunk.document_id
            for chunk_id in session_record.retrieved_chunk_ids
            if (chunk := get_chunk_by_id(conn, chunk_id)) is not None
        }
        if document_id in retrieved_document_ids:
            count += 1
    return count


def is_stale(
    conn: sqlite3.Connection,
    document: DocumentRecord,
    now: datetime | None = None,
    age_days: int = STALENESS_AGE_DAYS,
    min_retrieval_count: int = MIN_RETRIEVAL_COUNT,
) -> bool:
    """A document is stale once it is both old and frequently retrieved.

    Age alone is not enough — an old, rarely-used document is simply
    unimportant, not a review priority; retrieval frequency alone is not
    enough either — a frequently retrieved *recent* document is working as
    intended. Both conditions together are what "frequently retrieved
    documents older than 90 days" (the tracker item) actually describes.
    """
    now = now or datetime.now(UTC)
    age = now - effective_document_date(document)
    if age < timedelta(days=age_days):
        return False
    return count_document_retrievals(conn, document.id) >= min_retrieval_count


def detect_stale_documents(
    conn: sqlite3.Connection,
    now: datetime | None = None,
    age_days: int = STALENESS_AGE_DAYS,
    min_retrieval_count: int = MIN_RETRIEVAL_COUNT,
) -> list[int]:
    """Recompute and persist `staleness_status` for every document.

    Every document is re-evaluated from scratch each call (not just ones
    currently `FRESH`), so a document that stops qualifying — e.g. it was
    re-ingested, which resets `staleness_status` to `FRESH` and refreshes
    `last_modified_date` via `memQrag.ingestion.storage.save_document()` —
    is not left stuck flagged `STALE` from a previous sweep. Returns the
    ids of documents flagged `STALE` by this sweep (not just the ones that
    changed), so a caller has the full current stale list without a second
    query.

    Not called automatically by anything yet — no scheduler/orchestration
    layer exists (same "call functions directly until a real need arises"
    precedent as `memQrag.memory.boost`/`memQrag.memory.decay`). A future
    scheduled job or the Phase 7 API layer is the eventual caller.
    """
    now = now or datetime.now(UTC)
    stale_ids = []
    for document in get_all_documents(conn):
        status = (
            DocumentStalenessStatus.STALE
            if is_stale(
                conn, document, now=now, age_days=age_days, min_retrieval_count=min_retrieval_count
            )
            else DocumentStalenessStatus.FRESH
        )
        if status != document.staleness_status:
            update_document_staleness_status(conn, document.id, status)
        if status is DocumentStalenessStatus.STALE:
            stale_ids.append(document.id)
    return stale_ids
