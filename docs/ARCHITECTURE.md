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
Session Memory Records" in `docs/DECISIONS.md`. `memQrag/memory/long_term.py` adds a
`long_term_memory` table (`query`, `best_document_ids` — also a JSON-encoded list, kept
consistent with session memory's shape even though `documents.id` is stable enough that a
foreign key would be safe here — `success_count`, `hit_rate`, `decay_weight`, `last_used`) to the
same shared database; `connect()` extends `memory.session.connect()`'s chain. `long_term_memory`
now also has a `query_embedding` column (JSON-encoded, added by this PR) and a `match_count`
column (the `hit_rate` denominator); `update_long_term_memory()` is still a plain field setter, not
the boosting/decay formulas themselves. See "Decision: SQLite Schema For Long-Term Memory Records"
in `docs/DECISIONS.md`. `memQrag/memory/boost.py` now implements retrieval flow steps 2 and 6:
`find_similar_successful_memory()` scores an incoming query's embedding against every
`long_term_memory` row by brute-force cosine similarity and returns the most similar one that both
clears a similarity threshold and has a track record of being useful; `apply_memory_boost()` adds a
fixed boost to the `rrf_score` of every fused result whose document was one of that memory's best
matches and re-sorts, returning `BoostedRetrievalResult` (the first result type carrying
`applied_memory_boost`). `remember_query_outcome()` and `promote_session_memory_to_long_term()` are
the write path: they turn `session_memory` rows with feedback into `long_term_memory` rows,
resolving `retrieved_chunk_ids` to their owning `document_id`s via a new
`memQrag.ingestion.storage.get_chunk_by_id()`, and merge near-duplicate queries into one
reinforced row instead of creating duplicates. See "Decision: Memory-Informed Retrieval Boosts For
Similar Past Queries" in `docs/DECISIONS.md`. Nothing calls `promote_session_memory_to_long_term()`
yet, and `apply_memory_boost()` is not yet wired between `retrieval.fusion` and `retrieval.rerank`
in an actual pipeline — both are deferred to Phase 4's final PR, mirroring how Phase 3 only stitched
its stages together in its own last PR.

`memQrag/memory/decay.py` now gives `long_term_memory.decay_weight` an actual effect:
`is_decay_eligible()` flags records that are both old (no match in 30+ days, measured from
`last_used`) and low-value (low `hit_rate`); `decay_weight_for()` recomputes the weight from
scratch each time (not eligible -> full strength `1.0`; eligible -> shrinks toward a `0.1` floor
the longer it stays eligible), so repeated decay sweeps are idempotent and a reused memory is
restored to full strength rather than staying stuck at a decayed value; `apply_memory_decay()`
persists that recomputed weight for every record. `memQrag.memory.boost.apply_memory_boost()` now
multiplies its boost by the matched memory's `decay_weight`, so old, low-value memories influence
ranking progressively less over time instead of either the full boost or none. See "Decision:
Memory Decay For Old, Low-Hit-Rate Memories" in `docs/DECISIONS.md`. Like
`promote_session_memory_to_long_term()`, nothing calls `apply_memory_decay()` on a schedule yet.

`memQrag/memory/staleness.py` now implements configurable staleness detection for frequently
retrieved documents: `documents.staleness_status` (`FRESH`/`STALE`, via
`DocumentStalenessStatus`) was added to the shared SQLite schema;
`effective_document_date()` / `count_document_retrievals()` / `is_stale()` decide when a document
is both old (no fresher content in 90+ days, preferring `last_modified_date` then `created_date`
then `ingested_at`) and frequently retrieved (its chunks appear in at least 5 recorded
`session_memory` queries across every session); `detect_stale_documents()` recomputes and
persists that status for every document. Re-ingestion via `save_document()` resets the status to
`FRESH`. See "Decision: Configurable Staleness Detection For Frequently Retrieved Documents" in
`docs/DECISIONS.md`. Like boost/decay, nothing calls `detect_stale_documents()` on a schedule yet.

