# Architecture

This document captures the intended technical shape and boundaries for memQrag. It is not an implementation claim.

## Current Shape

The repository contains project rails plus a placeholder Python package scaffold under
`memQrag/`. Most submodules below are still empty, documented packages with no runtime behavior;
see `docs/PRODUCT_TIMELINE.md` for which phase fills each one in. The one exception is
`memQrag/api`, which now has a real FastAPI app (`memQrag.api.app.create_app`) exposing a `GET
/health` liveness endpoint; no business endpoints exist yet.

A `ui/` demo UI shell also exists now (Vite + React + TypeScript + Tailwind CSS v4). It renders a
static placeholder page with no product workflow logic and makes no API calls; see "Decision:
Frontend Tooling Baseline For The `ui/` Demo" in `docs/DECISIONS.md`.

A root `docker-compose.yml` now wires the `api`, `ui`, and `chroma` services together with local
bind-mounted volumes; see "Decision: Docker Compose Topology For The Local Full Stack" in
`docs/DECISIONS.md`. This has been validated by config review and YAML syntax checks, not yet by
a live `docker compose up --build` run (Docker was unavailable in the authoring environment); do
not claim a verified one-command setup until that run has actually happened, per the "Boundaries"
section below.

GitHub Actions CI (`.github/workflows/ci.yml`) and matching local scripts (`scripts/check.sh`,
`scripts/check.ps1`) now run backend lint/format/tests and frontend lint/build on every push and
pull request; see "Decision: CI And Local Check Scripts" in `docs/DECISIONS.md`. This completes
Phase 1's exit criteria.

