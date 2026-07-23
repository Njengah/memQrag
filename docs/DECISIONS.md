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
  - `frontend`: `npm ci` in `ui/`, then `npm run lint`, `npm run build`.
- Add `scripts/check.sh` (POSIX) and `scripts/check.ps1` (PowerShell) that run the same checks
  locally in the same order, so a contributor gets identical results locally and in CI.

Consequences:

- Every future PR gets backend lint/format/tests and frontend lint/build checked automatically by
  CI, satisfying the Phase 1 exit criterion "Backend and frontend smoke checks pass."
- Contributors must run `ruff format .` (not just `ruff check .`) before committing Python changes,
  or CI's `ruff format --check .` step fails the PR.
- Adding a frontend formatter, a type checker beyond `tsc`, or additional CI jobs (e.g. Docker
  Compose smoke tests once Docker is available in CI) requires a new decision entry.
