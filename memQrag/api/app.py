"""FastAPI application factory for memQrag.

This wires together the FastAPI app instance. Most business endpoints
(`POST /api/ingest`, `POST /api/query`, etc.) land in Phase 7 per
docs/PRODUCT_TIMELINE.md; Phase 5 adds `GET /api/conflicts` early so
stored contradictions are listable for human review before the full
query API exists.
"""

from fastapi import FastAPI

from memQrag.api.conflicts import router as conflicts_router
from memQrag.api.health import router as health_router


def create_app() -> FastAPI:
    """Build and return the memQrag FastAPI application."""
    app = FastAPI(
        title="memQrag",
        description="Production RAG system with persistent retrieval memory.",
        version="0.1.0",
    )
    app.include_router(health_router)
    app.include_router(conflicts_router)
    return app


app = create_app()
