"""Retrieval module boundary.

Planned responsibility, per docs/ARCHITECTURE.md: ChromaDB dense retrieval,
BM25 sparse retrieval, Reciprocal Rank Fusion, cross-encoder reranking, and
confidence scoring.

Implemented so far (Phase 3 of docs/PRODUCT_TIMELINE.md):
- dense retrieval in `memQrag.retrieval.dense` (`dense_retrieve`,
  `DenseRetrievalResult`), querying the `memqrag_chunks` Chroma collection
  by cosine similarity;
- sparse retrieval in `memQrag.retrieval.sparse` (`sparse_retrieve`,
  `SparseRetrievalResult`), scoring the same collection's chunk text with
  BM25.

Fusion, reranking, and confidence scoring do not exist yet.
"""