`tests/test_memory_pipeline.py` now stitches session / long-term / boost / decay / staleness
together against one shared SQLite fixture and directly asserts all three Phase 4 exit criteria
(similar-query boosts, stale-document surfacing, reduced influence from old low-value memory).
`applied_memory_boost` stays on `BoostedRetrievalResult` only — propagating it through
rerank/confidence types is deferred until Phase 6/7 orchestration needs it. See "Decision:
End-To-End Memory And Staleness Fixture Tests" in `docs/DECISIONS.md`. This completes Phase 4.

Phase 5 (Contradiction Detection) is underway. `memQrag/conflicts/records.py` adds a `conflicts`
table (`entity`, `claim_a`, `claim_b`, `claim_a_chunk_ids` / `claim_b_chunk_ids` as JSON-encoded
lists — not foreign keys, since `chunks.id` rows get replaced on re-ingestion —
`detected_at`, `review_status` as `UNREVIEWED`/`REVIEWED`) to the same shared SQLite database;
`connect()` extends `memory.long_term.connect()`'s chain so one call still gets the full shared
schema. `record_conflict()` / `set_review_status()` / `get_conflict_by_id()` /
`get_all_conflicts()` are plain write/read functions. See "Decision: SQLite Schema For
Contradiction Records" in `docs/DECISIONS.md`. `memQrag/conflicts/compare.py` now implements
entity/claim comparison over retrieved chunks: `extract_claims` pulls quantitative factual
claims (known entity patterns + numeric values with units) from chunk text without an LLM;
`find_conflicting_claim_pairs` groups by entity and pairs distinct values from different
chunks; `detect_conflicts` persists new pairs via `record_conflict` (idempotent for the same
claim texts) and returns the conflicts found. Both opposing claims are stored side by side —
detection never picks a winner. See "Decision: Entity And Claim Comparison For Retrieved
Chunks" in `docs/DECISIONS.md`. `memQrag/conflicts/flagging.py` now wraps that detection for
query responses: `flag_conflicting_claims(conn, chunks)` returns
`ConflictFlaggedQueryEvidence` carrying the original chunks unchanged plus `ConflictWarning`s
that each hold both opposing claims (and helpers to see which chunk ids are involved). It does
not synthesize answer text or pick a winner — Phase 7's `POST /api/query` and Phase 8's
contradiction alert will serialize/display these warnings. See "Decision: Flag Conflicting
Factual Claims In Query Responses" in `docs/DECISIONS.md`. `GET /api/conflicts` is now
implemented in `memQrag/api/conflicts.py` (wired through `memQrag.api.app.create_app`, with DB
access via `memQrag.api.deps.get_db` → `conflicts.records.connect()`): it lists every stored
conflict with both opposing claims, most recently detected first. See "Decision: GET
/api/conflicts Read Path" in `docs/DECISIONS.md`. `tests/test_conflicts_pipeline.py` now
stitches detect -> flag -> list against one intentional fictional multi-document policy corpus
(one contradiction per supported entity pattern: return window, shipping time, warranty) built
as `ScoredRetrievalResult` chunks, and directly asserts both Phase 5 exit criteria (both-sided
warnings on query evidence; stored conflicts listable for human review, including via
`GET /api/conflicts`). Agreeing peers and non-claim filler must not invent false conflicts. See
"Decision: Intentional Contradictory Fixture Content Tests" in `docs/DECISIONS.md`. This
completes Phase 5.

The planned runtime shape is:

- `memQrag/ingestion`: document intake, text extraction, semantic chunking, chunk metadata assembly, and persistence coordination.
- `memQrag/retrieval`: ChromaDB dense retrieval, BM25 sparse retrieval, Reciprocal Rank Fusion, cross-encoder reranking, and confidence scoring.
- `memQrag/memory`: SQLite-backed session memory, long-term memory, memory-informed retrieval boosts, memory decay, and staleness review signals.
- `memQrag/conflicts`: contradiction record persistence, entity/claim comparison, and review-status surfacing.
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
- `GET /api/conflicts`: list stored contradiction records for human review (both claims always
  present). See "Decision: GET /api/conflicts Read Path" in `docs/DECISIONS.md`.

Planned business endpoints (Phase 7):

- `POST /api/ingest`: upload and process documents.
- `POST /api/query`: ask a question and receive answer metadata.
- `GET /api/memory/session`: view current session memory.
- `GET /api/memory/longterm`: view persistent memory store.
- `GET /api/documents`: list ingested documents with staleness flags.

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
