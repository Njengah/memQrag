"""SQLite schema for contradiction / conflict records (Phase 5 PR 1).

Stores one row per detected conflict between two factual claims about the
same entity, with the chunk ids that support each claim and a review
status for human follow-up. Detection logic (Phase 5 PR 2) and the
`GET /api/conflicts` read path (Phase 5 PR 4) build on this schema; this
module is schema plus basic read/write only. See docs/DECISIONS.md
("SQLite Schema For Contradiction Records") for why chunk references are
JSON columns rather than foreign keys, and why this lives in its own
`memQrag.conflicts` package rather than under `memory` or `agent`.

Functions take a plain `sqlite3.Connection` (dependency injection, same
pattern as `memQrag.memory.session` / `memQrag.memory.long_term`), so
tests use `sqlite3.connect(":memory:")` instead of touching disk.
`connect()` extends `memQrag.memory.long_term.connect()`'s chain, so one
call still gets the full shared schema.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from memQrag.ingestion.storage import DEFAULT_DB_PATH
from memQrag.memory.long_term import connect as connect_long_term_db

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity TEXT NOT NULL,
    claim_a TEXT NOT NULL,
    claim_b TEXT NOT NULL,
    claim_a_chunk_ids TEXT NOT NULL,
    claim_b_chunk_ids TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    review_status TEXT NOT NULL DEFAULT 'unreviewed'
);
"""


class ConflictReviewStatus(str, Enum):
    """Whether a human has reviewed this conflict yet.

    Kept to two states for the MVP: detection surfaces conflicts as
    `UNREVIEWED`, and a later review action (Phase 5 PR 4 / Phase 8 UI)
    marks them `REVIEWED`. A fuller resolution workflow (dismissed,
    resolved-by-doc-update, etc.) can be layered on later if needed.
    """

    UNREVIEWED = "unreviewed"
    REVIEWED = "reviewed"


@dataclass(frozen=True)
class ConflictRecord:
    """A `conflicts` row, as read back from SQLite."""

    id: int
    entity: str
    claim_a: str
    claim_b: str
    claim_a_chunk_ids: list[int]
    claim_b_chunk_ids: list[int]
    detected_at: datetime
    review_status: ConflictReviewStatus


def connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a connection to the shared memQrag SQLite database, creating
    the ingestion, memory, and conflicts tables."""
    conn = connect_long_term_db(db_path)
    create_tables(conn)
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    """Create the conflicts table if it does not already exist."""
    conn.executescript(_SCHEMA)
    conn.commit()


def record_conflict(
    conn: sqlite3.Connection,
    entity: str,
    claim_a: str,
    claim_b: str,
    claim_a_chunk_ids: list[int],
    claim_b_chunk_ids: list[int],
) -> int:
    """Create a new conflict record; return the new row's id.

    Starts as `UNREVIEWED` — review status is feedback collected after the
    fact via `set_review_status()`, not known at detection time.
    """
    cursor = conn.execute(
        """
        INSERT INTO conflicts
            (entity, claim_a, claim_b, claim_a_chunk_ids, claim_b_chunk_ids,
             detected_at, review_status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entity,
            claim_a,
            claim_b,
            json.dumps(claim_a_chunk_ids),
            json.dumps(claim_b_chunk_ids),
            datetime.now(UTC).isoformat(),
            ConflictReviewStatus.UNREVIEWED.value,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def set_review_status(
    conn: sqlite3.Connection,
    conflict_id: int,
    review_status: ConflictReviewStatus,
) -> None:
    """Update one conflict's review status."""
    current = get_conflict_by_id(conn, conflict_id)
    if current is None:
        raise ValueError(f"No conflicts record with id {conflict_id}.")

    conn.execute(
        "UPDATE conflicts SET review_status = ? WHERE id = ?",
        (review_status.value, conflict_id),
    )
    conn.commit()


def get_conflict_by_id(conn: sqlite3.Connection, conflict_id: int) -> ConflictRecord | None:
    """Return one conflict by id, or `None` if it doesn't exist."""
    row = conn.execute("SELECT * FROM conflicts WHERE id = ?", (conflict_id,)).fetchone()
    return _row_to_record(row) if row else None


def get_all_conflicts(conn: sqlite3.Connection) -> list[ConflictRecord]:
    """Return every conflict, most recently detected first.

    This is the read path Phase 5 PR 4's `GET /api/conflicts` will use;
    there is no filtering by review status yet.
    """
    rows = conn.execute("SELECT * FROM conflicts ORDER BY detected_at DESC, id DESC").fetchall()
    return [_row_to_record(row) for row in rows]


def _row_to_record(row: sqlite3.Row) -> ConflictRecord:
    return ConflictRecord(
        id=row["id"],
        entity=row["entity"],
        claim_a=row["claim_a"],
        claim_b=row["claim_b"],
        claim_a_chunk_ids=json.loads(row["claim_a_chunk_ids"]),
        claim_b_chunk_ids=json.loads(row["claim_b_chunk_ids"]),
        detected_at=datetime.fromisoformat(row["detected_at"]),
        review_status=ConflictReviewStatus(row["review_status"]),
    )
