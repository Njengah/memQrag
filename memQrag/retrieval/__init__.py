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
  BM25;
- Reciprocal Rank Fusion in `memQrag.retrieval.fusion`
  (`reciprocal_rank_fusion`, `FusedRetrievalResult`), combining the two
  ranked lists above into one;
- cross-encoder reranking in `memQrag.retrieval.rerank` (`rerank`,
  `RerankedRetrievalResult`), scoring the fused candidates against the
  query with `memQrag.retrieval.cross_encoder.score_pairs` and truncating
  to the final top-5;
- confidence scoring in `memQrag.retrieval.confidence` (`assign_confidence`,
  `confidence_for_dense_score`, `ConfidenceLevel`, `ScoredRetrievalResult`),
  labeling each final chunk HIGH/MEDIUM/LOW from its dense cosine
  similarity.

This completes Phase 3's retrieval stages; only the cross-module retrieval
test suite (Phase 3's last tracker item) remains.
"""
