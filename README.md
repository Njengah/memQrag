# memQrag

Python library for **RAG with persistent retrieval memory**: hybrid search, rerank, confidence, session/long-term memory, staleness, and source-conflict detection.

Most RAG stacks treat every query as stateless. memQrag remembers which chunks helped similar questions, down-weights stale sources, and surfaces contradictory claims instead of silently picking a winner.

## Status

**Library + tests through Phase 5, plus query classification.** Local FastAPI exposes `/health` and `GET /api/conflicts`. The React UI is a buildable shell (no chat/upload yet). Ingest and query HTTP endpoints are not wired (Phase 7).

| Layer | State |
|---|---|
| Ingestion (PDF/DOCX/TXT/MD → chunk → SQLite + Chroma) | Implemented, tested |
| Hybrid retrieval (dense + BM25 + RRF + rerank + confidence) | Implemented, tested |
| Memory (session, long-term, boost, decay, staleness) | Implemented, tested |
| Conflict records + `GET /api/conflicts` | Implemented, tested |
| Query classify (FACTUAL / COMPARATIVE / MULTI-HOP / UNKNOWN) | Implemented, tested |
| Multi-hop synthesis, `POST /api/ingest`, `POST /api/query` | Not built |
| Chat UI / side-by-side demo | Not built |

## Setup

Python 3.11+:

```bash
python -m pip install -e ".[dev]"
pytest -q
```

API (health):

```bash
uvicorn memQrag.api.app:app --reload --port 8000
```

`GET http://127.0.0.1:8000/health` → `{"status":"ok"}`.

Optional full stack (API + UI shell + Chroma):

```bash
docker compose up --build
```

UI shell (placeholder only):

```bash
cd ui && npm install && npm run dev
```

## Why it exists

- Hybrid retrieval: Chroma dense + BM25 sparse, Reciprocal Rank Fusion, cross-encoder rerank, HIGH/MEDIUM/LOW confidence.
- Memory: SQLite session and long-term records, boost for similar past queries, decay after 30 days of low hits, staleness flag for hot docs older than 90 days.
- Conflicts: contradictory claims stored and listed for review.
- Not in scope: hosted SaaS, auth, billing, live multi-tenant deploy.

## Docs

- [Product timeline](./docs/PRODUCT_TIMELINE.md) — what is done vs next
- [Architecture](./docs/ARCHITECTURE.md)
- [Contributing](./CONTRIBUTING.md)

## License

MIT. See [`LICENSE`](./LICENSE).
