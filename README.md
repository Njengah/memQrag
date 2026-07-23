# memQrag

Production RAG with persistent retrieval memory for teams that need cited answers, visible confidence, and reviewable retrieval behavior.

## Status

Current stage: project rails.

Product features are not built yet. This repository currently defines the project scope, architecture boundaries, roadmap, and progress tracker.

## Why This Exists

Most RAG demos treat every query as stateless. memQrag is designed to remember which documents were useful for similar questions, surface stale or contradictory sources, and make the memory advantage visible through a side-by-side demo against standard RAG.

## What It Will Do

- Ingest PDF, DOCX, TXT, and Markdown documents into a semantic chunking pipeline.
- Combine dense ChromaDB retrieval, BM25 retrieval, Reciprocal Rank Fusion, reranking, and confidence scoring.
- Maintain session and long-term retrieval memory in SQLite.
- Detect frequently retrieved stale documents and contradictory source claims.
- Orchestrate factual, comparative, and multi-hop queries through an agentic query layer.
- Provide a React + Tailwind demo UI with a split-panel standard RAG vs memQrag comparison.

## What Is Not In Scope Yet

- Hosted multi-tenant SaaS behavior.
- Authentication, billing, or organization management.
- Production observability beyond the checks needed for the local MVP.
- Fine-tuning, custom model training, or proprietary model hosting.
- Building product features before the tracked project rails are in place.

## Planned Stack

- Python
- FastAPI
- LangChain
- ChromaDB
- SQLite
- React
- Tailwind CSS
- Docker Compose

## Quick Start

No runnable product exists yet.

The planned local setup target is:

```bash
docker compose up --build
```

Do not add setup commands here until the corresponding implementation exists and has been verified.

## Project Docs

- [Project blueprint](./docs/PROJECT_BLUEPRINT.md)
- [Product timeline](./docs/PRODUCT_TIMELINE.md)
- [Roadmap](./docs/ROADMAP.md)
- [Architecture](./docs/ARCHITECTURE.md)
- [Development cycle](./docs/DEVELOPMENT_CYCLE.md)
- [Decisions](./docs/DECISIONS.md)
- [Contributing](./CONTRIBUTING.md)

## License

MIT. See [`LICENSE`](./LICENSE).
