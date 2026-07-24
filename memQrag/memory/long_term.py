"""SQLite schema for long-term memory records (Phase 4 PR 2).

Stores one row per remembered query: which documents were its best
matches, and counters (success count, hit rate, decay weight, last used)
that Phase 4 PR 3 (memory-informed boosts) and PR 4 (memory decay) update
over time. See docs/DECISIONS.md ("SQLite Schema For Long-Term Memory
Records") for why there is no query-embedding column yet, and why
`best_document_ids` is a plain JSON column rather than a foreign key.

Functions take a plain `sqlite3.Connection` (dependency injection, same
pattern as `memQrag.ingestion.storage`/`memQrag.memory.session`), so tests
use `sqlite3.connect(":memory:")` instead of touching disk. `connect()`
extends `memQrag.memory.session.connect()`'s chain, so one call still
gets the full shared schema.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from memQrag.ingestion.storage import DEFAULT_DB_PATH
from memQrag.memory.session import connect as connect_session_db

_SCHEMA = """
CREATE TABLE IF NOT EXISTS long_term_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    best_document_ids TEXT NOT NULL,
    success_count INTEGER NOT NULL DEFAULT 0,
    hit_rate REAL NOT NULL DEFAULT 0.0,
    decay_weight REAL NOT NULL DEFAULT 1.0,
    last_used TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class LongTermMemoryRecord:
    """A `long_term_memory` row, as read back from SQLite."""

    id: int
    query: str
    best_document_ids: list[int]
    success_count: int
    hit_rate: float
    decay_weight: float
    last_used: datetime


def connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a connection to the shared memQrag SQLite database, creating
    the ingestion, session memory, and long-term memory tables."""
    conn = connect_session_db(db_path)
    create_tables(conn)
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    """Create the long_term_memory table if it does not already exist."""
    conn.executescript(_SCHEMA)
    conn.commit()


def record_long_term_memory(
    conn: sqlite3.Connection,
    query: str,
    best_document_ids: list[int],
) -> int:
    """Create a new long-term memory record; return the new row's id.

    Counters start at their defaults (success_count/hit_rate at 0,
    decay_weight at full strength); Phase 4 PR 3/PR 4 update them later
    via `update_long_term_memory()`, not here.
    """
    cursor = conn.execute(
        """
        INSERT INTO long_term_memory
            (query, best_document_ids, success_count, hit_rate, decay_weight, last_used)
        VALUES (?, ?, 0, 0.0, 1.0, ?)
        """,
        (query, json.dumps(best_document_ids), datetime.now(UTC).isoformat()),
    )
    conn.commit()
    return cursor.lastrowid


def update_long_term_memory(
    conn: sqlite3.Connection,
    long_term_memory_id: int,
    *,
    success_count: int | None = None,
    hit_rate: float | None = None,
    decay_weight: float | None = None,
    last_used: datetime | None = None,
) -> None:
    """Update one or more counters on an existing record.

    Omitted keyword arguments keep their current value. This is
    deliberately just a field setter, not an algorithm: it does not
    decide what the new `success_count`/`hit_rate` should be (Phase 4
    PR 3) or how `decay_weight` should shrink over time (Phase 4 PR 4).
    """
    current = get_long_term_memory_by_id(conn, long_term_memory_id)
    if current is None:
        raise ValueError(f"No long_term_memory record with id {long_term_memory_id}.")

    conn.execute(
        """
        UPDATE long_term_memory
        SET success_count = ?, hit_rate = ?, decay_weight = ?, last_used = ?
        WHERE id = ?
        """,
        (
            current.success_count if success_count is None else success_count,
            current.hit_rate if hit_rate is None else hit_rate,
            current.decay_weight if decay_weight is None else decay_weight,
            (current.last_used if last_used is None else last_used).isoformat(),
            long_term_memory_id,
        ),
    )
    conn.commit()


def get_long_term_memory_by_id(
    conn: sqlite3.Connection, long_term_memory_id: int
) -> LongTermMemoryRecord | None:
    """Return one long-term memory record by id, or `None` if it doesn't exist."""
    row = conn.execute(
        "SELECT * FROM long_term_memory WHERE id = ?", (long_term_memory_id,)
    ).fetchone()
    return _row_to_record(row) if row else None


def get_all_long_term_memory(conn: sqlite3.Connection) -> list[LongTermMemoryRecord]:
    """Return every long-term memory record, most recently used first.

    No similarity search yet — Phase 4 PR 3 will match an incoming
    query's embedding against these once query-embedding storage exists;
    this is just a full read-back for now.
    """
    rows = conn.execute("SELECT * FROM long_term_memory ORDER BY last_used DESC").fetchall()
    return [_row_to_record(row) for row in rows]


def _row_to_record(row: sqlite3.Row) -> LongTermMemoryRecord:
    return LongTermMemoryRecord(
        id=row["id"],
        query=row["query"],
        best_document_ids=json.loads(row["best_document_ids"]),
        success_count=row["success_count"],
        hit_rate=row["hit_rate"],
        decay_weight=row["decay_weight"],
        last_used=datetime.fromisoformat(row["last_used"]),
    )
