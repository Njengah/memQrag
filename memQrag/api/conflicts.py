"""`GET /api/conflicts` — list stored contradiction records for human review.

Phase 5 PR 4 of docs/PRODUCT_TIMELINE.md. Reads via
`memQrag.conflicts.records.get_all_conflicts()` and returns both opposing
claims on every item — never a single resolved claim. See docs/DECISIONS.md
("GET /api/conflicts Read Path").
"""

from __future__ import annotations

import sqlite3
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from memQrag.api.deps import get_db
from memQrag.conflicts.records import ConflictRecord, ConflictReviewStatus, get_all_conflicts

router = APIRouter(prefix="/api", tags=["conflicts"])


class ConflictResponse(BaseModel):
    """One stored conflict, ready for human review.

    `claim_a` and `claim_b` are always both present — the API never picks
    a winner between them.
    """

    id: int
    entity: str
    claim_a: str
    claim_b: str
    claim_a_chunk_ids: list[int]
    claim_b_chunk_ids: list[int]
    detected_at: datetime
    review_status: ConflictReviewStatus


class ConflictListResponse(BaseModel):
    """Payload for `GET /api/conflicts`."""

    conflicts: list[ConflictResponse] = Field(default_factory=list)


def _to_response(record: ConflictRecord) -> ConflictResponse:
    return ConflictResponse(
        id=record.id,
        entity=record.entity,
        claim_a=record.claim_a,
        claim_b=record.claim_b,
        claim_a_chunk_ids=record.claim_a_chunk_ids,
        claim_b_chunk_ids=record.claim_b_chunk_ids,
        detected_at=record.detected_at,
        review_status=record.review_status,
    )


@router.get("/conflicts", response_model=ConflictListResponse)
def list_conflicts(conn: sqlite3.Connection = Depends(get_db)) -> ConflictListResponse:
    """Return every stored conflict, most recently detected first."""
    records = get_all_conflicts(conn)
    return ConflictListResponse(conflicts=[_to_response(record) for record in records])