Phase 2 (Document Ingestion Pipeline) is underway. `memQrag/ingestion/contracts.py` defines the
file intake contract: `SupportedFileType` (PDF, DOCX, TXT, MARKDOWN), the `RawDocument` dataclass,
and `intake_document()`/`detect_file_type()` validation functions; see "Decision: File Intake
Contract Design" in `docs/DECISIONS.md`. `memQrag/ingestion/extraction.py` now turns a
`RawDocument` into an `ExtractedDocument` (source document, created/modified dates, and a list of
`ExtractedSegment`s with page number and/or section heading where the format supports it), via
per-format adapters (`pypdf` for PDF, `python-docx` for DOCX, stdlib decoding for TXT/Markdown);
see "Decision: Text Extraction Adapter Behavior" in `docs/DECISIONS.md`. `memQrag/ingestion/chunking.py`
now turns an `ExtractedDocument` into `Chunk`s: sentences within each segment are embedded (via
`memQrag/ingestion/embeddings.py`, using `fastembed`'s `BAAI/bge-small-en-v1.5` model) and grouped
at semantic-similarity breakpoints, then merged below 200 tokens and split above 800 tokens; see
"Decision: Sentence Embedding Model For Semantic Chunking" and "Decision: Semantic Chunking
Algorithm" in `docs/DECISIONS.md`. `memQrag/ingestion/storage.py` now persists `ExtractedDocument`/
`Chunk` data into a SQLite `documents`/`chunks` schema (plain `sqlite3`, no ORM), with
`persist_ingested_document()` as the combined write path and `get_document_by_filename()`/
`get_chunks_for_document()` as read paths; see "Decision: SQLite Persistence For Document And
Chunk Metadata" in `docs/DECISIONS.md`. `memQrag/ingestion/vector_store.py` now persists one
Chroma vector per `Chunk` (embedded via the same `embed_sentences` model used for chunking),
keyed by `str(chunk_id)` so a vector resolves back to its SQLite chunk row without a separate
mapping table; see "Decision: ChromaDB Vector Persistence" in `docs/DECISIONS.md`.
`tests/test_ingestion_pipeline.py` now exercises all five modules together end-to-end against a
small fictional fixture per supported file type, directly asserting all three Phase 2 exit
criteria; see "Decision: End-To-End Ingestion Fixture Tests" in `docs/DECISIONS.md`. This
completes Phase 2. No orchestration/pipeline module exists yet — the API layer (Phase 7) will call
the per-module functions directly, the same way the new tests do, until a real orchestration need
arises.

Phase 3 (Hybrid Retrieval Engine) is underway. `memQrag/retrieval/dense.py` now queries the
`memqrag_chunks` Chroma collection: `dense_retrieve(collection, query, top_k=20)` embeds the query
with the same `embed_sentences` model used for chunk storage and returns up to `top_k`
`DenseRetrievalResult`s ranked by cosine similarity, built entirely from Chroma's stored metadata
and document text. `memQrag/ingestion/vector_store.py`'s `get_collection()` now creates the
collection with `hnsw:space="cosine"` so a query's `1 - distance` is a real cosine similarity,
matching the confidence thresholds below; see "Decision: Dense Retrieval, Query Embedding, And
Chroma Distance Space" in `docs/DECISIONS.md`. `memQrag/retrieval/sparse.py` now adds BM25 sparse
retrieval: `sparse_retrieve(collection, query, top_k=20)` reads every chunk's text directly from
the same `memqrag_chunks` collection, scores it with `rank_bm25`'s `BM25Okapi`, and excludes
chunks sharing no token with the query (not the same as filtering on a positive score — BM25's IDF
can go negative for a token common across a small corpus); see "Decision: BM25 Sparse Retrieval"
in `docs/DECISIONS.md`. `memQrag/retrieval/fusion.py` now combines both ranked lists with
Reciprocal Rank Fusion (`reciprocal_rank_fusion`, `k=60`): each chunk's RRF score sums `1 / (k +
rank)` over every input ranking it appears in, so a bounded cosine similarity and an unbounded
BM25 score never need to be normalized against each other; the result carries `dense_score` when
present, `sparse_rank` when present, and the fused rank/score. See "Decision: Reciprocal Rank
Fusion For Dense And Sparse Results" in `docs/DECISIONS.md`. `memQrag/retrieval/rerank.py` now
scores the fused candidates against the query with a cross-encoder
(`memQrag/retrieval/cross_encoder.py`'s `score_pairs`, wrapping fastembed's
`Xenova/ms-marco-MiniLM-L-6-v2` ONNX model) and truncates to the final top-5 — the only step in
this flow that truncates its output, per the retrieval flow below. See "Decision: Cross-Encoder
Reranking Model And Final Top-5 Selection" in `docs/DECISIONS.md`. `memQrag/retrieval/confidence.py`
now labels each final chunk HIGH/MEDIUM/LOW from `dense_score` using the exact cosine thresholds
in step 9 below (`confidence_for_dense_score`, `assign_confidence`); a chunk with no `dense_score`
(sparse-only) is always LOW. See "Decision: Confidence Scoring Thresholds And Sparse-Only
Handling" in `docs/DECISIONS.md`. `tests/test_retrieval_pipeline.py` now exercises all five
retrieval modules together end-to-end against a small fictional 7-chunk fixture corpus, directly
asserting both Phase 3 exit criteria; see "Decision: End-To-End Retrieval Fixture Tests" in
`docs/DECISIONS.md`. This completes Phase 3. No retrieval orchestration/pipeline module exists yet
— the API layer (Phase 7) will call the per-module functions directly, the same way the new tests
do, until a real orchestration need arises.

Phase 4 (Persistent Memory System) is underway. `memQrag/memory/session.py` adds a
`session_memory` table (`session_id`, `query`, `retrieved_chunk_ids` — a JSON-encoded list, not a
foreign key, since `chunks.id` rows get replaced wholesale on re-ingestion — `usefulness_flag`,
`created_at`) to the same shared SQLite database `memQrag/ingestion/storage.py` uses:
`connect()` opens that shared file and ensures both modules' tables exist.
`record_session_query()`/`set_usefulness()`/`get_session_memory()` are plain write/read
functions; no memory-informed boosting logic exists yet. See "Decision: SQLite Schema For
Session Memory Records" in `docs/DECISIONS.md`.

The planned runtime shape is:

- `memQrag/ingestion`: document intake, text extraction, semantic chunking, chunk metadata assembly, and persistence coordination.
- `memQrag/retrieval`: ChromaDB dense retrieval, BM25 sparse retrieval, Reciprocal Rank Fusion, cross-encoder reranking, and confidence scoring.
- `memQrag/memory`: SQLite-backed session memory, long-term memory, memory-informed retrieval boosts, memory decay, and staleness review signals.
- `memQrag/agent`: query analysis, multi-hop decomposition, comparative retrieval orchestration, response synthesis, source citation assembly, and low-confidence handling.
- `memQrag/api`: FastAPI app, request and response schemas, endpoint handlers, and dependency wiring.
- `ui`: React + Tailwind demo interface.

## Data Stores

- ChromaDB stores chunk embeddings and vector-search records.
- SQLite stores document metadata, chunk metadata, session memory, long-term memory, staleness state, and contradiction records.

## Planned Data Model

Core entities:

- Document: source document name, file type, created date, last modified date, ingest timestamp, staleness status.
- Chunk: chunk id, document id, page number, section heading, text excerpt, token count, embedding reference.
- Session memory: query, retrieved chunks, usefulness flag, session id, timestamp.
- Long-term memory: query embedding, best document ids, success count, last used, hit rate, decay weight.
- Retrieval result: chunk id, dense score, sparse rank, fused rank, rerank score, confidence level, applied memory boost.
- Conflict: entity, claim A, claim B, source chunk references, detection timestamp, review status.

## Retrieval Flow

1. Analyze the query type as FACTUAL, COMPARATIVE, MULTI-HOP, or UNKNOWN.
2. Check long-term memory for similar successful queries.
3. Run dense retrieval against ChromaDB for top-20 candidates.
4. Run BM25 sparse retrieval for top-20 candidates.
5. Fuse both rankings with Reciprocal Rank Fusion.
6. Apply memory-informed boosts where appropriate.
7. Rerank top candidates with a cross-encoder.
8. Select final top-5 chunks.
9. Assign confidence using cosine similarity thresholds:
   - HIGH: greater than 0.85
   - MEDIUM: 0.65 to 0.85
   - LOW: less than 0.65
10. Detect stale and contradictory evidence.
11. Generate a cited response with explicit confidence and warnings.

## API Boundary

Implemented today:

- `GET /health`: unprefixed infrastructure liveness probe. Not a business endpoint; see
  "Decision: Unprefixed `/health` Infrastructure Endpoint" in `docs/DECISIONS.md`.

Planned business endpoints (Phase 7):

- `POST /api/ingest`: upload and process documents.
- `POST /api/query`: ask a question and receive answer metadata.
- `GET /api/memory/session`: view current session memory.
- `GET /api/memory/longterm`: view persistent memory store.
- `GET /api/documents`: list ingested documents with staleness flags.
- `GET /api/conflicts`: list detected document contradictions.

## UI Boundary

Implemented today: a static placeholder shell (`ui/src/App.tsx`) with no product workflow logic
and no API calls. Everything below is planned for Phase 8.

The demo UI should prioritize the side-by-side comparison:

- Left panel: standard stateless RAG answer.
- Right panel: memQrag answer using persistent memory and trust signals.
- Shared input: one question drives both panels.
- Supporting surfaces: upload panel, citations, memory panel, staleness banner, contradiction alert.

## External Integrations

The specific embedding model, reranker, and LLM provider are not selected yet. Any provider choice must be recorded in `docs/DECISIONS.md` before implementation.

## Boundaries

- Do not add authentication or hosted deployment before the local MVP works.
- Do not store hidden memory that users cannot inspect through the API or UI.
- Do not silently suppress stale or contradictory sources.
- Do not claim a one-command setup until Docker Compose has been implemented and verified.
- Do not add real company policy documents to the repository.

## Decisions

Important architecture decisions should be recorded in [`docs/DECISIONS.md`](./DECISIONS.md).

## Out Of Scope

- Multi-tenant SaaS architecture.
- Automatic source document rewriting.
- Distributed retrieval infrastructure.
- Fine-tuning or model training.
- Compliance certification.
