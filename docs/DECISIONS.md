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
