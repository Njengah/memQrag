"""FastAPI application factory for memQrag.

This wires together the FastAPI app instance. Business endpoints
(`POST /api/ingest`, `POST /api/query`, etc.) land in Phase 7 per
docs/PRODUCT_TIMELINE.md; only the infrastructure health check exists so
far.
"""

from fastapi import FastAPI

from memQrag.api.health import router as health_router


def create_app() -> FastAPI:
    """Build and return the memQrag FastAPI application."""
    app = FastAPI(
        title="memQrag",
        description="Production RAG system with persistent retrieval memory.",
        version="0.1.0",
    )
    app.include_router(health_router)
    return app


app = create_app()
