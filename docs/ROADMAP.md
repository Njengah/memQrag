# Roadmap

This roadmap describes product direction. Use [`docs/PRODUCT_TIMELINE.md`](./PRODUCT_TIMELINE.md) for PR-level tracking.

## Milestone 0: Project Rails

Goal:

> Make memQrag clear enough for humans and agents to work safely before feature implementation begins.

Expected outcomes:

- README explains the idea, status, planned stack, and docs map.
- Project blueprint defines users, goals, non-goals, MVP, workflows, and safety boundaries.
- Product timeline tracks PR-sized work.
- Agent instructions define working rules.
- Architecture doc captures initial module boundaries.
- Decisions log records accepted starting constraints.

## Milestone 1: Runnable Foundation

Goal:

> Create a local full-stack skeleton that proves the repository shape.

Expected outcomes:

- Python package exists under `memQrag/`.
- FastAPI app has a health endpoint and test harness.
- React + Tailwind demo shell exists.
- Docker Compose starts the local services.
- ChromaDB and SQLite are represented in the runtime shape, even before full behavior is implemented.

## Milestone 2: Ingestion And Retrieval MVP

Goal:

> Turn supported documents into retrievable, cited chunks.

Expected outcomes:

- PDF, DOCX, TXT, and Markdown can be ingested.
- Semantic chunking respects the 200-token merge and 800-token split boundaries.
- Metadata is stored in SQLite.
- Vectors are stored in ChromaDB.
- Hybrid retrieval combines dense search, BM25, RRF, reranking, and confidence labels.

## Milestone 3: Memory Advantage

Goal:

> Make persistent retrieval memory affect answer quality in a demonstrable way.

Expected outcomes:

- Session memory records useful retrieved chunks.
- Long-term memory tracks query patterns and successful documents.
- Similar future queries boost previously successful documents.
- Memory decay reduces stale low-value memories.
- Staleness alerts identify old frequently retrieved documents.

## Milestone 4: Trust Signals

Goal:

> Make uncertainty, stale sources, and contradictory evidence impossible to miss.

Expected outcomes:

- Contradictions are detected and stored.
- Low-confidence answers explicitly say they are low confidence.
- Citations include document name, chunk reference, excerpt, and confidence.
- The UI highlights stale and conflicting source states.

## Milestone 5: Killer Demo

Goal:

> Show why memQrag is different from stateless RAG.

Expected outcomes:

- Split panel compares standard RAG and memQrag answers for the same question.
- Memory panel shows what the system learned during the session.
- Fictional policy dataset triggers memory, staleness, and contradiction behavior immediately.
- README includes a verified one-command setup and demo walkthrough.

## Later

- Authentication and role-based access.
- Hosted deployment target.
- Advanced evaluation harness.
- Admin review workflow for stale and contradictory documents.
- Additional file types.
- Provider-specific optimization for embedding, reranking, and generation models.
