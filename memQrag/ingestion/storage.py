"""SQLite persistence for ingested document and chunk metadata (Phase 2 PR 4).

Stores what `memQrag.ingestion.extraction` and `memQrag.ingestion.chunking`
already produce: one row per ingested document, and one row per chunk. See
docs/DECISIONS.md ("SQLite Persistence For Document And Chunk Metadata") for
the schema rationale, including why `staleness_status` (Phase 4) and
`embedding_reference` (Phase 2 PR 5) columns are deferred.

Functions take a plain `sqlite3.Connection` (dependency injection), so tests
use `sqlite3.connect(":memory:")` instead of touching disk.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from memQrag.ingestion.chunking import Chunk
from memQrag.ingestion.extraction import ExtractedDocument

DEFAULT_DB_PATH = Path("data/memqrag.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL UNIQUE,
    file_type TEXT NOT NULL,
    created_date TEXT,
    last_modified_date TEXT,
    ingested_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER,
    section_heading TEXT,
    text TEXT NOT NULL,
    token_count INTEGER NOT NULL
);
"""


@dataclass(frozen=True)
class DocumentRecord:
    """A `documents` row, as read back from SQLite."""

    id: int
    filename: str
    file_type: str
    created_date: datetime | None
    last_modified_date: datetime | None
    ingested_at: datetime


@dataclass(frozen=True)
class ChunkRecord:
    """A `chunks` row, as read back from SQLite."""

    id: int
    document_id: int
    page_number: int | None
    section_heading: str | None
    text: str
    token_count: int


def connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a connection to the memQrag SQLite database, creating the schema if needed."""
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    create_tables(conn)
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    """Create the documents/chunks tables if they do not already exist."""
    conn.executescript(_SCHEMA)
    conn.commit()


def save_document(conn: sqlite3.Connection, document: ExtractedDocument) -> int:
    """Insert or update a document row by filename; return its id.

    Re-ingesting an already-known filename updates that row in place rather
    than creating a duplicate document.
    """
    conn.execute(
        """
        INSERT INTO documents (filename, file_type, created_date, last_modified_date, ingested_at)
        VALUES (:filename, :file_type, :created_date, :last_modified_date, :ingested_at)
        ON CONFLICT(filename) DO UPDATE SET
            file_type = excluded.file_type,
            created_date = excluded.created_date,
            last_modified_date = excluded.last_modified_date,
            ingested_at = excluded.ingested_at
        """,
        {
            "filename": document.source_document,
            "file_type": document.file_type.value,
            "created_date": _isoformat(document.created_date),
            "last_modified_date": _isoformat(document.last_modified_date),
            "ingested_at": datetime.now(UTC).isoformat(),
        },
    )
    conn.commit()
    row = conn.execute(
        "SELECT id FROM documents WHERE filename = ?", (document.source_document,)
    ).fetchone()
    return row["id"]


def replace_chunks(conn: sqlite3.Connection, document_id: int, chunks: list[Chunk]) -> list[int]:
    """Replace all chunks belonging to a document; return the new chunk ids, in order."""
    conn.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
    chunk_ids = []
    for chunk in chunks:
        cursor = conn.execute(
            """
            INSERT INTO chunks (document_id, page_number, section_heading, text, token_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            (document_id, chunk.page_number, chunk.section_heading, chunk.text, chunk.token_count),
        )
        chunk_ids.append(cursor.lastrowid)
    conn.commit()
    return chunk_ids


def persist_ingested_document(
    conn: sqlite3.Connection, document: ExtractedDocument, chunks: list[Chunk]
) -> tuple[int, list[int]]:
    """Save a document and its chunks together; return `(document_id, chunk_ids)`."""
    document_id = save_document(conn, document)
    chunk_ids = replace_chunks(conn, document_id, chunks)
    return document_id, chunk_ids


def get_document_by_filename(conn: sqlite3.Connection, filename: str) -> DocumentRecord | None:
    """Return the document row matching `filename`, or `None` if not ingested."""
    row = conn.execute("SELECT * FROM documents WHERE filename = ?", (filename,)).fetchone()
    return _row_to_document(row) if row else None


def get_chunks_for_document(conn: sqlite3.Connection, document_id: int) -> list[ChunkRecord]:
    """Return all chunks for a document, in insertion order."""
    rows = conn.execute(
        "SELECT * FROM chunks WHERE document_id = ? ORDER BY id", (document_id,)
    ).fetchall()
    return [_row_to_chunk(row) for row in rows]


def _isoformat(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _row_to_document(row: sqlite3.Row) -> DocumentRecord:
    return DocumentRecord(
        id=row["id"],
        filename=row["filename"],
        file_type=row["file_type"],
        created_date=_parse_datetime(row["created_date"]),
        last_modified_date=_parse_datetime(row["last_modified_date"]),
        ingested_at=datetime.fromisoformat(row["ingested_at"]),
    )


def _row_to_chunk(row: sqlite3.Row) -> ChunkRecord:
    return ChunkRecord(
        id=row["id"],
        document_id=row["document_id"],
        page_number=row["page_number"],
        section_heading=row["section_heading"],
        text=row["text"],
        token_count=row["token_count"],
    )
