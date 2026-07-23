# Contributing to memQrag

memQrag is developed tracker-first: [`docs/PRODUCT_TIMELINE.md`](./docs/PRODUCT_TIMELINE.md) is the
source of truth for what gets built next, for both human and AI-assisted contributions.

## Before You Start

1. Read [`README.md`](./README.md), [`docs/PROJECT_BLUEPRINT.md`](./docs/PROJECT_BLUEPRINT.md), and
   [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) to understand the product goal and boundaries.
2. Read [`docs/PRODUCT_TIMELINE.md`](./docs/PRODUCT_TIMELINE.md) and work on the first unchecked
   item unless a maintainer explicitly asks for something else.
3. Read [`docs/DEVELOPMENT_CYCLE.md`](./docs/DEVELOPMENT_CYCLE.md) for the full workflow this
   project follows before, during, and after a change.
4. Sync the default branch and create a focused branch for your change.

## Project Boundaries

- Backend code belongs under `memQrag/`.
- Demo UI code belongs under `ui/`.
- Sample documents belong under a future sample-data directory and must be fictional; never add
  real company or personal data.
- Do not build product features while project-rails or scaffolding items are still open.
- Do not silently invent architecture. If a change implies a meaningful product or technical
  decision, add an entry to [`docs/DECISIONS.md`](./docs/DECISIONS.md) using the template there.

## Pull Request Expectations

Every pull request should:

- have one clear purpose and stay small enough to review in one pass (see "PR Size Guidance" in
  `docs/DEVELOPMENT_CYCLE.md`);
- avoid bundling unrelated product systems together;
- update docs when behavior, scope, or decisions change;
- include the strongest relevant verification for the change (formatting/linting, unit tests, API
  tests, UI build checks, or documented manual checks when automated checks are not yet possible);
- update `docs/PRODUCT_TIMELINE.md` by checking off exactly the completed item and recording the PR
  number, only once the PR is opened;
- report the next unchecked timeline item in the PR description or summary.

## Code Style

Formatting, linting, and type-checking tooling will be documented here once the corresponding
scaffolding lands (see Phase 1 of `docs/PRODUCT_TIMELINE.md`). Until then, match the existing style
of the surrounding files.

## Reporting Issues

Open a GitHub issue describing the problem or proposal, including which part of the architecture or
timeline it affects. Do not include real company data, credentials, or secrets in issues, PRs, or
sample data.

## Code of Conduct

Be respectful and constructive. Disagreements about architecture or scope should be resolved by
referencing `docs/PROJECT_BLUEPRINT.md`, `docs/ARCHITECTURE.md`, and `docs/DECISIONS.md`, or by
proposing a new decision entry for maintainer review.
