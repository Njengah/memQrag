"""BM25 sparse retrieval (Phase 3 PR 2).

Scores every chunk in the `memqrag_chunks` Chroma collection (see
`memQrag.ingestion.vector_store`) against a query using BM25 (Okapi
variant, via `rank_bm25`), and returns the top-k non-zero-scoring chunks.
See docs/DECISIONS.md ("BM25 Sparse Retrieval") for why the corpus is read
from Chroma rather than SQLite, and why the tokenizer is a simple
lowercase word-boundary regex.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from chromadb.api.models.Collection import Collection
from rank_bm25 import BM25Okapi

SPARSE_TOP_K = 20

_TOKEN_RE = re.compile(r"\w+")


@dataclass(frozen=True)
class SparseRetrievalResult:
    """One BM25 hit, self-contained from Chroma's stored metadata.

    Shaped identically to `memQrag.retrieval.dense.DenseRetrievalResult`
    (so Phase 3 PR 3's fusion step can treat both as ranked candidate
    lists), but kept as its own type rather than an alias, since `score`'s
    units differ (raw BM25 score here, cosine similarity there) and the
    two could diverge further later.
    """

    chunk_id: int
    document_id: int
    score: float
    text: str
    source_document: str
    page_number: int | None
    section_heading: str | None


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def sparse_retrieve(
    collection: Collection,
    query: str,
    top_k: int = SPARSE_TOP_K,
) -> list[SparseRetrievalResult]:
    """Return up to `top_k` chunks ranked by BM25 score against `query`.

    `score` is a raw BM25 score (unbounded, corpus-size-dependent), not a
    similarity in `[0, 1]` or `[-1, 1]`; do not compare it directly against
    `dense_retrieve`'s cosine similarity scores. Chunks sharing no token
    with the query are excluded, since they are not a real sparse match.
    This is *not* the same as filtering on `score > 0`: BM25's IDF term
    goes negative for tokens common across the whole corpus (a real
    possibility with a small demo corpus), so a genuinely overlapping
    chunk can still score negative; `BM25Okapi.get_scores()` scores every
    chunk regardless, so the overlap check is done separately here.
    """
    if not query.strip():
        raise ValueError("query must not be empty.")

    corpus = collection.get(include=["metadatas", "documents"])
    chunk_ids = corpus["ids"]
    if not chunk_ids:
        return []

    documents = corpus["documents"]
    metadatas = corpus["metadatas"]
    tokenized_documents = [_tokenize(document) for document in documents]
    query_tokens = set(_tokenize(query))

    bm25 = BM25Okapi(tokenized_documents)
    scores = bm25.get_scores(list(query_tokens))

    ranked = sorted(
        zip(chunk_ids, scores, metadatas, documents, tokenized_documents, strict=True),
        key=lambda item: item[1],
        reverse=True,
    )

    results = [
        SparseRetrievalResult(
            chunk_id=int(chunk_id),
            document_id=metadata["document_id"],
            score=float(score),
            text=document_text,
            source_document=metadata["source_document"],
            page_number=metadata.get("page_number"),
            section_heading=metadata.get("section_heading"),
        )
        for chunk_id, score, metadata, document_text, tokens in ranked
        if query_tokens & set(tokens)
    ]
    return results[:top_k]
