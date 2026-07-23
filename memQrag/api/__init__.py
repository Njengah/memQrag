"""API module boundary.

Planned responsibility, per docs/ARCHITECTURE.md: the FastAPI app, request
and response schemas, endpoint handlers, and dependency wiring.

The FastAPI app (`memQrag.api.app.create_app`) currently exposes only the
`/health` infrastructure endpoint. Business endpoints (`/api/...`) land in
Phase 7 of docs/PRODUCT_TIMELINE.md.
"""
