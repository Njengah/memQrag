# Development Cycle

Use this workflow for AI-assisted memQrag development.

## Before Work

1. Sync the default branch.
2. Read `docs/PRODUCT_TIMELINE.md`.
3. Confirm the first unchecked item unless the user explicitly overrides it.
4. Create a focused branch when working through PRs.
5. Read `docs/ARCHITECTURE.md` and `docs/DECISIONS.md` before changing system boundaries.

## During Work

1. Implement only the selected timeline item.
2. Keep product systems separate unless a testable integration requires touching both.
3. Add or update tests when the change is executable.
4. Update docs when behavior, scope, setup, or decisions change.
5. Keep unrelated cleanup out of the PR.
6. Do not mark tracker items complete before a PR exists.

## After Opening A PR

Only perform these steps when the user asked for a PR workflow and the repository has a configured remote.

1. Add the PR number to the matching timeline item.
2. Mark that item `[x]`.
3. Push the tracker commit.
4. Run or wait for verification.
5. Report the next unchecked item.

## Verification By Change Type

- Documentation-only rails: inspect expected files and run `git status --short`.
- Python backend: run formatter, lint, type checks when configured, and tests.
- FastAPI endpoints: run API tests and inspect generated or documented response shapes.
- Retrieval and memory logic: run deterministic unit tests with fixtures.
- React UI: run frontend lint, tests when configured, and production build.
- Docker Compose: run `docker compose up --build` or a documented smoke equivalent.

## Completion Evidence

A ready change should have:

- passing local checks or documented manual verification;
- passing CI when available;
- a clean understanding of expected uncommitted files;
- no unexpected generated artifacts;
- a timeline update when a PR is opened;
- the next unchecked item reported.

## PR Size Guidance

Keep PRs small enough to review in one pass. A good memQrag PR usually does one of:

- adds one module boundary;
- implements one algorithm with tests;
- exposes one endpoint with tests;
- adds one UI state or panel with build verification;
- updates one documented decision.
