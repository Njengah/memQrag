"""Shared FastAPI dependencies for memQrag API routes.

DB connections open the shared SQLite schema via
`memQrag.conflicts.records.connect()` (which chains through long-term /
session / ingestion tables). Tests override `get_db` with a temp-file or
in-memory path rather than touching `data/memqrag.db`.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator

from memQrag.conflicts.records import connect


def get_db() -> Iterator[sqlite3.Connection]:
    """Yield one SQLite connection per request, closed afterward."""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()
