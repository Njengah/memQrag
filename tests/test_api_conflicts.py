"""API tests for `GET /api/conflicts` (Phase 5 PR 4).

Uses a per-test SQLite file under `data/` (gitignored) via FastAPI
dependency override so these tests never touch `data/memqrag.db` and never
share state. Avoids pytest's `tmp_path` (which can hit Windows permission
errors on the shared pytest temp root).
"""

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from memQrag.api.app import create_app
from memQrag.api.deps import get_db
from memQrag.conflicts.records import ConflictReviewStatus, connect, record_conflict

_TEST_DB_DIR = Path("data") / "test-dbs"


@pytest.fixture
def client():
    _TEST_DB_DIR.mkdir(parents=True, exist_ok=True)
    db_path = _TEST_DB_DIR / f"conflicts-{uuid.uuid4().hex}.db"

    def override_get_db():
        conn = connect(db_path)
        try:
            yield conn
        finally:
            conn.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client, db_path
    finally:
        app.dependency_overrides.clear()
        db_path.unlink(missing_ok=True)


def test_list_conflicts_returns_empty_list_when_none_stored(client):
    test_client, _db_path = client

    response = test_client.get("/api/conflicts")

    assert response.status_code == 200
    assert response.json() == {"conflicts": []}


def test_list_conflicts_returns_both_claims_for_each_stored_conflict(client):
    test_client, db_path = client
    conn = connect(db_path)
    try:
        record_conflict(
            conn,
            entity="return window",
            claim_a="Fictional returns are accepted within 30 days.",
            claim_b="Fictional returns must be made within 14 days.",
            claim_a_chunk_ids=[1],
            claim_b_chunk_ids=[2],
        )
    finally:
        conn.close()

    response = test_client.get("/api/conflicts")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["conflicts"]) == 1
    conflict = payload["conflicts"][0]
    assert conflict["entity"] == "return window"
    assert conflict["claim_a"] == "Fictional returns are accepted within 30 days."
    assert conflict["claim_b"] == "Fictional returns must be made within 14 days."
    assert conflict["claim_a_chunk_ids"] == [1]
    assert conflict["claim_b_chunk_ids"] == [2]
    assert conflict["review_status"] == ConflictReviewStatus.UNREVIEWED.value
    assert "detected_at" in conflict
    assert conflict["id"] == 1


def test_list_conflicts_returns_most_recently_detected_first(client):
    test_client, db_path = client
    conn = connect(db_path)
    try:
        older_id = record_conflict(
            conn,
            entity="shipping time",
            claim_a="Shipping takes 2 days.",
            claim_b="Delivery arrives in 5 days.",
            claim_a_chunk_ids=[1],
            claim_b_chunk_ids=[2],
        )
        newer_id = record_conflict(
            conn,
            entity="return window",
            claim_a="Returns within 30 days.",
            claim_b="Returns within 14 days.",
            claim_a_chunk_ids=[3],
            claim_b_chunk_ids=[4],
        )
    finally:
        conn.close()

    response = test_client.get("/api/conflicts")

    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["conflicts"]]
    assert ids == [newer_id, older_id]


def test_list_conflicts_never_omits_either_claim(client):
    """Regression guard for AGENTS.md: do not silently resolve contradictions."""
    test_client, db_path = client
    conn = connect(db_path)
    try:
        record_conflict(
            conn,
            entity="warranty",
            claim_a="Warranty lasts 1 year.",
            claim_b="Warranty lasts 2 years.",
            claim_a_chunk_ids=[10],
            claim_b_chunk_ids=[11],
        )
    finally:
        conn.close()

    conflict = test_client.get("/api/conflicts").json()["conflicts"][0]

    assert conflict["claim_a"]
    assert conflict["claim_b"]
    assert conflict["claim_a"] != conflict["claim_b"]
