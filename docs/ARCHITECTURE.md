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
Chunk Metadata" in `docs/DECISIONS.md`. Persistence into ChromaDB does not exist yet.

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
