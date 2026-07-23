# Agent Instructions

You are working on memQrag, a production RAG system with persistent memory.

## Required Workflow

1. Read `docs/PRODUCT_TIMELINE.md` before starting any work.
2. Work on the first unchecked item unless the user explicitly overrides it.
3. Keep every change PR-sized and focused.
4. Do not build product features during project-rails work.
5. Do not silently invent architecture; update `docs/DECISIONS.md` when a meaningful product or technical decision is made.
6. Run the relevant verification command before claiming completion.
7. Update `docs/PRODUCT_TIMELINE.md` only when the tracked item is actually completed.
8. If a PR workflow is in use, mark exactly one completed item `[x]` and add the PR number.
9. Mention the next unchecked item in final summaries.

## Project Boundaries

- Backend code belongs under `memQrag/`.
- Demo UI code belongs under `ui/`.
- Sample documents belong under a future sample-data directory and must be fictional.
- SQLite stores document metadata, session memory, long-term memory, conflict records, and staleness review state.
- ChromaDB stores vector embeddings and chunk references.
- The side-by-side standard RAG vs memQrag comparison is the most important demo feature.

## Do Not

- Do not skip the tracker.
- Do not bundle unrelated product systems into one PR.
- Do not claim completion without evidence.
- Do not overwrite user changes.
- Do not continue from memory after a merge; sync main and reread the tracker.
- Do not let the LLM silently resolve source contradictions.
- Do not hide low confidence retrieval behind confident answer wording.

## Verification Standard

Every implementation PR should include the strongest relevant checks available at that stage:

- formatting and linting;
- unit tests for domain logic;
- API tests for FastAPI endpoints;
- UI build checks for React;
- smoke checks for Docker Compose once Docker support exists;
- manual demo notes when visual behavior is involved.

If a check cannot run yet because the project is still scaffolding, document that explicitly in the final summary.

## PR Standard

Every PR should include:

- one clear purpose;
- docs updated when behavior, scope, or decisions change;
- tests or documented checks;
- product timeline update when the PR is opened;
- concise verification evidence.
