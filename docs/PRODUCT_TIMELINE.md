# Product Timeline

This file is the source of truth for progress.

Rules:

1. Start every PR by reading this file.
2. Work on the first unchecked item unless the user explicitly overrides it.
3. Keep each item PR-sized.
4. If no PR workflow exists yet, leave items unchecked and report the next item.
5. After opening a PR, change exactly the completed item from `[ ]` to `[x]`.
6. Add the PR number at the end of the completed item, for example `(#12)`.
7. Leave the next unchecked item visible in the final summary.

## Phase 0: Project Rails

Goal:

> Make memQrag understandable before building product features.

Expected PRs:

- [x] Add README, project blueprint, roadmap, architecture, decisions log, development cycle, and agent instructions. (#1)
- [x] Add repository metadata baseline, including `.gitignore`, license decision, and contribution expectations. (#2)
- [x] Choose and document the first implementation PR order. (#3)

Exit criteria:

- A new contributor can understand the product goal.
- An agent can find the next task without asking.
- PRs have a verification standard.
- Product feature work is deferred until rails are accepted.

## Phase 1: Foundation Scaffold

Goal:

> Create the smallest runnable full-stack shape without implementing the full RAG pipeline.

Implementation order:

The PRs below must land in the listed order. Each PR depends on the artifact produced by the
previous one (package scaffold before the API that lives in it, API and UI before the Docker
Compose that wires them together, backend tests and a frontend build target before the check
scripts that run them). See "Decision: Phase 1 Implementation PR Order" in
[`docs/DECISIONS.md`](./DECISIONS.md) for the full rationale. Do not reorder this list without
adding a new decision entry.

Expected PRs:

- [x] Scaffold Python package layout under `memQrag/` with placeholder module boundaries only. (#4)
- [x] Scaffold FastAPI app with health endpoint and test harness. (#5)
- [x] Scaffold React + Tailwind demo UI shell with no product workflow logic. (#6)
- [x] Add Docker Compose for API, UI, ChromaDB, and local volumes. (#7)
- [x] Add CI or local check scripts for backend tests, frontend build, linting, and formatting. (#8)

Exit criteria:

- The project runs locally.
- Backend and frontend smoke checks pass.
- Module boundaries match `docs/ARCHITECTURE.md`.

## Phase 2: Document Ingestion Pipeline

Goal:

> Process supported documents into semantically meaningful chunks with metadata.

Expected PRs:

- [x] Add file intake contracts for PDF, DOCX, TXT, and Markdown. (#9)
- [x] Implement text extraction adapters with metadata capture for source document, page number, section heading, created date, and last modified date. (#10)
- [x] Implement semantic chunking using sentence embeddings with merge-below-200-token and split-above-800-token behavior. (#11)
- [x] Persist chunk metadata in SQLite. (#12)
- [x] Persist vector records in ChromaDB. (#13)
- [x] Add ingestion tests using small fixture documents. (#14)

Exit criteria:

- Supported files ingest successfully.
- Chunk metadata can be queried from SQLite.
- Vector references resolve back to stored chunk metadata.

## Phase 3: Hybrid Retrieval Engine

Goal:

> Retrieve and rank candidate chunks with dense search, sparse search, fusion, reranking, and confidence scoring.

Expected PRs:

- [x] Implement ChromaDB dense retrieval with top-20 results. (#15)
- [x] Implement BM25 sparse retrieval with top-20 results. (#16)
- [x] Implement Reciprocal Rank Fusion for dense and sparse results. (#17)
- [x] Add cross-encoder reranking of top-20 candidates to final top-5. (#18)
- [ ] Add confidence scoring with HIGH, MEDIUM, and LOW thresholds.
- [ ] Add retrieval tests for ranking, fusion, reranking, and confidence labels.

Exit criteria:

- Retrieval returns ranked chunks with source references and confidence.
- Tests prove fusion and threshold behavior.

## Phase 4: Persistent Memory System

Goal:

> Make retrieval improve over time through session and long-term memory.

Expected PRs:

- [ ] Add SQLite schema for session memory records.
- [ ] Add SQLite schema for long-term memory records.
- [ ] Implement memory-informed retrieval boosts for similar past queries.
- [ ] Implement memory decay for memories older than 30 days with low hit rate.
- [ ] Implement configurable staleness detection for frequently retrieved documents older than 90 days.
- [ ] Add memory and staleness tests.

Exit criteria:

- Similar queries can boost previously successful documents.
- Stale frequently retrieved documents are surfaced for review.
- Old low-value memory has reduced retrieval influence.

## Phase 5: Contradiction Detection

Goal:

> Surface conflicting source claims instead of silently resolving them.

Expected PRs:

- [ ] Define contradiction record model and SQLite persistence.
- [ ] Implement entity and claim comparison path for retrieved chunks.
- [ ] Flag conflicting factual claims in query responses.
- [ ] Add `GET /api/conflicts` read path.
- [ ] Add tests for intentional contradictory fixture content.

Exit criteria:

- Contradictory retrieved chunks are visible in API responses.
- Stored conflicts can be listed for human review.

## Phase 6: Agentic Query Orchestration

Goal:

> Route queries by type and generate confidence-gated cited answers.

Expected PRs:

- [ ] Implement query classification for FACTUAL, COMPARATIVE, MULTI-HOP, and UNKNOWN.
- [ ] Implement multi-hop decomposition, per-subquery retrieval, and synthesis.
- [ ] Implement comparative retrieval across document sets with structured comparison output.
- [ ] Implement confidence-gated answer formatting.
- [ ] Ensure every answer includes source document name, chunk reference, and confidence level.
- [ ] Add orchestration tests for factual, comparative, multi-hop, unknown, low-confidence, and conflict cases.

Exit criteria:

- Query behavior changes based on query class.
- Low-confidence and conflicting answers are explicit.
- Citations are present on every answer.

## Phase 7: API Surface

Goal:

> Expose the core system through stable FastAPI endpoints.

Expected PRs:

- [ ] Add `POST /api/ingest`.
- [ ] Add `POST /api/query`.
- [ ] Add `GET /api/memory/session`.
- [ ] Add `GET /api/memory/longterm`.
- [ ] Add `GET /api/documents`.
- [ ] Add `GET /api/conflicts`.
- [ ] Add API contract tests and example responses.

Exit criteria:

- All requested endpoints exist and return documented shapes.
- API tests pass locally.

## Phase 8: Demo UI

Goal:

> Make the memory advantage visible through a polished React demo.

Expected PRs:

- [ ] Add chat interface and document upload panel.
- [ ] Add response rendering with answer, confidence badge, citations, and excerpts.
- [ ] Add memory panel showing session learnings.
- [ ] Add staleness alert banner.
- [ ] Add contradiction alert treatment.
- [ ] Add side-by-side standard RAG vs memQrag split panel.
- [ ] Add frontend build checks and UI smoke tests.

Exit criteria:

- The split panel clearly shows standard RAG on the left and memQrag on the right.
- Memory, staleness, contradiction, confidence, and citation states are visible.
- UI build passes.

## Phase 9: Demo Dataset And Walkthrough

Goal:

> Provide a compelling local demo with fictional policies, intentional contradictions, and outdated information.

Expected PRs:

- [ ] Add 10 fictional company policy Markdown files.
- [ ] Include intentional contradictions across selected policy files.
- [ ] Include intentionally outdated policy metadata or content.
- [ ] Add scripted demo questions that trigger memory, staleness, and contradiction behavior.
- [ ] Update README with one-command setup and demo walkthrough after implementation is verified.

Exit criteria:

- A fresh local run can demonstrate memQrag without external documents.
- Staleness and contradiction alerts fire immediately during the walkthrough.

## Phase 10: Production Hardening

Goal:

> Improve reliability, observability, and maintainability after the MVP works.

Expected PRs:

- [ ] Add structured logging and request IDs.
- [ ] Add error taxonomy and API error responses.
- [ ] Add database migration workflow.
- [ ] Add configurable providers for embeddings, reranking, and LLM calls.
- [ ] Add performance checks for ingestion and retrieval.
- [ ] Add security and privacy review docs.

Exit criteria:

- The system has credible production-readiness checks.
- Operational risks are documented and tested where practical.

## Next Item

The next unchecked item is:

- [ ] Add confidence scoring with HIGH, MEDIUM, and LOW thresholds.
