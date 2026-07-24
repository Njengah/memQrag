"""ChromaDB dense retrieval (Phase 3 PR 1).

Embeds a query with the same model used to store chunk vectors
(`memQrag.ingestion.embeddings.embed_sentences`), then queries the
`memqrag_chunks` collection (see `memQrag.ingestion.vector_store`) for the
top-k nearest chunks by cosine similarity. See docs/DECISIONS.md ("Dense
Retrieval, Query Embedding, And Chroma Distance Space") for why query and
chunk embeddings must share one model, and why the collection is created
with cosine distance space.
"""

from __future__ import annotations

from dataclasses import dataclass

from chromadb.api.models.Collection import Collection

from memQrag.ingestion.embeddings import embed_sentences

DENSE_TOP_K = 20


@dataclass(frozen=True)
class DenseRetrievalResult:
    """One dense-retrieval hit, self-contained from Chroma's stored metadata."""

    chunk_id: int
    document_id: int
    score: float
    text: str
    source_document: str
    page_number: int | None
    section_heading: str | None


def dense_retrieve(
    collection: Collection,
    query: str,
    top_k: int = DENSE_TOP_K,
) -> list[DenseRetrievalResult]:
    """Return up to `top_k` chunks ranked by cosine similarity to `query`.

    Results are ordered most to least similar, matching Chroma's own query
    order. `score` is a cosine similarity in `[-1, 1]` (`1 - distance`,
    since the collection is created with `hnsw:space="cosine"`).
    """
    if not query.strip():
        raise ValueError("query must not be empty.")

    query_embedding = embed_sentences([query])[0]
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["metadatas", "documents", "distances"],
    )

    chunk_ids = result["ids"][0]
    distances = result["distances"][0]
    metadatas = result["metadatas"][0]
    documents = result["documents"][0]

    return [
        DenseRetrievalResult(
            chunk_id=int(chunk_id),
            document_id=metadata["document_id"],
            score=1 - distance,
            text=document_text,
            source_document=metadata["source_document"],
            page_number=metadata.get("page_number"),
            section_heading=metadata.get("section_heading"),
        )
        for chunk_id, distance, metadata, document_text in zip(
            chunk_ids, distances, metadatas, documents, strict=True
        )
    ]
