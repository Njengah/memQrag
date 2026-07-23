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
