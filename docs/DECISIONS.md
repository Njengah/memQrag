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
