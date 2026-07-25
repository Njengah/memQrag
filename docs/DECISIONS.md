# Decisions

Use this file to stop agents from re-deciding the same architecture and product questions.

## Template

### Decision: Short Title

Date: YYYY-MM-DD

Status: proposed, accepted, rejected, or superseded.

Context:

- Why this decision is needed.
- What constraints matter.

Decision:

- What the project will do.

Consequences:

- What this enables.
- What tradeoffs it creates.
- What should not be changed without a new decision.

## Accepted Decisions

### Decision: Build memQrag As A Local-First Production-Shaped RAG System

Date: 2026-07-23

Status: accepted.

Context:

- The project needs to demonstrate production RAG behavior without starting with hosted SaaS complexity.
- The requested stack is Python, FastAPI, LangChain, ChromaDB, SQLite, React, Tailwind, and Docker.

Decision:

- Build local-first with Docker Compose as the primary setup target.
- Keep backend code under `memQrag/`.
- Keep the demo UI under `ui/`.
- Use ChromaDB for vector storage and SQLite for metadata, memory, staleness, and contradiction records.

Consequences:

- The MVP can be demonstrated locally before hosting decisions are made.
- Future hosted deployment work must preserve the local demo path.
- Changes to the stack require a new decision entry.

### Decision: Treat Persistent Memory As The Core Product Differentiator

Date: 2026-07-23

Status: accepted.

Context:

- The key product claim is that memQrag improves retrieval behavior using session and long-term memory.
- The demo must make the difference visible against stateless RAG.

Decision:

- Prioritize memory-informed retrieval and the side-by-side comparison mode.
- The UI must show standard RAG on the left and memQrag on the right for the same query.
- Session memory, long-term memory, staleness alerts, and contradiction alerts must be inspectable.

Consequences:

- UI work should not bury the comparison behind secondary navigation.
- Backend APIs must return enough metadata for the UI to explain why memQrag differs from standard RAG.
- Memory behavior needs deterministic tests before it is presented as a product advantage.

### Decision: Surface Uncertainty And Conflicts Explicitly

Date: 2026-07-23

Status: accepted.

Context:

- A trustworthy RAG system must not hide low confidence or contradictory sources.
- The user specifically requires low-confidence answers, stale document alerts, and contradiction warnings.

Decision:

- Every answer must include source citations and confidence.
- LOW confidence must be stated explicitly in the answer.
- Conflicting factual claims must surface both sources and flag the conflict instead of letting the LLM silently choose.

Consequences:

- Response schemas need explicit fields for confidence, citations, stale sources, and conflicts.
- UI states for low confidence, staleness, and contradictions are first-class product requirements.
- Future answer-generation changes must preserve these trust signals.

### Decision: License memQrag Under MIT

Date: 2026-07-23

Status: accepted.

Context:

- The repository metadata baseline task requires an explicit license decision before contribution
  expectations can be documented.
- memQrag is a local-first, non-hosted demo project intended to be freely usable, forkable, and
  inspectable by other engineers.
- No dependency in the planned stack (Python, FastAPI, LangChain, ChromaDB, SQLite, React,
  Tailwind, Docker) requires a specific reciprocal or copyleft license choice.

Decision:

- License memQrag under the MIT License.
- Record the license in a root `LICENSE` file with the repository owner as copyright holder.

Consequences:

- Contributors and users can freely use, modify, and redistribute memQrag with minimal friction.
- No copyleft obligations are imposed on downstream forks or embedders.
- Changing away from MIT later requires a new decision entry and explicit maintainer sign-off.

### Decision: Phase 1 Implementation PR Order

Date: 2026-07-23

Status: accepted.

Context:

- Phase 1 (Foundation Scaffold) in `docs/PRODUCT_TIMELINE.md` lists five expected PRs, but the
  tracker did not previously state the intended sequencing or the reasoning behind it.
- Rails work requires the implementation order to be chosen and documented before scaffolding
  starts, so PRs land in a dependency-safe, reviewable sequence instead of an ad hoc order.
- Each Phase 1 PR must stay small enough to review in one pass, per the PR size guidance in
  `docs/DEVELOPMENT_CYCLE.md`.

Decision:

- Implement Phase 1 in this fixed order:
  1. Backend Python package scaffold under `memQrag/` with placeholder module boundaries only
     (`ingestion`, `retrieval`, `memory`, `agent`, `api`). This establishes the package that every
     later backend PR imports into, with no runtime behavior yet.
  2. FastAPI health endpoint and backend test harness. This is the first runnable backend surface
     and depends on the package scaffold from step 1 already existing.
  3. React + Tailwind demo UI shell with no product workflow logic. This is an independent
     frontend artifact that only needs to exist as a buildable shell; it does not depend on
     backend behavior beyond knowing the health endpoint exists for later wiring.
  4. Docker Compose wiring for API, UI, ChromaDB, and local volumes. This depends on both the API
     (step 2) and UI (step 3) being real, buildable services before compose can wire them together.
  5. Local check scripts or CI for backend tests, frontend build, linting, and formatting. This
     depends on backend tests (step 2) and a frontend build target (step 3) already existing, so
     the scripts have real checks to run instead of placeholders.
- This order matches the existing bullet order already listed under Phase 1 in
  `docs/PRODUCT_TIMELINE.md`; that order is now authoritative rather than incidental.

Consequences:

- Each PR builds on a working artifact from the previous PR, keeping diffs small and avoiding
  speculative wiring to systems that do not exist yet.
- Docker Compose (step 4) and CI (step 5) will fail fast and obviously if earlier scaffolding is
  incomplete, since they depend directly on artifacts from steps 1 through 3.
- Reordering Phase 1 PRs later requires a new decision entry superseding this one.

### Decision: Python Packaging Baseline For The `memQrag` Package

Date: 2026-07-23

Status: accepted.

Context:

- The first Phase 1 PR introduces the `memQrag/` package scaffold and needs a way to make it
  importable and testable without committing to product dependencies (FastAPI, LangChain,
  ChromaDB) before they are actually used.
- A Python version floor and build backend need to be picked so later PRs do not each re-decide
  packaging basics.

Decision:

- Use `pyproject.toml` with the `setuptools` build backend and flat-layout package discovery
  (`memQrag*`) as the single source of packaging metadata; no `setup.py` or `setup.cfg`.
- Set `requires-python = ">=3.11"`.
- Keep `dependencies` empty until a PR actually needs a runtime dependency; add dev-only tooling
  (starting with `pytest`) under `[project.optional-dependencies].dev`.
- Place tests under a root-level `tests/` directory (not nested inside `memQrag/`), run via
  `python -m pytest` or an editable install (`pip install -e ".[dev]"`).

Consequences:

- Later Phase 1/2/3 PRs add their runtime dependencies (FastAPI, LangChain, ChromaDB, etc.) to
  `dependencies` in `pyproject.toml` as each is actually wired in, instead of front-loading an
  unused dependency list.
- Contributors run one standard command (`pip install -e ".[dev]"` then `pytest`) regardless of
  which backend module they are working on.
- Switching build backend or package layout later requires a new decision entry.

### Decision: Unprefixed `/health` Infrastructure Endpoint

Date: 2026-07-23

Status: accepted.

Context:

- The second Phase 1 PR adds the first real FastAPI endpoint: a liveness health check.
- `docs/ARCHITECTURE.md` plans all business endpoints under an `/api/...` prefix (`POST
  /api/ingest`, `POST /api/query`, etc.), which are implemented later in Phase 7.
- Docker Compose (the next Phase 1 PR) will need a stable, conventional path to configure a
  container health check against.

Decision:

- Expose the liveness probe at unprefixed `GET /health`, not `GET /api/health`.
- Keep `/health` free of business logic and authentication; it only reports process liveness.
- Introduce `memQrag/api/app.py` with a `create_app()` factory as the single place that assembles
  the FastAPI app and registers routers; future endpoint modules follow the same router-per-file
  pattern used by `memQrag/api/health.py`.

Consequences:

- `/health` is reserved and must not be reused for a future business endpoint.
- The upcoming Docker Compose PR can rely on `GET /health` returning `{"status": "ok"}` with a
  200 status code for its health check configuration.
- Adding real business endpoints in Phase 7 means adding new router modules and including them in
  `create_app()`, without touching `/health`.

### Decision: Frontend Tooling Baseline For The `ui/` Demo

Date: 2026-07-23

Status: accepted.

Context:

- The third Phase 1 PR scaffolds the demo UI shell under `ui/` and needs a concrete toolchain
  before any product UI work (Phase 8) begins.
- The stack decision already fixed React and Tailwind CSS; the specific build tool, language, and
  lint setup still needed to be chosen.

Decision:

- Use [Vite](https://vite.dev/) with the official `react-ts` template as the build tool and dev
  server for `ui/`.
- Use Tailwind CSS v4 via the official `@tailwindcss/vite` plugin (single `@import "tailwindcss";`
  in `src/index.css`; no separate `tailwind.config.js` or PostCSS config required).
- Keep the default `oxlint` linter that `create-vite` wires up rather than adding ESLint.
- The shell (`src/App.tsx`) contains no product workflow logic: no API calls, no forms, no state
  beyond proving the page renders. It only shows a static placeholder message and stack name.

Consequences:

- `npm run build` (`tsc -b && vite build`) and `npm run lint` (`oxlint`) are the standard frontend
  verification commands for every future UI PR.
- Phase 8 UI work (chat interface, upload panel, memory panel, split-panel comparison) builds on
  this shell without re-deciding build tooling.
- Switching build tool, styling approach, or linter later requires a new decision entry.

### Decision: Docker Compose Topology For The Local Full Stack

Date: 2026-07-23

Status: accepted.

Context:

- The fourth Phase 1 PR wires the API, UI, and ChromaDB into one local Docker Compose stack, per
  "Decision: Build memQrag As A Local-First Production-Shaped RAG System".
- SQLite has no schema yet (Phase 4), but the compose topology needs a stable place for it to
  land later without another infrastructure PR.
- `memQrag/api` already exposes `GET /health` (see "Decision: Unprefixed `/health` Infrastructure
  Endpoint"), which this PR relies on for the API container's health check.

Decision:

- `chroma` service uses the official `ghcr.io/chroma-core/chroma:latest` image with
  `IS_PERSISTENT=TRUE`, per Chroma's documented Docker Compose setup, healthchecked against its
  `/api/v2/heartbeat` endpoint.
- `api` service builds from a root-level `Dockerfile` (`python:3.12-slim`, installs the `memQrag`
  package via `pip install .`, runs `uvicorn memQrag.api.app:app`), healthchecked against
  `GET /health`, and depends on `chroma` being healthy before starting.
- `ui` service builds from `ui/Dockerfile`: a multi-stage build (`node:24-alpine` to run
  `npm run build`, then `nginx:stable-alpine` serving the built `dist/` output on port 80).
- Host port mapping: API on `8000`, ChromaDB on `8001` (avoids colliding with the API's `8000`),
  UI on `3000`.
- Persistence uses local bind mounts under a root `data/` directory (already covered by the
  existing `.gitignore` `data/` entry) rather than named Docker volumes: `./data/chroma` for
  ChromaDB and `./data/sqlite` for the future SQLite database. This keeps local-first data
  physically inspectable on the host, consistent with the project's local-first, non-hidden-state
  philosophy.

Consequences:

- `docker compose up --build` is the standard way to run the full local stack once this PR lands;
  README's one-command setup claim is only added after a real `docker compose up --build` run is
  verified (per `docs/ARCHITECTURE.md` "Boundaries"), which was not possible in the environment
  this PR was authored in (Docker is not installed there — see PR verification notes).
- Phase 4 (SQLite schema) can start writing to `/app/data` inside the `api` container without
  touching `docker-compose.yml`.
- Changing base images, port mappings, or the bind-mount-vs-named-volume choice later requires a
  new decision entry.

### Decision: CI And Local Check Scripts

Date: 2026-07-23

Status: accepted.

Context:

- The fifth and final Phase 1 PR needs to close the "backend tests, frontend build, linting, and
  formatting" tracker item with something contributors and CI both run consistently.
- Python had lint and format tooling missing; `ui/` already had `oxlint` (lint) and `tsc && vite
  build` (build) established as its standard checks by "Decision: Frontend Tooling Baseline For
  The `ui/` Demo".
- The repository has an active GitHub remote already used for every PR in this project, so GitHub
  Actions CI gives real, automatic verification on every push and pull request, not just when a
  contributor remembers to run checks locally.

Decision:

- Add `ruff` (lint + format) as the Python tooling, configured in `pyproject.toml`
  (`line-length = 100`, `target-version = "py311"`, lint rule sets `E`, `F`, `I`). Use `ruff
  format` as the formatter (no separate `black`).
- Do not add a separate frontend formatter (e.g. Prettier) in this PR; `oxlint` + the existing
  `tsc && vite build` remain the frontend's standard checks, per the prior frontend tooling
  decision. Revisit only if a real formatting inconsistency shows up.
- Add `.github/workflows/ci.yml` with two independent jobs, `backend` and `frontend`, running on
  every push to `main` and every pull request:
  - `backend`: `pip install -e ".[dev]"`, then `ruff check .`, `ruff format --check .`, `pytest`.
  - `frontend`: `npm install` in `ui/` (not `npm ci`; see below), then `npm run lint`, `npm run
    build`.
- Use `npm install` rather than `npm ci` for the frontend CI install step. `npm ci` requires
  `package-lock.json` to be perfectly in sync and failed in practice: Vite 8's Rolldown bundler
  and Tailwind's Oxide engine ship platform-specific optional native binaries (e.g.
  `@emnapi/core`, `@emnapi/runtime`), and `npm install` on this project did not consistently
  record every platform variant into the lockfile, so a clean-room `npm ci` (as GitHub Actions
  runs it) failed with "Missing: ... from lock file" even though a local `npm install` worked.
  `npm install` reconciles the lockfile instead of failing outright, which unblocks CI at the
  cost of `npm ci`'s stricter reproducibility guarantee.
- Add `scripts/check.sh` (POSIX) and `scripts/check.ps1` (PowerShell) that run the same checks
  locally in the same order, so a contributor gets identical results locally and in CI.

Consequences:

- Every future PR gets backend lint/format/tests and frontend lint/build checked automatically by
  CI, satisfying the Phase 1 exit criterion "Backend and frontend smoke checks pass."
- Contributors must run `ruff format .` (not just `ruff check .`) before committing Python changes,
  or CI's `ruff format --check .` step fails the PR.
- Frontend CI installs are slightly less strict than `npm ci` would be; if the optional-dependency
  lockfile drift is fixed upstream (npm, Vite/Rolldown, or Tailwind Oxide), switching back to
  `npm ci` should be revisited but does not require a new decision entry (it restores the
  originally intended behavior rather than changing it).
- Adding a frontend formatter, a type checker beyond `tsc`, or additional CI jobs (e.g. Docker
  Compose smoke tests once Docker is available in CI) requires a new decision entry.

### Decision: File Intake Contract Design

Date: 2026-07-23

Status: accepted.

Context:

- The first Phase 2 PR needs a shared contract that the text extraction adapters (Phase 2 PR 2)
  will consume, without implementing any actual extraction yet.
- `docs/PROJECT_BLUEPRINT.md` fixes the supported file types as PDF, DOCX, TXT, and Markdown, and
  explicitly lists "Building unsupported file types before PDF, DOCX, TXT, and Markdown are
  complete" as a non-goal.

Decision:

- Detect file type by filename extension only (no content/MIME sniffing) via
  `memQrag.ingestion.contracts.detect_file_type`. This is simple, predictable, and sufficient for
  a local demo where the user controls the uploaded files; content-sniffing can be added later as
  a new decision if extension spoofing becomes a real concern.
- `SupportedFileType` is a `str` enum with four members: `PDF`, `DOCX`, `TXT`, `MARKDOWN`. Both
  `.md` and `.markdown` extensions map to `MARKDOWN`.
- `RawDocument` is a frozen `dataclasses.dataclass`, not a Pydantic model. Ingestion domain
  contracts stay decoupled from the API layer's request/response schemas (Pydantic, via FastAPI);
  the `memQrag/api` layer will translate HTTP upload payloads into `RawDocument` instances when
  `POST /api/ingest` is implemented in Phase 7.
- `intake_document(filename, content)` is the single validated entry point later ingestion steps
  call; it raises `UnsupportedFileTypeError` (unsupported extension) or `ValueError` (empty
  filename/content) rather than silently accepting bad input.

Consequences:

- Text extraction adapters (Phase 2 PR 2) accept a `RawDocument` and dispatch on its `file_type`,
  without re-deriving file type detection themselves.
- Uploading a file with a spoofed extension (e.g. a `.txt` file that is actually a PDF) is not
  caught at this layer; that is an accepted limitation until a new decision changes it.
- Adding new supported file types, switching to content-sniffing, or changing `RawDocument`'s
  shape requires a new decision entry, since later ingestion PRs depend on this contract.

### Decision: Text Extraction Adapter Behavior

Date: 2026-07-24

Status: accepted.

Context:

- The second Phase 2 PR turns a validated `RawDocument` (from "Decision: File Intake Contract
  Design") into extracted text plus the metadata `docs/PRODUCT_TIMELINE.md` calls for: source
  document, page number, section heading, created date, and last modified date.
- The four supported formats (PDF, DOCX, TXT, Markdown) have very different native structure:
  PDF has pages but no reliable general heading markup; DOCX has paragraph styles but no fixed
  page boundaries outside a rendering engine; TXT has neither; Markdown has ATX headings but no
  pages.
- `RawDocument` only carries filename and in-memory bytes, not a filesystem path, so OS-level
  file timestamps are not available to this layer.

Decision:

- Add `pypdf` (PDF reading) and `python-docx` (DOCX reading) as runtime dependencies in
  `pyproject.toml`. Both are pure-Python-distributed, permissively licensed, and already the de
  facto standard choice for these formats without pulling in a heavier OCR/rendering stack.
- Implement one adapter function per `SupportedFileType` in `memQrag/ingestion/extraction.py`,
  dispatched by `extract_text(document: RawDocument) -> ExtractedDocument` via a
  `SupportedFileType -> Callable` lookup table:
  - PDF: one `ExtractedSegment` per page, with `page_number` set and `section_heading` left
    unset (no general-purpose PDF heading detection in this PR). `created_date` /
    `last_modified_date` come from the PDF Info dictionary (`PdfReader.metadata`) when present,
    else `None`.
  - DOCX: one `ExtractedSegment` per run of paragraphs between two paragraphs styled
    `"Heading *"`; `section_heading` is set to the heading text, `page_number` stays unset.
    `created_date` / `last_modified_date` come from `core_properties.created` /
    `.modified`, else `None`.
  - TXT: a single `ExtractedSegment` holding the whole decoded file; no page number or heading;
    no embedded dates (`None` / `None`).
  - Markdown: one `ExtractedSegment` per ATX (`#`...`######`) heading section, `section_heading`
    set to the heading text (or `None` for content before the first heading); no embedded dates.
- `ExtractedDocument` and `ExtractedSegment` are frozen dataclasses (matching `RawDocument`'s
  precedent), not Pydantic models.
- Test fixtures for PDF and DOCX are built in-memory at test time (a hand-assembled minimal PDF
  byte stream, and `python-docx`'s own `Document` API), not checked-in binary fixture files, to
  keep the test suite plain-text and self-contained.

Consequences:

- Semantic chunking (Phase 2 PR 3) consumes `ExtractedDocument.segments` as its input units; it
  must not assume every segment has a page number or heading, since that varies by format.
- No heading detection exists for PDF in this PR; if a demo document needs PDF section headings
  later, that requires a new decision (e.g. font-size heuristics or a layout-aware library).
- TXT and Markdown documents will always have `created_date`/`last_modified_date` set to `None`
  from this layer; if the API layer (Phase 7) has access to upload-time or filesystem timestamps,
  it may attach those separately without changing this module's contract.
- Adding OCR, other file formats, or changing the per-format segmentation strategy requires a new
  decision entry, since chunking and persistence build on this shape.

### Decision: Sentence Embedding Model For Semantic Chunking

Date: 2026-07-24

Status: accepted.

Context:

- The third Phase 2 PR needs to embed sentences to detect semantic breakpoints, per
  `docs/PRODUCT_TIMELINE.md` ("Implement semantic chunking using sentence embeddings").
- `docs/ARCHITECTURE.md` ("External Integrations") requires any embedding model choice to be
  recorded here before implementation, and notes the final retrieval-time embedding model is not
  selected yet (that is a Phase 3 decision, made when ChromaDB storage is wired up in Phase 2 PR
  5 or when hybrid retrieval is built in Phase 3).
- `sentence-transformers`, the most commonly cited "sentence embeddings" library, requires
  PyTorch even when using its ONNX backend (confirmed via current sentence-transformers docs), which
  is a heavy (600MB-1.2GB) dependency for a step that only needs inference, not training.

Decision:

- Use [`fastembed`](https://github.com/qdrant/fastembed) (Qdrant's ONNX-runtime-based embedding
  library) with its default dense text model, `BAAI/bge-small-en-v1.5` (384-dim), for the
  sentence embeddings used during chunking. It has no PyTorch dependency (~50MB of new packages
  vs. 600MB+ for sentence-transformers) and downloads a small quantized ONNX model on first use,
  cached locally by `huggingface_hub`.
- Wrap it behind `memQrag.ingestion.embeddings.embed_sentences(sentences) -> list[list[float]]`,
  a plain function with no fastembed types in its signature, so the chunking algorithm depends on
  a `Callable[[Sequence[str]], Sequence[Sequence[float]]]` shape, not on fastembed directly.
- This is scoped to chunking only. It does not fix the embedding model used for ChromaDB storage
  (Phase 2 PR 5) or retrieval (Phase 3); those PRs may reuse `bge-small-en-v1.5` for consistency
  between chunk-time and query-time embeddings, or choose differently, but must record that choice
  explicitly when made.

Consequences:

- First use of chunking on a machine without a cached model requires network access to download
  the model; `tests/test_ingestion_embeddings.py` skips itself (rather than failing) if that
  download is not possible, since this module's own unit tests should not be network-flaky. The
  chunking algorithm's tests use a fake embedding function instead (see "Decision: Semantic
  Chunking Algorithm").
- Switching embedding libraries or models later requires a new decision entry, since it changes
  where semantic chunk boundaries land for already-documented behavior.

### Decision: Semantic Chunking Algorithm

Date: 2026-07-24

Status: accepted.

Context:

- `docs/PRODUCT_TIMELINE.md` specifies three behaviors for this PR: semantic chunking using
  sentence embeddings, merging chunks below 200 tokens, and splitting chunks above 800 tokens.
- Sentence embedding generation is an external, network-and-model-dependent operation (see
  "Decision: Sentence Embedding Model For Semantic Chunking"); the chunking algorithm itself
  should still be deterministically unit-testable without it.
- No LLM or embedding provider's exact tokenizer has been chosen yet (`docs/ARCHITECTURE.md`,
  "External Integrations"), so an exact token count is not yet meaningful.

Decision:

- `memQrag/ingestion/chunking.py` implements `chunk_document(document: ExtractedDocument, embed:
  EmbeddingFunction) -> list[Chunk]`, where `EmbeddingFunction` is a plain
  `Callable[[Sequence[str]], Sequence[Sequence[float]]]`. Production callers pass
  `memQrag.ingestion.embeddings.embed_sentences`; tests pass a small deterministic fake, keeping
  the algorithm's tests fast and network-free.
- Sentence splitting uses a lightweight punctuation-based regex heuristic (no NLTK/spaCy
  dependency), sufficient for the demo's fictional documents; `docs/DECISIONS.md` should be
  updated if a more sophisticated splitter is needed later.
- Token counting (`estimate_token_count`) is a whitespace word-count approximation, not a real
  LLM tokenizer, since no provider's tokenizer has been chosen yet. This is an explicit,
  intentional approximation that the 200/800 thresholds are measured against; revisit when Phase
  7 picks an LLM provider.
- Algorithm, run once per `ExtractedSegment` (chunks never span segments, to keep each chunk's
  inherited `page_number`/`section_heading` accurate):
  1. Split the segment's text into sentences.
  2. Embed all sentences in one batch call and walk adjacent pairs; start a new group whenever
     cosine similarity between neighboring sentence embeddings drops below `0.5`, otherwise
     extend the current group. A single-sentence segment skips embedding entirely.
  3. Merge each undersized group (< `MIN_CHUNK_TOKENS` = 200) forward into the next group; if the
     final group is still undersized, merge it backward into the previous one instead. This is a
     pure token-count pass and intentionally ignores semantic similarity once triggered.
  4. Split any resulting group over `MAX_CHUNK_TOKENS` = 800 back into multiple chunks, greedily
     accumulating sentences until the next one would exceed the limit.
- `Chunk` (the output type) carries `text`, `token_count`, `source_document`, `page_number`, and
  `section_heading` only. It intentionally omits `chunk_id`, `document_id`, and `embedding
  reference` from `docs/ARCHITECTURE.md`'s planned `Chunk` entity, since those only become
  meaningful once persistence (Phase 2 PRs 4-5) assigns real identifiers.

Consequences:

- Chunking is deterministic and fully unit-testable without a model or network call; only the
  default `embed_sentences` wiring needs (skippable) network-dependent testing.
- A chunk can still exceed `MAX_CHUNK_TOKENS` if a single sentence alone exceeds it (an accepted
  edge case; no sub-sentence splitting is implemented).
- Persistence PRs (4-5) consume `Chunk` as-is and are responsible for assigning `chunk_id`,
  `document_id`, and the embedding reference when writing to SQLite/ChromaDB.
- Changing the similarity threshold, the merge/split strategy, or the token estimation method
  later requires a new decision entry, since retrieval quality depends on chunk boundaries.

### Decision: SQLite Persistence For Document And Chunk Metadata

Date: 2026-07-24

Status: accepted.

Context:

- The fourth Phase 2 PR needs to persist what `memQrag.ingestion.extraction` and
  `memQrag.ingestion.chunking` already produce (`ExtractedDocument`, `Chunk`) into SQLite, per
  `docs/PRODUCT_TIMELINE.md`'s exit criterion "Chunk metadata can be queried from SQLite."
  `docs/ARCHITECTURE.md`'s planned `Chunk` entity also lists `embedding reference`, and the
  planned `Document` entity lists `staleness status`, but neither is meaningful yet:
  `embedding reference` only exists once ChromaDB vectors are written (Phase 2 PR 5, not this
  one), and `staleness status` is only computed once Phase 4 implements staleness detection.
- `docker-compose.yml` already reserves a `./data/sqlite:/app/data` bind mount for the API
  container (see "Decision: Docker Compose Topology For The Local Full Stack"), so the database
  file's location should line up with that mount without requiring compose changes later.
- The project has consistently preferred the lightest dependency that does the job (e.g. `pypdf`/
  `python-docx` over heavier alternatives, `fastembed` over `sentence-transformers`).

Decision:

- Use Python's built-in `sqlite3` module directly; no ORM (e.g. SQLAlchemy) for this PR. Schema
  and queries live in `memQrag/ingestion/storage.py`.
- Schema, created via `CREATE TABLE IF NOT EXISTS`:
  - `documents(id INTEGER PRIMARY KEY, filename TEXT UNIQUE NOT NULL, file_type TEXT NOT NULL,
    created_date TEXT, last_modified_date TEXT, ingested_at TEXT NOT NULL)`. Dates are stored as
    ISO 8601 strings (SQLite has no native datetime type) and parsed back to `datetime` on read.
    No `staleness_status` column yet; add it in a new decision when Phase 4 needs it.
  - `chunks(id INTEGER PRIMARY KEY, document_id INTEGER NOT NULL REFERENCES documents(id) ON
    DELETE CASCADE, page_number INTEGER, section_heading TEXT, text TEXT NOT NULL, token_count
    INTEGER NOT NULL)`. No `embedding_reference` column yet; add it in a new decision alongside
    Phase 2 PR 5 (ChromaDB persistence).
  - `PRAGMA foreign_keys = ON` is set per connection, since SQLite does not enforce foreign keys
    by default.
- `filename` is the natural key for `documents`. Re-ingesting an already-known filename updates
  that row in place (`INSERT ... ON CONFLICT(filename) DO UPDATE`) rather than creating a
  duplicate, and `replace_chunks()` deletes and re-inserts that document's chunks. This keeps
  repeated demo ingestion idempotent instead of accumulating duplicate rows.
- The default database file is `data/memqrag.db` (relative to the process's working directory),
  matching the existing `data/` `.gitignore` entry. Running the API from the repository root
  inside the `api` container (working directory `/app`, per the existing `Dockerfile`) resolves
  this to `/app/data/memqrag.db`, which lands on the host at `./data/sqlite/memqrag.db` through
  the mount already reserved in `docker-compose.yml` — no compose change needed.
- All functions take a plain `sqlite3.Connection` (dependency injection), so tests use
  `sqlite3.connect(":memory:")` instead of touching disk.

Consequences:

- Phase 2 PR 5 (ChromaDB persistence) and Phase 4 (staleness detection) each add a column via a
  new decision entry plus an `ALTER TABLE` (or equivalent) rather than being blocked on this PR.
- Session memory, long-term memory, and contradiction records (Phases 4-5) get their own tables
  in their own PRs; this PR only owns `documents` and `chunks`.
- Switching to an ORM, changing the natural key, or changing the re-ingestion (upsert vs.
  versioned history) behavior later requires a new decision entry.

### Decision: ChromaDB Vector Persistence

Date: 2026-07-24

Status: accepted.

Context:

- The fifth Phase 2 PR needs to persist one vector per `Chunk` in ChromaDB, per
  `docs/PRODUCT_TIMELINE.md`, and satisfy the Phase 2 exit criterion "Vector references resolve
  back to stored chunk metadata."
- `docker-compose.yml` already runs a `chroma` service (the official Chroma server image) and
  already sets `CHROMA_HOST=chroma` / `CHROMA_PORT=8000` on the `api` service for exactly this
  connection (see "Decision: Docker Compose Topology For The Local Full Stack"), and maps that
  service to host port `8001`.
- "Decision: Sentence Embedding Model For Semantic Chunking" already chose `fastembed`'s
  `BAAI/bge-small-en-v1.5` for chunk-time semantic grouping and flagged that Chroma storage may
  reuse it "for consistency between chunk-time and query-time embeddings."
- ChromaDB itself is an explicit, non-swappable project dependency (`docs/PROJECT_BLUEPRINT.md`,
  `AGENTS.md`), unlike the embedding model or PDF/DOCX libraries, so there is no lighter
  alternative to evaluate here.

Decision:

- Add `chromadb` (the Python client/server package) as a runtime dependency.
- `memQrag/ingestion/vector_store.py` reuses `memQrag.ingestion.embeddings.embed_sentences` (the
  same model used for chunk-time grouping) to compute the vectors stored in Chroma, rather than
  relying on Chroma's own default embedding function. This keeps chunk boundaries and stored
  vectors consistent with one embedding model.
- The Chroma vector id for a chunk is `str(chunk_id)`, where `chunk_id` is that chunk's SQLite
  `chunks.id` primary key (see "Decision: SQLite Persistence For Document And Chunk Metadata").
  This directly satisfies "vector references resolve back to stored chunk metadata": given a
  Chroma id from a retrieval result, `int(vector_id)` is the SQLite chunk id to look up. No new
  `embedding_reference` column is added to `chunks`, superseding that earlier placeholder note.
- All chunk fields land in Chroma metadata (`document_id`, `source_document`, `token_count`, and
  `page_number`/`section_heading` when present) plus the chunk text as the Chroma "document", so a
  retrieval result is self-contained without a mandatory SQLite round-trip, while `chunk_id` still
  allows one when full row data (e.g. exact token count) is needed.
- `get_collection(client=None)` defaults to `chromadb.HttpClient(host=CHROMA_HOST or "localhost",
  port=CHROMA_PORT or 8001)` (the host-side port from `docker-compose.yml`), using a single fixed
  collection name (`memqrag_chunks`). All functions accept an already-constructed client/collection
  (dependency injection), so tests use `chromadb.EphemeralClient()` (a real, in-process Chroma
  client with no server or network) instead of requiring Docker or a running Chroma server.

Consequences:

- Retrieval (Phase 3) can query `memqrag_chunks` directly and resolve each hit's SQLite chunk row
  via `int(vector_id)`, without needing a lookup table.
- Re-ingesting a document currently assigns new SQLite chunk ids (via `replace_chunks`'
  delete-then-insert), which orphans the old Chroma vectors under the old ids. Cleaning those up
  is deferred to the ingestion orchestration path (Phase 2 PR 6 or later) that will call both
  `memQrag.ingestion.storage` and `memQrag.ingestion.vector_store` together; this PR only provides
  `delete_chunk_vectors()` for that future caller to use, and does not wire the two modules
  together itself.
- Switching the embedding model used for storage independently of chunking, changing the vector id
  scheme, or changing the collection name/count later requires a new decision entry.

### Decision: End-To-End Ingestion Fixture Tests

Date: 2026-07-24

Status: accepted.

Context:

- The sixth and final Phase 2 PR is "Add ingestion tests using small fixture documents," closing
  out Phase 2's three exit criteria in `docs/PRODUCT_TIMELINE.md`: files ingest successfully,
  chunk metadata is queryable from SQLite, and vector references resolve back to stored chunk
  metadata.
- Every Phase 2 module (`contracts`, `extraction`, `chunking`, `storage`, `vector_store`) already
  has its own unit tests, but no test exercises them composed together end-to-end; each exit
  criterion has only been demonstrated per-module, not as a whole pipeline.
- `docs/DECISIONS.md` ("ChromaDB Vector Persistence") already deferred building an orchestration
  module until "Phase 2 PR 6 or later"; this PR is that PR, but the tracker item is explicitly
  about tests, not a new production pipeline module.
- "Decision: Text Extraction Adapter Behavior" already established the precedent of building PDF/
  DOCX fixtures in-memory rather than checking in binary files.

Decision:

- No new orchestration/pipeline module is added. `tests/test_ingestion_pipeline.py` calls the
  existing per-module functions directly, in sequence (`intake_document` -> `extract_text` ->
  `chunk_document` -> `persist_ingested_document` -> `persist_chunk_vectors`), against one small,
  fictional fixture document per supported file type (`.txt`, `.md`, `.docx`, `.pdf`), and asserts
  each of the three exit criteria directly, one test per criterion (parametrized across all four
  file types).
- The shared PDF/DOCX in-memory builder functions used by `tests/test_ingestion_extraction.py`
  move into `tests/fixtures.py` (`build_minimal_pdf`, `build_minimal_docx`) so this new test file
  reuses them instead of duplicating fixture-construction code. `tests/` has no `__init__.py`, so
  pytest's default "prepend" import mode makes `tests/` importable as a top-level path; other test
  files import via `from fixtures import ...`, not `from tests.fixtures import ...`.
- These tests use the real `embed_sentences` (not the deterministic fake used in
  `test_ingestion_chunking.py`), since the point is to prove the real wiring works; the fixture
  that provides it skips (does not fail) if the embedding model cannot be loaded, matching
  `test_ingestion_embeddings.py`'s existing network-tolerance precedent.
- `chromadb.EphemeralClient()` instances share underlying state within a process (confirmed by
  hands-on testing: identical default settings hash to the same cached system), so every test
  needing a Chroma collection uses a `uuid`-suffixed collection name, not a fixed one, to stay
  isolated from other tests and other parametrized cases. The same fix was needed retroactively in
  `tests/test_ingestion_vector_store.py`.
- Parametrized test IDs are set explicitly via `pytest.param(..., id=...)` rather than left to
  pytest's default repr-based ID generation. Letting pytest derive an ID from raw DOCX/PDF fixture
  bytes produced a multi-kilobyte escaped-bytes string that pytest also writes into the
  `PYTEST_CURRENT_TEST` environment variable per test; on Windows this hit the OS's 32,767-
  character environment variable limit and crashed every parametrized test's setup/teardown.

Consequences:

- Phase 2's three exit criteria are now each directly, explicitly asserted by a passing test, not
  just implied by per-module unit tests.
- Any future ingestion orchestration module (e.g. a single `ingest_document()` entry point used by
  the Phase 7 `POST /api/ingest` endpoint) can reuse the same call sequence this test file
  demonstrates, but still does not exist yet.
- Parametrizing any future test with raw binary fixture bytes must set an explicit `id=`, per the
  Windows environment-variable-limit failure mode above.
- Adding a real orchestration/pipeline module, changing the fixture file format coverage, or
  moving fixtures to a checked-in `sample-data/` directory (reserved for Phase 8 demo content per
  `AGENTS.md`) requires a new decision entry.

### Decision: Dense Retrieval, Query Embedding, And Chroma Distance Space

Date: 2026-07-24

Status: accepted.

Context:

- The first Phase 3 PR needs to query ChromaDB for the top-20 chunks nearest a user's query, per
  `docs/PRODUCT_TIMELINE.md` and `docs/ARCHITECTURE.md`'s retrieval flow step 3.
- "Decision: Sentence Embedding Model For Semantic Chunking" explicitly deferred the query-time
  embedding model choice to this PR, noting retrieval "may reuse `bge-small-en-v1.5` for
  consistency between chunk-time and query-time embeddings, or choose differently, but must record
  that choice explicitly when made."
- `docs/ARCHITECTURE.md`'s planned confidence scoring (step 9, Phase 3 PR 5) is defined in terms
  of *cosine similarity* thresholds (HIGH > 0.85, MEDIUM 0.65-0.85, LOW < 0.65), but
  "Decision: ChromaDB Vector Persistence" created the `memqrag_chunks` collection without setting
  an explicit distance space, so it silently used Chroma's default (squared L2, not cosine) —
  confirmed by direct testing. Left uncorrected, later confidence-scoring code would be comparing
  L2 distances against cosine thresholds.
- Confirmed by direct testing that `fastembed`'s `BAAI/bge-small-en-v1.5` output vectors are
  already L2-normalized (norm ≈ 1.0), so switching the collection to cosine space needs no vector
  changes, only the collection's `hnsw:space` metadata.

Decision:

- Query embedding reuses `memQrag.ingestion.embeddings.embed_sentences` — the same model used to
  embed stored chunk vectors (`memQrag/ingestion/vector_store.py`). Query and chunk vectors must
  share one embedding space for similarity to be meaningful; this was not a real trade-off to
  re-litigate, just the explicit record the earlier decision asked for.
- `memQrag/ingestion/vector_store.py`'s `get_collection()` now creates `memqrag_chunks` with
  `metadata={"hnsw:space": "cosine"}`, so `1 - distance` from a Chroma query is a cosine
  similarity in `[-1, 1]`, matching the confidence thresholds' units ahead of Phase 3 PR 5. This
  amends "Decision: ChromaDB Vector Persistence" (which did not specify a distance space) rather
  than superseding it; no other behavior from that decision changes.
- Add `memQrag/retrieval/dense.py`: `dense_retrieve(collection, query, top_k=DENSE_TOP_K) ->
  list[DenseRetrievalResult]`, where `DENSE_TOP_K = 20`. `DenseRetrievalResult` is a frozen
  dataclass (`chunk_id`, `document_id`, `score`, `text`, `source_document`, `page_number`,
  `section_heading`) built entirely from Chroma's own stored metadata/document text — no mandatory
  SQLite round-trip to return a usable result, consistent with "Decision: ChromaDB Vector
  Persistence."
- `dense_retrieve` raises `ValueError` for a blank query rather than embedding and querying with
  empty text.

Consequences:

- Phase 3 PR 2 (BM25 sparse retrieval) and PR 3 (Reciprocal Rank Fusion) can treat
  `DenseRetrievalResult` as one of the two ranked candidate lists to fuse.
- Phase 3 PR 5 (confidence scoring) can use `DenseRetrievalResult.score` directly as a cosine
  similarity against the HIGH/MEDIUM/LOW thresholds, without re-deriving distance-to-similarity
  conversion.
- Any existing `memqrag_chunks` collection created before this PR (there is no live deployment
  yet, so none exists) would need to be dropped and re-created to pick up the new distance space;
  this is a no-op in practice since Phase 2 PR 5 was never deployed with real traffic.
- Switching the query embedding model independently of the storage embedding model, or changing
  the distance space again, requires a new decision entry.

### Decision: BM25 Sparse Retrieval

Date: 2026-07-24

Status: accepted.

Context:

- The second Phase 3 PR needs BM25 sparse retrieval for the top-20 candidates, per
  `docs/PRODUCT_TIMELINE.md` and `docs/ARCHITECTURE.md`'s retrieval flow step 4, to later fuse
  with dense retrieval (`memQrag/retrieval/dense.py`) via Reciprocal Rank Fusion (Phase 3 PR 3).
- Unlike dense retrieval, BM25 is not backed by a persistent, incrementally-queryable index in
  this project; a BM25 corpus must be built from the full set of chunk texts before scoring.
- "Decision: ChromaDB Vector Persistence" already stores every chunk's full text and metadata
  (`document_id`, `source_document`, `page_number`, `section_heading`) in the `memqrag_chunks`
  Chroma collection, self-contained without a mandatory SQLite round-trip; `dense_retrieve` reads
  that same collection.
- The project has consistently preferred small, well-known libraries over reinventing standard
  algorithms (`pypdf`, `python-docx`, `fastembed`) when the library is lightweight.

Decision:

- Add [`rank-bm25`](https://github.com/dorianbrown/rank_bm25) (`BM25Okapi`) as a runtime
  dependency. It is a single-module, pure-Python implementation whose only dependency is `numpy`,
  which is already installed transitively via `chromadb`, so this adds no meaningful new
  dependency weight.
- `memQrag/retrieval/sparse.py`'s `sparse_retrieve(collection, query, top_k=SPARSE_TOP_K)`
  (`SPARSE_TOP_K = 20`, matching `DENSE_TOP_K`) builds its BM25 corpus by reading every chunk's
  text and metadata directly from the same `memqrag_chunks` Chroma collection via
  `collection.get()` (confirmed to return the full collection with no hidden page-size limit),
  rather than adding a new SQLite read path. This keeps dense and sparse retrieval symmetric: both
  take a Chroma collection and return self-contained results.
- Tokenization is a simple lowercase word-boundary regex (`\w+`), with no stemming, lemmatization,
  or stopword removal in this PR — the same "lightweight heuristic, no NLP dependency" choice
  already made for sentence splitting in "Decision: Semantic Chunking Algorithm." Revisit with a
  new decision if a demo document's retrieval quality actually needs it.
- Chunks sharing no token with the query are excluded from the results, even though
  `BM25Okapi.get_scores()` returns a score for every chunk in the corpus (scoring the whole
  corpus, rather than an inverted index, is an implementation detail; a chunk sharing no terms
  with the query is not a real sparse match and should not occupy one of the top-20 slots). This
  overlap check is a separate token-set intersection, **not** a `score > 0` filter: BM25's IDF
  term goes negative for a token that appears in every document in the corpus (confirmed by
  direct testing with a single-document corpus), which is a real possibility for a small demo
  corpus, so a genuinely overlapping chunk can still score negative.
- `SparseRetrievalResult` mirrors `DenseRetrievalResult`'s shape (`chunk_id`, `document_id`,
  `score`, `text`, `source_document`, `page_number`, `section_heading`), but `score` stays a raw
  BM25 score (unbounded, corpus-size-dependent), not normalized to `[0, 1]` or made comparable to
  cosine similarity. Reciprocal Rank Fusion (Phase 3 PR 3) fuses by *rank position* per
  `docs/ARCHITECTURE.md` ("Fuse both rankings with Reciprocal Rank Fusion"), not by raw score, so
  the two scales never need to be reconciled.
- Empty-collection and blank-query handling mirrors `dense_retrieve`: an empty corpus returns `[]`
  immediately (avoiding `BM25Okapi` on zero documents), and a blank query raises `ValueError`.

Consequences:

- Phase 3 PR 3 (Reciprocal Rank Fusion) consumes `DenseRetrievalResult` and `SparseRetrievalResult`
  as two same-shaped-but-differently-scaled ranked lists, fusing by rank rather than score.
- `sparse_retrieve` re-scans and re-tokenizes the entire collection on every call (no cached BM25
  index across calls). This is an accepted simplicity/performance trade-off for a local demo-sized
  corpus; a real deployment with a large corpus would need a persistent inverted index instead,
  which requires a new decision entry.
- Adding stemming/stopword removal, switching to an inverted-index-backed BM25 library, or
  changing what counts as "no match" later requires a new decision entry.

### Decision: Reciprocal Rank Fusion For Dense And Sparse Results

Date: 2026-07-24

Status: accepted.

Context:

- The third Phase 3 PR fuses `memQrag.retrieval.dense.dense_retrieve` and
  `memQrag.retrieval.sparse.sparse_retrieve`'s ranked lists into one, per
  `docs/ARCHITECTURE.md`'s retrieval flow step 5 ("Fuse both rankings with Reciprocal Rank
  Fusion") and `docs/PRODUCT_TIMELINE.md`.
- `docs/ARCHITECTURE.md`'s planned "Retrieval result" entity lists `dense score` and `sparse
  rank` (not `sparse score`) as the fields it expects to carry forward, which lines up with a
  real constraint: a cosine similarity (`DenseRetrievalResult.score`) is bounded and directly
  meaningful (it already feeds the planned confidence thresholds in Phase 3 PR 5), while a raw
  BM25 score (`SparseRetrievalResult.score`) is unbounded and corpus-size-dependent, so only its
  *rank* is meaningful outside its own retrieval call.
- Reciprocal Rank Fusion (Cormack, Clarke & Buettcher, 2009) is the standard choice here
  precisely because it fuses by rank position, not by raw score, so two rankings on incomparable
  scales (cosine similarity vs. BM25) never need to be normalized against each other.
- The paper (and widely-adopted implementations — Elasticsearch's and OpenSearch's RRF both
  default `rank_constant` to this same value) uses a smoothing constant `k = 60`, chosen from a
  pilot study; the paper notes the optimum is flat across `k ∈ [20, 100]`.

Decision:

- Add `memQrag/retrieval/fusion.py`: `reciprocal_rank_fusion(dense_results, sparse_results, k=RRF_K)
  -> list[FusedRetrievalResult]`, with `RRF_K = 60`.
- RRF score for a chunk = `sum(1 / (k + rank))` over every input ranking that contains it, where
  `rank` is that ranking's 1-indexed position for the chunk. A chunk appearing in only one of the
  two rankings still gets fused, using only that ranking's contribution (this is exactly the
  "reciprocal rank fusion outperforms individual methods" property from the paper, not a gap to
  fill in).
- `FusedRetrievalResult` carries `chunk_id`, `document_id`, `text`, `source_document`,
  `page_number`, `section_heading` (from whichever input result the chunk was found in; identical
  either way since both point at the same stored chunk), `dense_score` (`float | None`, present
  only if the chunk appeared in `dense_results`), `sparse_rank` (`int | None`, present only if the
  chunk appeared in `sparse_results`), `fused_rank` (1-indexed final position), and `rrf_score`
  (the raw fused score that produced `fused_rank`). `rrf_score` is not in `docs/ARCHITECTURE.md`'s
  planned entity list, but is kept for transparency/debuggability (per `AGENTS.md`'s "do not hide
  low confidence retrieval behind confident answer wording" spirit) and because it costs nothing
  to carry.
- This function does not truncate its output to any particular size; it returns every chunk that
  appeared in either input ranking (a bounded union of at most `len(dense_results) +
  len(sparse_results)`, deduplicated by `chunk_id`), fully ranked. Per the retrieval flow, Phase 3
  PR 4 (cross-encoder reranking) is responsible for narrowing "top-20 candidates" down further,
  and PR 5 selects the "final top-5"; fusion itself should not pre-empt that.
- Tie-breaking for equal RRF scores (e.g. two sparse-only chunks that never overlap with any dense
  result) falls out of a stable sort over dense-then-sparse insertion order; this is deterministic
  but not a meaningful ranking signal on its own.

Consequences:

- Phase 3 PR 4 (reranking) and PR 5 (confidence scoring) consume `FusedRetrievalResult` as their
  input candidate list; PR 5 in particular can use `dense_score` directly against the cosine
  thresholds when present, and must decide separately how to handle a chunk that has no
  `dense_score` (sparse-only match) once it gets there.
- Changing the fusion algorithm, the `k` constant's default, or `FusedRetrievalResult`'s shape
  later requires a new decision entry.

### Decision: Cross-Encoder Reranking Model And Final Top-5 Selection

Date: 2026-07-24

Status: accepted.

Context:

- The fourth Phase 3 PR reranks `memQrag.retrieval.fusion.reciprocal_rank_fusion`'s output down
  to the final top-5 chunks, per `docs/ARCHITECTURE.md`'s retrieval flow steps 7-8 ("Rerank top
  candidates with a cross-encoder" / "Select final top-5 chunks") and `docs/PRODUCT_TIMELINE.md`.
- `docs/ARCHITECTURE.md`'s "External Integrations" section requires any reranker choice to be
  recorded here before implementation.
- `fastembed` (already a dependency; see "Sentence Embedding Model For Semantic Chunking") added
  a `fastembed.rerank.cross_encoder.TextCrossEncoder` API that runs ONNX cross-encoder rerankers
  locally, the same lightweight-dependency shape as the embedding model already in use — no new
  runtime dependency, no PyTorch. This makes it the natural choice over a separate
  `sentence-transformers`-based cross-encoder library.
- Of `TextCrossEncoder`'s supported models, `Xenova/ms-marco-MiniLM-L-6-v2` is the smallest
  (~80MB) and is the standard MS MARCO-trained MiniLM reranker quoted in fastembed's own README
  example; larger options (`BAAI/bge-reranker-base` at ~1GB, the `jina-reranker-v2` multilingual
  model) trade size for capability this project's fictional, English-only demo corpus doesn't
  need.

Decision:

- Add `memQrag/retrieval/cross_encoder.py`: `score_pairs(query, documents) -> list[float]`,
  wrapping a module-level `lru_cache`d `TextCrossEncoder(model_name="Xenova/ms-marco-MiniLM-L-6-v2")`,
  mirroring `memQrag.ingestion.embeddings.embed_sentences`'s shape (plain function, no fastembed
  types leaking into callers) so `memQrag/retrieval/rerank.py` can depend on a
  `Callable[[str, Sequence[str]], Sequence[float]]` shape and tests can substitute a fake scorer,
  the same pattern `memQrag.ingestion.chunking` and `memQrag.retrieval.dense` already use.
- Scores are raw model logits: unbounded, can be negative, higher means more relevant. They are
  not a probability or a similarity in `[0, 1]`/`[-1, 1]` like `dense_retrieve`'s cosine score, and
  must not be compared against it directly (same caution as `sparse_retrieve`'s BM25 score).
- Add `memQrag/retrieval/rerank.py`: `rerank(fused_results, query, top_k=RERANK_TOP_K) ->
  list[RerankedRetrievalResult]`, with `RERANK_TOP_K = 5` (the architecture's "final top-5").
  Scores every input chunk's `text` against `query` with `score_pairs`, then returns the top
  `top_k` sorted by descending rerank score. Unlike `reciprocal_rank_fusion`, this step *does*
  truncate its output — this is the "Select final top-5 chunks" step in the retrieval flow, so
  this is where the funnel narrows for good.
- `RerankedRetrievalResult` carries forward `chunk_id`, `document_id`, `text`, `source_document`,
  `page_number`, `section_heading`, `dense_score`, `sparse_rank`, and `fused_rank` from the input
  `FusedRetrievalResult`, plus `rerank_score` (matching the planned entity's `rerank score` field)
  and `final_rank` (1-indexed position in the returned top-5; not in the planned entity list, but
  kept for the same transparency reason `rrf_score` was kept on `FusedRetrievalResult` — a
  consistent "how did this chunk get here" trail through every stage).
- An empty `fused_results` input returns `[]` rather than raising, since an empty candidate list
  is a legitimate (if unlikely) state Phase 3 PR 5's confidence scoring must handle as LOW
  confidence, not an error condition.

Consequences:

- Phase 3 PR 5 (confidence scoring) consumes `RerankedRetrievalResult` as its final candidate
  list and assigns HIGH/MEDIUM/LOW confidence, primarily from `dense_score` per the cosine
  thresholds already documented in `docs/ARCHITECTURE.md`.
- Swapping the reranker model, changing `RERANK_TOP_K`, or changing `RerankedRetrievalResult`'s
  shape later requires a new decision entry.

### Decision: Confidence Scoring Thresholds And Sparse-Only Handling

Date: 2026-07-24

Status: accepted.

Context:

- The fifth Phase 3 PR assigns a confidence level to each of
  `memQrag.retrieval.rerank.rerank`'s final top-5 chunks, per `docs/ARCHITECTURE.md`'s retrieval
  flow step 9, which already specifies exact cosine similarity thresholds (HIGH greater than
  0.85, MEDIUM 0.65 to 0.85, LOW less than 0.65) — this PR implements those, it does not choose
  them.
- `RerankedRetrievalResult.dense_score` is `None` for a chunk that only appeared in the sparse
  ranking (see "Reciprocal Rank Fusion For Dense And Sparse Results"). The cross-encoder's
  `rerank_score` is not a substitute: it is a raw, unbounded logit with no defined relationship
  to the documented cosine thresholds, so using it to backfill a missing `dense_score` would
  invent a threshold behavior nowhere documented.
- `AGENTS.md`'s "Do not hide low confidence retrieval behind confident answer wording" rules out
  defaulting a sparse-only chunk to MEDIUM/HIGH just because it survived fusion and reranking —
  surviving those steps is not the same evidence as a high cosine similarity.

Decision:

- Add `memQrag/retrieval/confidence.py`: `ConfidenceLevel(str, Enum)` (`HIGH`, `MEDIUM`, `LOW`,
  matching the `SupportedFileType(str, Enum)` pattern in `memQrag.ingestion.contracts`),
  `HIGH_CONFIDENCE_THRESHOLD = 0.85`, `MEDIUM_CONFIDENCE_THRESHOLD = 0.65`.
- `confidence_for_dense_score(dense_score: float | None) -> ConfidenceLevel` is the pure
  threshold function: `> 0.85` is HIGH, `0.65` to `0.85` inclusive is MEDIUM, below `0.65` is LOW.
  A `None` score (sparse-only chunk) is always LOW, per the context above.
- `assign_confidence(reranked_results) -> list[ScoredRetrievalResult]` attaches a
  `confidence_level` to every input chunk, in order, with no filtering or reordering —
  confidence is a label, not another ranking signal at this stage.
- `ScoredRetrievalResult` carries every `RerankedRetrievalResult` field forward plus
  `confidence_level`, and is the first type whose field list matches
  `docs/ARCHITECTURE.md`'s planned "Retrieval result" entity almost exactly (still missing only
  `applied memory boost`, which does not exist until Phase 4/5).

Consequences:

- Phase 4/5's memory-informed boosting, once implemented, either adds an `applied_memory_boost`
  field to a later result type or feeds back earlier in the flow (before reranking, per the
  retrieval flow's step ordering) — either way, changing where boosting plugs in relative to this
  PR's confidence assignment requires a new decision entry.
- The response synthesis layer (Phase 6) is responsible for deciding what an *answer's* overall
  confidence is from a list of per-chunk confidence levels (e.g. the top chunk's level, or the
  lowest across all cited chunks) — that policy is out of scope for this PR and is not decided
  here.

### Decision: End-To-End Retrieval Fixture Tests

Date: 2026-07-24

Status: accepted.

Context:

- The sixth and final Phase 3 PR is "Add retrieval tests for ranking, fusion, reranking, and
  confidence labels," closing out Phase 3's two exit criteria in `docs/PRODUCT_TIMELINE.md`:
  retrieval returns ranked chunks with source references and confidence, and tests prove fusion
  and threshold behavior.
- Every Phase 3 module (`dense`, `sparse`, `fusion`, `rerank`, `confidence`) already has its own
  focused unit tests using fakes/mocks for exact, deterministic assertions (dense/sparse ranking,
  the RRF "two votes beat one" property, rerank truncation, confidence thresholds), but no test
  exercises them composed together end-to-end against one shared corpus — mirroring the gap
  `tests/test_ingestion_pipeline.py` closed for Phase 2 (see "Decision: End-To-End Ingestion
  Fixture Tests").
- No orchestration/pipeline module exists for retrieval either; per that same precedent, this PR
  is test-only and calls the existing per-module functions directly in sequence, the same way the
  eventual API layer (Phase 7) will.

Decision:

- Add `tests/test_retrieval_pipeline.py`. It builds one small, fictional, topically varied
  7-chunk corpus (a direct near-answer to the test query, a same-meaning-different-words
  paraphrase with zero lexical overlap, a same-words-different-meaning lexical decoy, and four
  unrelated filler chunks), persists it into one real Chroma collection with real embeddings, and
  runs `dense_retrieve` -> `sparse_retrieve` -> `reciprocal_rank_fusion` -> `rerank` ->
  `assign_confidence` in sequence — real model calls throughout, skipping (not failing) if either
  model can't be loaded, matching `tests/test_retrieval_dense.py` and `tests/test_retrieval_rerank.py`.
- The corpus size (7) deliberately exceeds `RERANK_TOP_K` (5) so truncation is actually exercised,
  and deliberately stays under both `DENSE_TOP_K` and `SPARSE_TOP_K` (20) so `dense_retrieve`
  returns every chunk — making "fusion does not truncate, reranking does" a directly observable,
  asserted property rather than an implementation detail taken on faith.
- All five pipeline stages run once in a module-scoped fixture (`pipeline_output`); the six test
  functions each assert one property of that shared result (dense/sparse both return candidates,
  fusion ranks the dual-signal chunk first without truncating, reranking truncates to top-5 with
  contiguous `final_rank`, every result carries a valid `source_document`, every result's
  `confidence_level` matches `confidence_for_dense_score(dense_score)` recomputed independently,
  and the top result is not LOW confidence) rather than re-embedding per test.

Consequences:

- This completes Phase 3's exit criteria and its tracker.
- The confidence-matches-recomputed-threshold assertion is a wiring-correctness check (proving
  `assign_confidence` was actually applied to the real pipeline's real scores), not a restatement
  of `confidence_for_dense_score`'s own unit tests; it will keep passing even if the real
  embedding model's exact scores drift, which the dense/fusion-ordering assertions in this file
  are not fully immune to (a materially different embedding or reranker model could change which
  chunk ends up ranked first) — swapping either model requires re-checking this file, not just
  the decision entries governing the model choice.

### Decision: SQLite Schema For Session Memory Records

Date: 2026-07-24

Status: accepted.

Context:

- The first Phase 4 PR adds the SQLite schema for session memory, per `docs/ARCHITECTURE.md`'s
  planned "Session memory" entity (query, retrieved chunks, usefulness flag, session id,
  timestamp) and `AGENTS.md`'s boundary that SQLite (not ChromaDB) stores session memory.
  Memory-informed boosting (Phase 4 PR 3) and the rest of Phase 4 build on this schema; this PR is
  schema plus basic read/write only, not the boosting logic itself.
- `memQrag.ingestion.storage` already owns the `documents`/`chunks` tables in the same SQLite
  database file (`data/memqrag.db`; see "SQLite Persistence For Document And Chunk Metadata").
  `AGENTS.md`'s boundary describes one SQLite store holding document metadata, session memory,
  long-term memory, conflict records, and staleness state — one database file, with each module
  owning its own tables, not one database per module.
- A session memory row's "retrieved chunks" naturally point at `chunks.id` rows, but
  `replace_chunks()` deletes and recreates a document's chunk rows wholesale on re-ingestion
  (fresh autoincrement ids each time), which would silently break a hard foreign key from session
  memory to `chunks.id` on the very first re-ingestion — turning a persistent memory feature into
  one that quietly loses history. `memQrag.ingestion.vector_store` already faced an analogous
  cross-store reference (a Chroma vector id pointing at a SQLite chunk id) and treated it as a
  plain stored value, not an enforced foreign key.

Decision:

- Add `memQrag/memory/session.py` with a `session_memory` table: `id`, `session_id` (`TEXT`),
  `query` (`TEXT`), `retrieved_chunk_ids` (`TEXT`, a JSON-encoded list of ints — a plain stored
  value, not a foreign key, for the re-ingestion reason above; a stale id it points at is a later
  problem for whatever reads it, not a constraint this table enforces), `usefulness_flag`
  (`INTEGER`, nullable: `NULL` means no feedback yet, `0`/`1` means not-useful/useful), and
  `created_at` (`TEXT`, ISO 8601 UTC, matching `documents.ingested_at`'s format).
  `usefulness_flag` is nullable and set later via a separate call, not at insert time — per
  `docs/PROJECT_BLUEPRINT.md`'s "Ask a question" workflow ("...persist session feedback"),
  usefulness is feedback collected after a query's chunks are already retrieved and recorded, not
  known upfront.
- `connect(db_path=DEFAULT_DB_PATH)` calls `memQrag.ingestion.storage.connect()` (so the shared
  database's `documents`/`chunks` tables always exist too) and then this module's own
  `create_tables()`, so one `memory.session.connect()` call is sufficient to get the full schema
  needed for memory tests or future callers — no orchestration module needed for this, matching
  the same "call functions directly until a real need arises" precedent as ingestion and
  retrieval.
- `record_session_query(conn, session_id, query, retrieved_chunk_ids)` inserts a row (`created_at`
  defaults to now) and returns the new row's id; `set_usefulness(conn, session_memory_id, useful)`
  updates one row's flag; `get_session_memory(conn, session_id)` reads all of one session's rows
  back, oldest first.

Consequences:

- Phase 4 PR 3 (memory-informed retrieval boosts) reads `session_memory` (likely filtered by
  `usefulness_flag = 1`) to decide which past queries' chunks to boost; it is not implemented
  here.
- Phase 4 PR 2 (long-term memory schema) will face the same "loose reference, not a foreign key"
  question for whatever document/chunk references it stores, and should follow this same
  precedent unless a new decision documents otherwise.
- Changing `retrieved_chunk_ids`'s storage shape (e.g. a join table instead of a JSON column) or
  `usefulness_flag`'s tri-state semantics later requires a new decision entry.

### Decision: SQLite Schema For Long-Term Memory Records

Date: 2026-07-24

Status: accepted.

Context:

- The second Phase 4 PR adds the SQLite schema for long-term memory, per `docs/ARCHITECTURE.md`'s
  planned "Long-term memory" entity (query embedding, best document ids, success count, last
  used, hit rate, decay weight). Like session memory's schema PR, this is schema plus basic
  read/write only — memory-informed boosting (Phase 4 PR 3) and decay (Phase 4 PR 4) implement the
  actual formulas that update these counters over time; this PR just gives them somewhere to live.
- `query embedding` is only meaningful once something can actually run a similarity search against
  it, which is Phase 4 PR 3's job, not this one — the same reasoning "Decision: SQLite Persistence
  For Document And Chunk Metadata" used to defer `Chunk`'s `embedding_reference` column until
  Phase 2 PR 5 actually implemented ChromaDB persistence. Adding a raw embedding storage column
  now, before anything reads it, would be exactly the kind of speculative schema that precedent
  argues against.
- Unlike `chunks.id` (wholesale deleted and recreated by `replace_chunks()` on re-ingestion, which
  is why session memory's `retrieved_chunk_ids` is a plain JSON column, not a foreign key —
  see "SQLite Schema For Session Memory Records"), `documents.id` is stable across re-ingestion
  (`save_document()` is an upsert keyed on `filename`). A `best_document_ids` foreign key would
  therefore actually be safe here.
- `memQrag.memory.session.connect()` already opens the shared database and ensures its own table
  exists on top of `memQrag.ingestion.storage`'s tables; extending that same chain is simpler than
  each memory submodule separately re-deriving "how do I get the full shared schema."

Decision:

- Add `memQrag/memory/long_term.py` with a `long_term_memory` table: `id`, `query` (`TEXT` — the
  representative query text; no embedding column yet, per the context above), `best_document_ids`
  (`TEXT`, a JSON-encoded list of ints), `success_count` (`INTEGER`, default `0`), `hit_rate`
  (`REAL`, default `0.0`), `decay_weight` (`REAL`, default `1.0` — full strength until Phase 4 PR 4
  starts reducing it), and `last_used` (`TEXT`, ISO 8601 UTC).
- `best_document_ids` is a plain JSON column, not a foreign key, even though `documents.id` is
  stable enough that a foreign key would be safe — kept consistent with session memory's
  `retrieved_chunk_ids` shape rather than introducing a second storage convention for "a list of
  ids" within the same module family. A future decision can revisit this once a real need for
  referential integrity here (e.g. cascading cleanup when a document is deleted) shows up.
- `connect(db_path=DEFAULT_DB_PATH)` calls `memQrag.memory.session.connect()` (which itself calls
  `memQrag.ingestion.storage.connect()`), extending the same chain so one
  `memory.long_term.connect()` call is sufficient to get the full shared schema
  (`documents`/`chunks`/`session_memory`/`long_term_memory`) — each new memory submodule builds on
  the previous one's `connect()` rather than re-deriving it.
- `record_long_term_memory(conn, query, best_document_ids)` inserts a row with the defaults above
  and returns its id. `update_long_term_memory(conn, id, *, success_count=None, hit_rate=None,
  decay_weight=None, last_used=None)` is a plain field setter — omitted keyword arguments keep
  their current value — deliberately not an "algorithm" (it does not decide *what* the new
  success_count or hit_rate should be; that policy belongs to Phase 4 PR 3/PR 4). `get_long_term_memory_by_id()`
  and `get_all_long_term_memory()` (most recently used first) are the read paths; there is no
  similarity search yet, since that needs the query embedding this PR defers.

Consequences:

- Phase 4 PR 3 must decide, and record here, how an incoming query gets matched against
  `long_term_memory` rows (this is also where the query-embedding storage question — a new SQLite
  column, or a separate Chroma collection like chunk vectors — gets decided) and what formula
  updates `success_count`/`hit_rate` on a match.
- Phase 4 PR 4 (memory decay) must decide, and record here, the formula that reduces
  `decay_weight` for memories older than 30 days with a low hit rate.
- Changing `best_document_ids`'s storage shape, adding the query embedding column/store, or
  changing what triggers a `long_term_memory` row to be created later all require a new decision
  entry.

### Decision: Memory-Informed Retrieval Boosts For Similar Past Queries

Date: 2026-07-24

Status: accepted.

Context:

- The third Phase 4 PR implements `docs/ARCHITECTURE.md`'s retrieval flow steps 2 ("Check
  long-term memory for similar successful queries") and 6 ("Apply memory-informed boosts where
  appropriate"). "SQLite Schema For Long-Term Memory Records" deferred two questions to this PR:
  where the query embedding lives, and what formula updates `success_count`/`hit_rate` on a
  match.
- "SQLite Schema For Session Memory Records" anticipated this PR reading `session_memory`
  (filtered by `usefulness_flag`) to decide what to boost — but `session_memory` only stores
  `retrieved_chunk_ids`, not document ids, and chunk ids are volatile across re-ingestion (the
  reason that table isn't a foreign key). Long-term memory needs to boost by document id (fusion's
  results carry `document_id`, and `chunks.id` rows for the same document already get replaced on
  re-ingestion), so something has to resolve chunk id -> document id at promotion time, not at
  boost time.
- `hit_rate` cannot be a meaningful ratio without a denominator (how many times this memory was
  matched), and no such column exists in the planned "Long-term memory" entity in
  `docs/ARCHITECTURE.md` (query embedding, best document ids, success count, last used, hit rate,
  decay weight). This is an implementation necessity, not a new planned-entity concept, and is
  recorded here per AGENTS.md's "update docs/DECISIONS.md when a meaningful ... decision is made."
- The long-term memory corpus is expected to stay small relative to the chunk corpus (one row per
  distinct remembered query pattern, not per document/chunk), so it does not need ChromaDB's
  ANN index the way chunk vectors do — brute-force cosine similarity over every
  `long_term_memory` row is fast enough at this scale.

Decision:

- Store each long-term memory row's embedding as a new `query_embedding` column (`TEXT`,
  JSON-encoded `list[float]`, `NOT NULL`) on the existing `long_term_memory` table, not in a
  second Chroma collection. This keeps the "small, non-ANN, per-query-pattern" store described
  above inside the same SQLite file AGENTS.md already scopes long-term memory to, rather than
  introducing a second vector-store category alongside "ChromaDB stores vector embeddings and
  chunk references" (that boundary is specifically about chunk references).
- Add a `match_count` column (`INTEGER`, default `0`) alongside `success_count`, so
  `hit_rate = success_count / match_count` is a real ratio, not an unbacked field. Both are
  updated together by `memQrag/memory/boost.py`'s `remember_query_outcome()`.
- There is no migration framework yet (out of scope until a real deployment need arises). Adding
  columns to an existing table only affects local, gitignored `data/memqrag.db` files, which have
  no production data yet; a developer with a pre-existing local database from before this PR must
  delete that file to pick up the new columns. This is acceptable for now and should be revisited
  once real deployed data exists.
- Add `memQrag/memory/boost.py`:
  - `remember_query_outcome(conn, query, best_document_ids, was_successful, *, query_embedding=None, merge_threshold=0.95)`
    is the write path. It embeds `query` (or reuses a passed-in `query_embedding`, to avoid a
    redundant `embed_sentences` call when a caller already has one — e.g. the same query
    `dense_retrieve` embeds), and either reinforces the most similar existing record whose cosine
    similarity is `>= merge_threshold` (so "What is the return policy?" and "What's your return
    policy?" accumulate into one row instead of fragmenting) or creates a new one via
    `long_term.record_long_term_memory()`. `match_count` increments by 1 either way;
    `success_count` increments only `if was_successful`; `hit_rate` is recomputed as their ratio.
    `merge_threshold` (0.95) is deliberately much stricter than `SIMILARITY_THRESHOLD` below,
    since merging conflates two records permanently while boosting only affects one query's
    ranking.
  - `find_similar_successful_memory(conn, query, *, query_embedding=None, similarity_threshold=0.90, min_hit_rate=0.5)`
    is the read path for flow step 2: the most similar record with `match_count > 0` and
    `hit_rate >= min_hit_rate`, or `None`. `similarity_threshold` (0.90) is set higher than dense
    retrieval's own HIGH-confidence cosine threshold (0.85), since this boosts based on a
    *different* query's historical outcome rather than checking the current query's relevance
    directly — the bar for "similar enough to trust" should be stricter than the bar for "this
    chunk itself looks relevant."
  - `apply_memory_boost(fused_results, similar_memory, boost_amount=0.05)` is flow step 6: adds
    `boost_amount` to the `rrf_score` of every `FusedRetrievalResult` whose `document_id` is in
    `similar_memory.best_document_ids` (or leaves every score unchanged if `similar_memory` is
    `None`), then re-sorts, returning `BoostedRetrievalResult` — the first result type to carry
    `applied_memory_boost`, per `docs/ARCHITECTURE.md`'s planned "Retrieval result" entity.
    `BOOST_AMOUNT = 0.05` is chosen larger than the maximum possible single-list RRF contribution
    (`1 / (RRF_K + 1) ≈ 0.0164`), so a boosted document reliably outranks a document matched in
    only one of dense/sparse retrieval, while staying the same order of magnitude as fusion scores
    generally (not so large it always overrides reranking's own signal downstream).
  - `promote_session_memory_to_long_term(conn, session_id, merge_threshold=0.95)` resolves the
    chunk-id -> document-id gap from the context above: it reads every `session_memory` row for
    a session with `usefulness_flag` set (skipping rows with no feedback yet), maps
    `retrieved_chunk_ids` to their owning `document_id`s via a new
    `memQrag.ingestion.storage.get_chunk_by_id()`, and calls `remember_query_outcome()` once per
    row. This is the concrete place `session_memory` feeds `long_term_memory`, closing the loop
    the session-memory decision anticipated.

Consequences:

- This PR implements the boost mechanism and the session -> long-term promotion path end to end,
  each with its own tests, but does not wire `apply_memory_boost()` into an actual
  fusion -> boost -> rerank -> confidence pipeline, and does not add `applied_memory_boost` to
  `RerankedRetrievalResult`/`ScoredRetrievalResult`. Phase 3's dense/sparse/fusion/rerank/
  confidence stages were likewise only stitched together in that phase's own final PR
  (`tests/test_retrieval_pipeline.py`); Phase 4's final PR ("Add memory and staleness tests") is
  where this same stitching, and that type-propagation question, should happen for memory.
- `promote_session_memory_to_long_term()` is not called automatically by anything yet — no
  orchestration layer exists (same "call functions directly until a real need arises" precedent
  as ingestion and retrieval). The Phase 6/7 agent/API layer is the eventual caller, once session
  feedback actually arrives over the API.
- Phase 4 PR 4 (memory decay) reduces `decay_weight` for old, low-hit-rate memories; it is not
  consulted by `find_similar_successful_memory()` here, since decay does not exist yet. Once it
  does, a new decision should record whether `apply_memory_boost()`'s effective boost should scale
  by `decay_weight`.
- Changing `SIMILARITY_THRESHOLD`, `MERGE_THRESHOLD`, `MIN_HIT_RATE_TO_BOOST`, `BOOST_AMOUNT`, the
  `hit_rate` formula, or the additive (vs. multiplicative) boost mechanism later requires a new
  decision entry.

### Decision: Memory Decay For Old, Low-Hit-Rate Memories

Date: 2026-07-24

Status: accepted.

Context:

- The fourth Phase 4 PR implements `docs/PRODUCT_TIMELINE.md`'s "Implement memory decay for
  memories older than 30 days with low hit rate" and its exit criterion "Old low-value memory has
  reduced retrieval influence." `long_term_memory.decay_weight` has existed since "SQLite Schema
  For Long-Term Memory Records" (default `1.0`, full strength), but nothing has read or written it
  since — this PR is what actually decides the formula and gives it an effect.
- "Memory-Informed Retrieval Boosts For Similar Past Queries" explicitly deferred one question to
  whichever PR implemented decay: "whether `apply_memory_boost()`'s effective boost should scale
  by `decay_weight`." Not scaling it would leave `decay_weight` a stored-but-inert number, which
  would not satisfy "reduced retrieval influence" — the whole point of a demo-visible decay signal
  is that it changes ranking behavior, not just a value in a table.
- A "multiply the stored `decay_weight` by a factor every time the decay job runs" formula would
  make the result depend on how often the job happens to run, not on elapsed time — running a
  decay sweep twice in one day would decay a memory twice as fast as running it once a day. That
  is not what "older than 30 days" describes, and would make behavior fragile to whatever schedule
  Phase 6/7 eventually wires up.
- Decaying to exactly `0.0` would make an old memory indistinguishable from "never boost this,"
  which reads as suppressing it outright rather than deprioritizing it — the same "do not silently
  suppress" concern already recorded for stale/contradictory evidence in AGENTS.md's "Do Not"
  section, applied here to memory instead of documents.

Decision:

- Add `memQrag/memory/decay.py`:
  - `is_decay_eligible(record, now=None, age_days=30, hit_rate_threshold=0.5)`: `True` once a
    record is both old (`now - record.last_used >= age_days` — measured from `last_used`, which
    `remember_query_outcome()` refreshes on every match, so a reused memory never ages out) and
    low-value (`record.hit_rate < hit_rate_threshold`; a never-matched record's default `hit_rate
    == 0.0` counts as low-value too). `hit_rate_threshold` defaults to the same `0.5` value as
    `memQrag.memory.boost.MIN_HIT_RATE_TO_BOOST`, since a memory that would not qualify for
    boosting is exactly the kind of "low-value" memory decay should target — kept as its own
    constant rather than importing `boost`'s, so the two stay independently tunable without one
    change silently changing the other's behavior.
  - `decay_weight_for(record, now=None, ...)`: **not** eligible -> `1.0`. Eligible -> `decay_factor
    ** elapsed_periods` (default `decay_factor = 0.5`; `elapsed_periods` is `1 +` how many whole
    `age_days`-long periods have passed since the record first became eligible), floored at
    `min_decay_weight = 0.1`. This recomputes from `(now, last_used, hit_rate)` every time and
    deliberately ignores the currently stored `decay_weight` — making `apply_memory_decay()`
    idempotent for a given `now` (calling it twice does not decay twice) and self-correcting (a
    decayed record that gets reused, refreshing `last_used`, is restored to `1.0` on the next
    sweep rather than staying stuck at its last decayed value), which directly avoids the
    schedule-dependent formula the context above rules out.
  - `apply_memory_decay(conn, now=None)`: reads every `long_term_memory` row, writes back
    `decay_weight_for(record, now)` wherever it differs from the stored value via
    `long_term.update_long_term_memory()`, and returns the changed ids. Like
    `promote_session_memory_to_long_term()`, nothing calls this automatically yet — no
    scheduler/orchestration layer exists (same "call functions directly until a real need arises"
    precedent as ingestion, retrieval, and `memQrag.memory.boost`).
- Resolve "Memory-Informed Retrieval Boosts"'s deferred question: `memQrag.memory.boost.apply_memory_boost()`
  now multiplies its boost by `similar_memory.decay_weight` (`effective_boost = BOOST_AMOUNT *
  decay_weight`) instead of applying the flat `BOOST_AMOUNT` regardless of age. A fully-decayed
  memory (`decay_weight` at the `0.1` floor) still nudges its documents slightly rather than being
  excluded outright, matching the "deprioritize, don't erase" framing above; `find_similar_successful_memory()`'s
  gating is unchanged, since a near-zero `decay_weight` already makes the resulting boost
  negligible without needing a second exclusion check.

Consequences:

- `decay_weight` now changes retrieval ranking (via `apply_memory_boost`), not just a stored
  metric — a future UI/API surface exposing long-term memory (Phase 7/8) should show it as "how
  much this memory currently influences results," not a raw, static field.
- Nothing runs `apply_memory_decay()` on a schedule yet; until the Phase 6/7 agent/API layer (or a
  scheduled job) calls it, `decay_weight` values only update whenever something happens to invoke
  it directly (e.g. in tests). This mirrors `promote_session_memory_to_long_term()`'s same
  not-yet-wired status.
- Changing `DECAY_AGE_DAYS`, `DECAY_HIT_RATE_THRESHOLD`, `DECAY_FACTOR`, `MIN_DECAY_WEIGHT`, the
  "recompute from scratch" (vs. "multiply the stored value") formula, or how `apply_memory_boost`
  incorporates `decay_weight` later requires a new decision entry.

### Decision: Configurable Staleness Detection For Frequently Retrieved Documents

Date: 2026-07-24

Status: accepted.

Context:

- The fifth Phase 4 PR implements `docs/PRODUCT_TIMELINE.md`'s "Implement configurable staleness
  detection for frequently retrieved documents older than 90 days" and its exit criterion "Stale
  frequently retrieved documents are surfaced for review." "SQLite Persistence For Document And
  Chunk Metadata" deferred `documents.staleness_status` until this PR needed it.
- Age alone is the wrong signal: an old, never-retrieved document is unimportant, not a review
  priority. Frequency alone is also wrong: a frequently retrieved *recent* document is working as
  intended. Both conditions together are what the tracker item actually describes.
- AGENTS.md says SQLite stores "staleness review state," and `docs/ARCHITECTURE.md`'s planned
  Document entity lists `staleness status`. A separate review-workflow table (with assignees,
  notes, resolution timestamps) would be overbuilt for a demo that only needs to *surface* stale
  documents — Phase 7's `GET /api/documents` and Phase 8's staleness banner can read a status
  column directly. A fuller review workflow can still be layered on later if a real need shows up.
- Retrieval frequency is already observable in `session_memory.retrieved_chunk_ids` (every query
  records which chunks it retrieved). Counting across every session, not just the current one, is
  what "frequently retrieved" means product-wide — a document retrieved five times in five
  different sessions is more of a review priority than one retrieved five times in a single
  throwaway session, but for MVP both count the same (a query is a query).
- There is still no migration framework (same precedent as adding `query_embedding`/`match_count`
  in Phase 4 PR 3). Adding a column to an existing table only affects local, gitignored
  `data/memqrag.db` files; a developer with a pre-existing local database from before this PR must
  delete that file to pick up the new column.

Decision:

- Add `staleness_status` (`TEXT NOT NULL DEFAULT 'fresh'`) to the `documents` table, with a
  `DocumentStalenessStatus` enum (`FRESH` / `STALE`). Stored on the document itself rather than a
  separate table, matching the planned Document entity and keeping the Phase 7/8 "list documents
  with staleness flags" surface a single-table read.
- `save_document()` always writes `FRESH` (including on re-ingestion upsert), so refreshing a
  document's content clears any prior stale flag — the re-ingested content is what is now stored,
  and earlier evidence no longer applies.
- Add `get_all_documents()` and `update_document_staleness_status()` on
  `memQrag.ingestion.storage` (plain list / field setter, same pattern as long-term memory's
  update helper). Add `get_all_session_memory()` on `memQrag.memory.session` so staleness can count
  retrievals across every session, not just one.
- Add `memQrag/memory/staleness.py`:
  - `effective_document_date(document)`: prefers `last_modified_date`, then `created_date`, then
    `ingested_at` — TXT/Markdown often lack the first two (see "Text Extraction Adapter Behavior").
  - `count_document_retrievals(conn, document_id)`: how many recorded queries (across every
    session) retrieved at least one of the document's chunks; a query that hits several of the
    same document's chunks still counts once.
  - `is_stale(conn, document, now=None, age_days=90, min_retrieval_count=5)`: `True` only when
    both conditions hold. Defaults match the tracker wording (90 days) and a small demo-scale
    frequency bar (`MIN_RETRIEVAL_COUNT = 5`); both are keyword-overridable, which is what
    "configurable" means in this PR (function parameters, not a config file — no settings system
    exists yet).
  - `detect_stale_documents(conn, now=None, ...)`: re-evaluates every document from scratch each
    call and persists `STALE`/`FRESH`, returning the current stale ids. Recomputing every document
    (not only currently-FRESH ones) keeps a re-ingested or no-longer-qualifying document from
    staying stuck `STALE`. Nothing calls this on a schedule yet — same
    call-functions-directly-until-needed precedent as boost/decay.

Consequences:

- Phase 4's final PR ("Add memory and staleness tests") should stitch memory + staleness together
  the way Phase 3's final PR stitched retrieval stages — this PR's own unit tests cover the
  detection module in isolation.
- Phase 7's `GET /api/documents` and Phase 8's staleness banner read `documents.staleness_status`
  directly; they should not invent a second source of truth for "is this document stale."
- Staleness is a review signal, not a retrieval filter — flagged documents still retrieve and
  answer. Hiding them would violate AGENTS.md's "do not silently suppress stale or contradictory
  sources."
- Changing `STALENESS_AGE_DAYS`, `MIN_RETRIEVAL_COUNT`, the both-conditions-required rule, the
  `effective_document_date` fallback order, or promoting this into a separate review-workflow
  table later requires a new decision entry.

### Decision: End-To-End Memory And Staleness Fixture Tests

Date: 2026-07-25

Status: accepted.

Context:

- The sixth and final Phase 4 PR is "Add memory and staleness tests," closing out Phase 4's three
  exit criteria in `docs/PRODUCT_TIMELINE.md`: similar queries can boost previously successful
  documents; stale frequently retrieved documents are surfaced for review; old low-value memory
  has reduced retrieval influence.
- Every Phase 4 module (`session`, `long_term`, `boost`, `decay`, `staleness`) already has its own
  focused unit tests, but no test exercises them composed together against one shared SQLite
  fixture — mirroring the gap `tests/test_retrieval_pipeline.py` closed for Phase 3 (see
  "Decision: End-To-End Retrieval Fixture Tests").
- "Memory-Informed Retrieval Boosts" deferred two questions to this PR: (1) stitching
  `apply_memory_boost()` into an actual fusion -> boost (-> rerank -> confidence) sequence, and
  (2) whether `applied_memory_boost` should propagate onto `RerankedRetrievalResult` /
  `ScoredRetrievalResult`. "Configurable Staleness Detection" likewise asked this PR to stitch
  memory + staleness together the way Phase 3's final PR stitched retrieval stages.
- No orchestration/pipeline module exists for memory either; per the same Phase 2/3 precedent,
  this PR is test-only and calls the existing per-module functions directly in sequence.

Decision:

- Add `tests/test_memory_pipeline.py`. It builds a small fictional two-document SQLite fixture
  (return-policy vs shipping) plus an old/new policy pair for staleness, and asserts each Phase 4
  exit criterion as its own test function:
  - **Boost:** `remember_query_outcome` -> `find_similar_successful_memory` ->
    `apply_memory_boost` on a synthetic fused ranking where the previously-successful document
    starts behind; the boosted ranking reorders it first with a non-zero `applied_memory_boost`.
  - **Decay:** mixed outcomes + aged `last_used` -> `apply_memory_decay` shrinks `decay_weight`;
    default `find_similar_successful_memory` then returns `None` (low hit rate fails its gate), so
    the default boost path applies zero influence; applying the decayed record directly still
    scales `BOOST_AMOUNT` by `decay_weight`, proving that wiring.
  - **Staleness:** old + frequently retrieved document is returned by `detect_stale_documents`
    and persisted as `STALE`; a frequent-but-recent peer stays `FRESH`.
  - **Session -> LTM composition:** `record_session_query` -> `set_usefulness` ->
    `promote_session_memory_to_long_term` -> `find_similar_successful_memory` ->
    `apply_memory_boost`, using the real embedder and skipping (not failing) if it can't load.
- Hand-picked query embeddings (not the real embedder) drive the boost/decay path so those exit
  criteria stay deterministic and network-free; only the session-promotion composition check needs
  `embed_sentences`.
- **Type-propagation decision:** `applied_memory_boost` stays on `BoostedRetrievalResult` only.
  Propagating it onto `RerankedRetrievalResult` / `ScoredRetrievalResult` (and teaching `rerank` to
  accept boosted inputs) is deferred until Phase 6/7 builds real orchestration — changing those
  types with no production caller would be speculative schema churn, the same reason earlier PRs
  deferred unused columns. The integration tests stitch through fusion -> boost (architecture
  steps 5-6) and leave steps 7-9 to the existing retrieval pipeline tests; the eventual API layer
  will call `apply_memory_boost` between `reciprocal_rank_fusion` and `rerank` the same way these
  tests do.

Consequences:

- This completes Phase 4's exit criteria and its tracker.
- Phase 5 (Contradiction Detection) starts next; it should not re-open memory type-propagation
  unless contradiction results also need to ride on the same retrieval result types.
- Changing the exit-criterion assertions, bringing `applied_memory_boost` into rerank/confidence
  types, or adding a production orchestration module that wraps this sequence later requires a new
  decision entry.

### Decision: SQLite Schema For Contradiction Records

Date: 2026-07-25

Status: accepted.

Context:

- The first Phase 5 PR adds the SQLite schema for contradiction / conflict records, per
  `docs/ARCHITECTURE.md`'s planned "Conflict" entity (entity, claim A, claim B, source chunk
  references, detection timestamp, review status) and `AGENTS.md`'s boundary that SQLite stores
  conflict records. Entity/claim comparison (Phase 5 PR 2), response flagging (PR 3), and
  `GET /api/conflicts` (PR 4) build on this schema; this PR is schema plus basic read/write only.
- `AGENTS.md` lists conflict records alongside document metadata and memory in one SQLite store —
  one database file, with each module owning its own tables. The existing connect-chain
  (`storage` -> `session` -> `long_term`) already opens that shared file; a new module should
  extend that chain rather than re-deriving it.
- Module placement is not obvious: `memQrag.memory`'s documented responsibility stops at session /
  long-term / boost / decay / staleness (no contradictions), and `memQrag.agent` is still a Phase 6
  placeholder whose responsibility list also omits contradiction detection. Phase 5 is its own
  tracker phase with its own API surface (`GET /api/conflicts`), so a dedicated top-level package
  is cleaner than forcing conflicts into memory or a still-empty agent module.
- Source chunk references face the same re-ingestion problem session memory already solved:
  `replace_chunks()` deletes and recreates `chunks.id` rows wholesale, so a foreign key from
  conflicts to `chunks.id` would silently break on the first re-ingestion. JSON-encoded id lists
  match the session / long-term memory precedent.

Decision:

- Add a new top-level package `memQrag/conflicts/` (update `tests/test_package_structure.py` and
  `docs/ARCHITECTURE.md`'s planned runtime shape to include it alongside ingestion / retrieval /
  memory / agent / api).
- Add `memQrag/conflicts/records.py` with a `conflicts` table: `id`, `entity` (`TEXT`), `claim_a`
  / `claim_b` (`TEXT` — the two opposing factual claims), `claim_a_chunk_ids` / `claim_b_chunk_ids`
  (`TEXT`, JSON-encoded lists of ints, not foreign keys), `detected_at` (`TEXT`, ISO 8601 UTC),
  and `review_status` (`TEXT`, default `'unreviewed'`).
- `ConflictReviewStatus` is a two-value enum (`UNREVIEWED` / `REVIEWED`) for the MVP — enough to
  distinguish "needs human attention" from "a human has seen this," without inventing a fuller
  resolution workflow (dismissed, resolved-by-doc-update, etc.) before any UI/API needs it.
- `connect(db_path=DEFAULT_DB_PATH)` calls `memQrag.memory.long_term.connect()` (which itself
  chains through session and ingestion storage), so one `conflicts.records.connect()` call gets
  the full shared schema (`documents` / `chunks` / `session_memory` / `long_term_memory` /
  `conflicts`).
- `record_conflict(...)` inserts a row as `UNREVIEWED` and returns its id.
  `set_review_status(conn, id, status)` updates review status (raises if the id is unknown).
  `get_conflict_by_id()` and `get_all_conflicts()` (most recently detected first) are the read
  paths; no review-status filter yet — Phase 5 PR 4 can add one if the API needs it.

Consequences:

- Phase 5 PR 2 (entity and claim comparison) must decide, and record here, how opposing claims are
  extracted from retrieved chunks and when `record_conflict()` is called — this PR does not detect
  anything.
- Phase 5 PR 4 (`GET /api/conflicts`) reads via `get_all_conflicts()` (or a filtered variant); it
  should not invent a second storage shape for conflict rows.
- Conflicting claims must remain visible as conflicts (AGENTS.md / PROJECT_BLUEPRINT) — this
  schema stores both claims side by side and never picks a winner.
- Changing the `conflicts` column set, `ConflictReviewStatus` values, chunk-id storage shape, or
  moving this module under `memory` / `agent` later requires a new decision entry.

### Decision: Entity And Claim Comparison For Retrieved Chunks

Date: 2026-07-25

Status: accepted.

Context:

- The second Phase 5 PR implements "entity and claim comparison path for retrieved chunks."
  "SQLite Schema For Contradiction Records" deferred two questions here: how opposing claims are
  extracted from retrieved chunks, and when `record_conflict()` is called.
- AGENTS.md / PROJECT_BLUEPRINT forbid letting the LLM silently resolve (or hide) source
  contradictions. Using an LLM to *extract* claims would also pull Phase 6's agent/LLM provider
  choice into Phase 5 before that provider is selected, and would make detection
  non-deterministic and hard to unit-test. The demo corpus's intentional contradictions are
  quantitative policy facts (return windows, shipping times, warranties) — exactly the kind of
  claim a small deterministic pattern set can catch.
- Phase 5 PR 3 ("Flag conflicting factual claims in query responses") is a separate tracker item;
  this PR detects and persists, but does not shape API/response payloads.

Decision:

- Add `memQrag/conflicts/compare.py` with a deterministic, LLM-free path:
  - `extract_claims_from_text` / `extract_claims`: split chunk text into sentences, emit a claim
    only when a sentence matches a known entity pattern **and** contains a numeric value with a
    recognized unit (`days` / `hours` / `years` / `months` / `percent`). Entity labels are a
    fixed ordered list (`return window`, `shipping time`, `warranty`); first match wins.
    Values are normalized (`1 day` and `1 days` both become `"1 days"`) so unit inflection does
    not hide a real agreement or invent a false conflict. Sentences with numbers but no known
    entity are ignored — missing a conflict is preferred over inventing an unexplained entity.
  - `find_conflicting_claim_pairs`: group claims by entity, then by normalized value; emit one
    pair per unordered distinct-value combination whose representative claims come from
    **different** chunk ids (same-chunk restatements are not cross-source contradictions).
  - `detect_conflicts(conn, chunks)`: run extract -> compare -> `record_conflict` for each new
    pair, returning the `ConflictRecord`s found in this call. Input is any `ChunkLike` protocol
    (`chunk_id` + `text`), so `ScoredRetrievalResult` and test fakes both work without coupling
    this module to retrieval types. Idempotent: if an existing row already stores the same
    entity and the same two claim texts (either order), that row is returned and no duplicate
    is inserted. Chunk id lists on the row include every chunk that asserted each value, not
    just the first.
- Detection never picks a winner, never filters the input chunks, and never alters retrieval
  ranking — it only observes and records.

Consequences:

- Phase 5 PR 3 must decide how detected conflicts appear on query responses (likely by calling
  `detect_conflicts` on the final top-5 and attaching the returned records), without collapsing
  the two claims into one answer.
- Phase 5 PR 5's intentional contradictory fixture content should use the supported entity/value
  patterns (or this decision must be extended) so the fixture actually triggers detection.
- Expanding `_ENTITY_PATTERNS` / recognized units, switching to LLM-based extraction, or changing
  the idempotency key later requires a new decision entry.

### Decision: Flag Conflicting Factual Claims In Query Responses

Date: 2026-07-25

Status: accepted.

Context:

- The third Phase 5 PR implements "Flag conflicting factual claims in query responses."
  "Entity And Claim Comparison For Retrieved Chunks" deferred the response-shaping question
  here: how detected conflicts appear on query responses without collapsing the two claims into
  one answer.
- `POST /api/query` does not exist yet (Phase 7). Building a full query endpoint here would bundle
  agent orchestration into a Phase 5 tracker item. The PR-sized deliverable is the domain-level
  response evidence shape that Phase 7 will serialize — the same "call functions directly until a
  real orchestration need arises" precedent used for ingestion, retrieval, and memory.
- AGENTS.md / PROJECT_BLUEPRINT require conflicting claims to be shown as conflicts, not hidden
  inside a synthesized answer. The flagging layer must therefore carry both claims and must not
  choose between them.

Decision:

- Add `memQrag/conflicts/flagging.py`:
  - `ConflictWarning`: response-facing view of one conflict (`conflict_id`, `entity`, `claim_a`,
    `claim_b`, both chunk-id lists, `review_status`). Exposes `involved_chunk_ids`. Never omits
    either claim.
  - `ConflictFlaggedQueryEvidence`: `chunks` (input order preserved as a tuple) plus
    `conflicts` (tuple of warnings). Helpers: `conflicted_chunk_ids`, `chunk_is_conflicted`,
    `conflicts_for_chunk` — so a future API/UI can mark which citations participate in a conflict
    without re-deriving that set.
  - `flag_conflicting_claims(conn, chunks)`: calls `detect_conflicts` (so new conflicts are still
    persisted for `GET /api/conflicts` / human review), then wraps results as warnings. Does not
    generate answer text, filter chunks, re-rank, or prefer `claim_a` over `claim_b`.
- No HTTP endpoint in this PR — Phase 5 PR 4 owns `GET /api/conflicts`, and Phase 7 owns
  `POST /api/query`. Both will consume these types (or serialize fields from them) rather than
  inventing a second conflict shape.

Consequences:

- Phase 7's query response schema must include a conflicts / warnings array that maps from
  `ConflictWarning` (both claims required). Answering as if one claim were definitive when
  warnings are non-empty would violate this decision.
- Phase 8's contradiction alert reads the same warnings (or the API's serialization of them).
- Changing the warning field set, moving flagging under `agent`/`api`, or having flagging skip
  persistence (detect-only without `record_conflict`) later requires a new decision entry.
