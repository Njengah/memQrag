"""API tests for the infrastructure health endpoint.

This establishes the FastAPI test harness pattern (TestClient against an
app built by `create_app()`) that later Phase 7 business endpoint tests
will follow.
"""

from fastapi.testclient import TestClient

from memQrag.api.app import create_app


def test_health_endpoint_returns_ok_status():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
