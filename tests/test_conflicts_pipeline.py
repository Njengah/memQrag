"""End-to-end contradiction tests with intentional fixture content (Phase 5 PR 5).

Stitches Phase 5's detect -> flag -> list path against one shared fictional
policy corpus that intentionally contradicts on every entity pattern
`memQrag.conflicts.compare` recognizes (return window, shipping time,
warranty). Asserts the two Phase 5 exit criteria from
docs/PRODUCT_TIMELINE.md directly:

- Contradictory retrieved chunks are visible in API responses.
- Stored conflicts can be listed for human review.

Each conflicts module already has focused unit tests
(test_conflicts_records/compare/flagging.py) and the HTTP list path has
test_api_conflicts.py; this file only proves they compose against
intentional cross-document fixture content shaped for the supported
entity/value patterns. See docs/DECISIONS.md ("Intentional Contradictory
Fixture Content Tests").
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from memQrag.api.app import create_app
from memQrag.api.deps import get_db
from memQrag.conflicts.flagging import flag_conflicting_claims
from memQrag.conflicts.records import ConflictReviewStatus, connect, get_all_conflicts
from memQrag.retrieval.confidence import ConfidenceLevel, ScoredRetrievalResult

# Intentional contradictions across fictional policy documents. Phrasing
# matches the entity/value patterns in memQrag.conflicts.compare so detection
# actually fires — Phase 8's demo corpus should follow the same shapes.
_CONTRADICTORY_CORPUS: tuple[tuple[str, str], ...] = (
    (
        "returns-policy-v1.txt",
        "Fictional Northwind returns are accepted within 30 days of purchase.",
    ),
    (
        "returns-policy-v2.txt",
        "Fictional Northwind returns must be made within 14 days of delivery.",
    ),
    (
        "shipping-standard.txt",
        "Standard shipping for fictional Northwind orders arrives in 2 days.",
    ),
    (
        "shipping-economy.txt",
        "Delivery for fictional Northwind orders arrives in 5 days.",
    ),
    (
        "warranty-basic.txt",
        "The fictional Northwind warranty lasts 1 year.",
    ),
    (
        "warranty-premium.txt",
        "The fictional Northwind warranty lasts 2 years.",
    ),
)

# Same return-window value from a second source — must not invent a conflict
# when retrieved alone with returns-policy-v1.
_AGREEING_RETURN_PEER = (
    "returns-policy-faq.txt",
    "The fictional Northwind return window is 30 days.",
)

_FILLER = (
    "bakery-notes.txt",
    "A fictional bakery introduced a new sourdough recipe this spring.",
)

_SUPPORTED_ENTITIES = frozenset({"return window", "shipping time", "warranty"})
_TEST_DB_DIR = Path("data") / "test-dbs"


def _scored_chunk(
    chunk_id: int,
    source_document: str,
    text: str,
    *,
    final_rank: int,
) -> ScoredRetrievalResult:
    """Build a realistic retrieved-chunk stand-in (satisfies ChunkLike)."""
    return ScoredRetrievalResult(
        chunk_id=chunk_id,
        document_id=chunk_id,
        text=text,
        source_document=source_document,
        page_number=1,
        section_heading=None,
        dense_score=0.9,
        sparse_rank=chunk_id,
        fused_rank=chunk_id,
        rerank_score=0.8,
        final_rank=final_rank,
        confidence_level=ConfidenceLevel.HIGH,
    )


def _corpus_chunks(
    corpus: tuple[tuple[str, str], ...],
    *,
    start_id: int = 1,
) -> list[ScoredRetrievalResult]:
    return [
        _scored_chunk(start_id + index, source, text, final_rank=index + 1)
        for index, (source, text) in enumerate(corpus)
    ]


@pytest.fixture
def conn():
    connection = connect(":memory:")
    yield connection
    connection.close()


@pytest.fixture
def contradictory_chunks() -> list[ScoredRetrievalResult]:
    return _corpus_chunks(_CONTRADICTORY_CORPUS)


def test_contradictory_retrieved_chunks_visible_on_query_evidence(conn, contradictory_chunks):
    """Exit criterion: Contradictory retrieved chunks are visible in API responses.

    Phase 7's POST /api/query will serialize ConflictFlaggedQueryEvidence;
    this asserts that shape already surfaces both claims without picking a
    winner or dropping either side.
    """
    evidence = flag_conflicting_claims(conn, contradictory_chunks)

    assert evidence.chunks == tuple(contradictory_chunks)
    assert len(evidence.conflicts) == 3
    for warning in evidence.conflicts:
        assert warning.claim_a
        assert warning.claim_b
        assert warning.claim_a != warning.claim_b
        assert warning.review_status is ConflictReviewStatus.UNREVIEWED
        assert warning.claim_a_chunk_ids
        assert warning.claim_b_chunk_ids
        assert set(warning.claim_a_chunk_ids).isdisjoint(warning.claim_b_chunk_ids)

    assert evidence.conflicted_chunk_ids == frozenset(
        chunk.chunk_id for chunk in contradictory_chunks
    )


def test_stored_conflicts_from_fixture_listed_for_human_review(conn, contradictory_chunks):
    """Exit criterion: Stored conflicts can be listed for human review."""
    flag_conflicting_claims(conn, contradictory_chunks)

    listed = get_all_conflicts(conn)

    assert len(listed) == 3
    entities = {record.entity for record in listed}
    assert entities == _SUPPORTED_ENTITIES
    for record in listed:
        assert record.claim_a != record.claim_b
        assert record.review_status is ConflictReviewStatus.UNREVIEWED


def test_fixture_covers_each_supported_entity_conflict(conn, contradictory_chunks):
    """Corpus must trigger one conflict per compare.py entity pattern."""
    evidence = flag_conflicting_claims(conn, contradictory_chunks)

    by_entity = {warning.entity: warning for warning in evidence.conflicts}
    assert set(by_entity) == _SUPPORTED_ENTITIES

    return_values = {by_entity["return window"].claim_a, by_entity["return window"].claim_b}
    assert any("30 days" in claim for claim in return_values)
    assert any("14 days" in claim for claim in return_values)

    shipping_values = {by_entity["shipping time"].claim_a, by_entity["shipping time"].claim_b}
    assert any("2 days" in claim for claim in shipping_values)
    assert any("5 days" in claim for claim in shipping_values)

    warranty_values = {by_entity["warranty"].claim_a, by_entity["warranty"].claim_b}
    assert any("1 year" in claim for claim in warranty_values)
    assert any("2 years" in claim for claim in warranty_values)


def test_agreeing_and_filler_fixture_peers_do_not_create_false_conflicts(conn):
    agreeing = _corpus_chunks(
        (_CONTRADICTORY_CORPUS[0], _AGREEING_RETURN_PEER, _FILLER),
    )

    evidence = flag_conflicting_claims(conn, agreeing)

    assert evidence.conflicts == ()
    assert evidence.conflicted_chunk_ids == frozenset()
    assert get_all_conflicts(conn) == []
    assert evidence.chunks == tuple(agreeing)


def test_fixture_conflicts_listable_via_get_api_conflicts(contradictory_chunks):
    """Human-review list path reads the same rows the fixture detection wrote."""
    _TEST_DB_DIR.mkdir(parents=True, exist_ok=True)
    db_path = _TEST_DB_DIR / f"conflicts-pipeline-{uuid.uuid4().hex}.db"

    seed = connect(db_path)
    try:
        flag_conflicting_claims(seed, contradictory_chunks)
    finally:
        seed.close()

    def override_get_db():
        connection = connect(db_path)
        try:
            yield connection
        finally:
            connection.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            response = client.get("/api/conflicts")
    finally:
        app.dependency_overrides.clear()
        db_path.unlink(missing_ok=True)

    assert response.status_code == 200
    payload = response.json()["conflicts"]
    assert len(payload) == 3
    assert {item["entity"] for item in payload} == _SUPPORTED_ENTITIES
    for item in payload:
        assert item["claim_a"]
        assert item["claim_b"]
        assert item["claim_a"] != item["claim_b"]
