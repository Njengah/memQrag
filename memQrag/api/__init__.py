"""API module boundary.

Planned responsibility, per docs/ARCHITECTURE.md: the FastAPI app, request
and response schemas, endpoint handlers, and dependency wiring.

The FastAPI app (`memQrag.api.app.create_app`) currently exposes:
- `GET /health` — unprefixed infrastructure liveness probe;
- `GET /api/conflicts` — list stored contradiction records (Phase 5).

Remaining business endpoints (`POST /api/ingest`, `POST /api/query`, etc.)
land in Phase 7 of docs/PRODUCT_TIMELINE.md.
"""
