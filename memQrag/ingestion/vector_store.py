"""ChromaDB vector persistence for ingested chunks (Phase 2 PR 5).

Stores one vector per `Chunk` (see `memQrag.ingestion.chunking`), embedded
with the same model used for chunk-time semantic grouping
(`memQrag.ingestion.embeddings.embed_sentences`), so chunk boundaries and
stored vectors stay consistent with one embedding model. See
docs/DECISIONS.md ("ChromaDB Vector Persistence") for the full rationale.

The Chroma vector id for a chunk is `str(chunk_id)`, where `chunk_id` is
that chunk's SQLite `chunks.id` (see `memQrag.ingestion.storage`). This is
how a retrieved vector "resolves back to stored chunk metadata": `chunk_id
= int(vector_id)`.

Functions take an already-constructed Chroma collection (dependency
injection), so tests use `chromadb.EphemeralClient()` (a real, in-process
Chroma client, no server or network) instead of requiring Docker.
"""

from __future__ import annotations

import os
from collections.abc import Sequence

import chromadb
from chromadb.api.models.Collection import Collection

from memQrag.ingestion.chunking import Chunk
from memQrag.ingestion.embeddings import embed_sentences

COLLECTION_NAME = "memqrag_chunks"

DEFAULT_CHROMA_HOST = "localhost"
DEFAULT_CHROMA_PORT = 8001  # matches docker-compose.yml's host-side chroma port mapping


def get_collection(client: chromadb.ClientAPI | None = None) -> Collection:
    """Return the memqrag_chunks collection, creating it if needed.

    Defaults to an HTTP client pointed at the CHROMA_HOST/CHROMA_PORT
    environment variables (set by docker-compose.yml for the api service),
    falling back to localhost:8001 for a non-Docker local `chroma` run.
    """
    if client is None:
        client = chromadb.HttpClient(
            host=os.environ.get("CHROMA_HOST", DEFAULT_CHROMA_HOST),
            port=int(os.environ.get("CHROMA_PORT", DEFAULT_CHROMA_PORT)),
        )
    return client.get_or_create_collection(COLLECTION_NAME)


def persist_chunk_vectors(
    collection: Collection,
    document_id: int,
    chunk_ids: Sequence[int],
    chunks: Sequence[Chunk],
) -> list[str]:
    """Embed and upsert one vector per chunk; return the Chroma ids used.

    `chunk_ids` must align positionally with `chunks`, as returned together
    by `memQrag.ingestion.storage.persist_ingested_document`.
    """
    if len(chunk_ids) != len(chunks):
        raise ValueError("chunk_ids and chunks must have the same length.")
    if not chunks:
        return []

    vector_ids = [str(chunk_id) for chunk_id in chunk_ids]
    embeddings = embed_sentences([chunk.text for chunk in chunks])
    collection.upsert(
        ids=vector_ids,
        embeddings=embeddings,
        metadatas=[_chunk_metadata(document_id, chunk) for chunk in chunks],
        documents=[chunk.text for chunk in chunks],
    )
    return vector_ids


def delete_chunk_vectors(collection: Collection, chunk_ids: Sequence[int]) -> None:
    """Delete vectors for the given chunk ids, if present.

    Callers that re-ingest a document (which assigns new SQLite chunk ids;
    see "Decision: ChromaDB Vector Persistence") are responsible for
    deleting the old chunk ids' vectors with this function before or after
    persisting the new ones.
    """
    if not chunk_ids:
        return
    collection.delete(ids=[str(chunk_id) for chunk_id in chunk_ids])


def get_chunk_vector_ids_for_document(collection: Collection, document_id: int) -> list[str]:
    """Return all Chroma vector ids currently stored for a document."""
    result = collection.get(where={"document_id": document_id})
    return result["ids"]


def _chunk_metadata(document_id: int, chunk: Chunk) -> dict[str, str | int]:
    metadata: dict[str, str | int] = {
        "document_id": document_id,
        "source_document": chunk.source_document,
        "token_count": chunk.token_count,
    }
    if chunk.page_number is not None:
        metadata["page_number"] = chunk.page_number
    if chunk.section_heading is not None:
        metadata["section_heading"] = chunk.section_heading
    return metadata
