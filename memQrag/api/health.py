"""Infrastructure health check endpoint.

This is a liveness probe, not a business endpoint. It intentionally lives
outside the `/api/...` business endpoint surface planned in Phase 7 of
docs/PRODUCT_TIMELINE.md (see docs/ARCHITECTURE.md "API Boundary"). Local
tooling and, eventually, Docker Compose health checks use this route.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["health"])
def get_health() -> dict[str, str]:
    """Return service liveness status."""
    return {"status": "ok"}
