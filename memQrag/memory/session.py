"""SQLite schema for session memory records (Phase 4 PR 1).

Stores one row per query asked during a session: the query text, which
chunks were retrieved for it, and whether that retrieval turned out to be
useful (set later, once feedback exists). See docs/DECISIONS.md ("SQLite
Schema For Session Memory Records") for why `retrieved_chunk_ids` is a
plain stored value rather than a foreign key into `chunks.id`.

Functions take a plain `sqlite3.Connection` (dependency injection, same
pattern as `memQrag.ingestion.storage`), so tests use
`sqlite3.connect(":memory:")` instead of touching disk. `connect()` opens
the same shared database file `memQrag.ingestion.storage` uses, so both
modules' tables live together in one `data/memqrag.db`, per AGENTS.md's
"SQLite stores document metadata, session memory, ..." boundary.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from memQrag.ingestion.storage import DEFAULT_DB_PATH
from memQrag.ingestion.storage import connect as connect_shared_db

_SCHEMA = """
CREATE TABLE IF NOT EXISTS session_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    query TEXT NOT NULL,
    retrieved_chunk_ids TEXT NOT NULL,
    usefulness_flag INTEGER,
    created_at TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class SessionMemoryRecord:
    """A `session_memory` row, as read back from SQLite."""

    id: int
    session_id: str
    query: str
    retrieved_chunk_ids: list[int]
    usefulness_flag: bool | None
    created_at: datetime


def connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a connection to the shared memQrag SQLite database, creating
    both the ingestion tables and this module's session_memory table."""
    conn = connect_shared_db(db_path)
    create_tables(conn)
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    """Create the session_memory table if it does not already exist."""
    conn.executescript(_SCHEMA)
    conn.commit()


def record_session_query(
    conn: sqlite3.Connection,
    session_id: str,
    query: str,
    retrieved_chunk_ids: list[int],
) -> int:
    """Record one query and the chunk ids retrieved for it; return the new row's id.

    `usefulness_flag` starts unset (`NULL`) — usefulness is feedback
    collected after the fact via `set_usefulness()`, not known at query
    time.
    """
    cursor = conn.execute(
        """
        INSERT INTO session_memory
            (session_id, query, retrieved_chunk_ids, usefulness_flag, created_at)
        VALUES (?, ?, ?, NULL, ?)
        """,
        (session_id, query, json.dumps(retrieved_chunk_ids), datetime.now(UTC).isoformat()),
    )
    conn.commit()
    return cursor.lastrowid


def set_usefulness(conn: sqlite3.Connection, session_memory_id: int, useful: bool) -> None:
    """Record feedback for a previously recorded session query."""
    conn.execute(
        "UPDATE session_memory SET usefulness_flag = ? WHERE id = ?",
        (int(useful), session_memory_id),
    )
    conn.commit()


def get_session_memory(conn: sqlite3.Connection, session_id: str) -> list[SessionMemoryRecord]:
    """Return all recorded queries for one session, oldest first."""
    rows = conn.execute(
        "SELECT * FROM session_memory WHERE session_id = ? ORDER BY id", (session_id,)
    ).fetchall()
    return [_row_to_record(row) for row in rows]


def _row_to_record(row: sqlite3.Row) -> SessionMemoryRecord:
    usefulness_flag = row["usefulness_flag"]
    return SessionMemoryRecord(
        id=row["id"],
        session_id=row["session_id"],
        query=row["query"],
        retrieved_chunk_ids=json.loads(row["retrieved_chunk_ids"]),
        usefulness_flag=None if usefulness_flag is None else bool(usefulness_flag),
        created_at=datetime.fromisoformat(row["created_at"]),
    )
