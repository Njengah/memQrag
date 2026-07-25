"""Tests for memQrag.conflicts.compare (entity/claim comparison, Phase 5 PR 2)."""

from dataclasses import dataclass

import pytest

from memQrag.conflicts.compare import (
    ExtractedClaim,
    detect_conflicts,
    extract_claims,
    extract_claims_from_text,
    find_conflicting_claim_pairs,
)
from memQrag.conflicts.records import connect, get_all_conflicts


@dataclass(frozen=True)
class _Chunk:
    chunk_id: int
    text: str


@pytest.fixture
def conn():
    connection = connect(":memory:")
    yield connection
    connection.close()


# -- extract_claims_from_text ----------------------------------------------


def test_extract_claims_from_text_finds_return_window_with_days():
    claims = extract_claims_from_text(
        1, "Fictional returns are accepted within 30 days of purchase."
    )

    assert len(claims) == 1
    assert claims[0].entity == "return window"
    assert claims[0].value == "30 days"
    assert claims[0].chunk_id == 1


def test_extract_claims_from_text_normalizes_singular_and_plural_units():
    claims = extract_claims_from_text(1, "The return window is 1 day for flash sales.")

    assert claims[0].value == "1 days"


def test_extract_claims_from_text_ignores_numbers_without_a_known_entity():
    claims = extract_claims_from_text(1, "The fictional warehouse holds 30 pallets of stock.")

    assert claims == []


def test_extract_claims_from_text_returns_empty_for_blank_text():
    assert extract_claims_from_text(1, "   ") == []


def test_extract_claims_from_text_finds_shipping_and_warranty_entities():
    shipping = extract_claims_from_text(1, "Fictional shipping takes 5 days on average.")
    warranty = extract_claims_from_text(2, "The fictional warranty lasts 2 years.")

    assert shipping[0].entity == "shipping time"
    assert shipping[0].value == "5 days"
    assert warranty[0].entity == "warranty"
    assert warranty[0].value == "2 years"


# -- find_conflicting_claim_pairs ------------------------------------------


def test_find_conflicting_claim_pairs_detects_different_values_same_entity():
    claims = [
        ExtractedClaim("return window", "30 days", "Returns within 30 days.", 1),
        ExtractedClaim("return window", "14 days", "Returns within 14 days.", 2),
    ]

    pairs = find_conflicting_claim_pairs(claims)

    assert len(pairs) == 1
    assert pairs[0].entity == "return window"
    assert {pairs[0].claim_a.value, pairs[0].claim_b.value} == {"30 days", "14 days"}


def test_find_conflicting_claim_pairs_ignores_matching_values():
    claims = [
        ExtractedClaim("return window", "30 days", "Returns within 30 days.", 1),
        ExtractedClaim("return window", "30 days", "The return window is 30 days.", 2),
    ]

    assert find_conflicting_claim_pairs(claims) == []


def test_find_conflicting_claim_pairs_ignores_same_chunk_restating_itself():
    claims = [
        ExtractedClaim("return window", "30 days", "Returns within 30 days.", 1),
        ExtractedClaim("return window", "14 days", "Or maybe 14 days elsewhere.", 1),
    ]

    assert find_conflicting_claim_pairs(claims) == []


def test_find_conflicting_claim_pairs_ignores_different_entities():
    claims = [
        ExtractedClaim("return window", "30 days", "Returns within 30 days.", 1),
        ExtractedClaim("shipping time", "5 days", "Shipping takes 5 days.", 2),
    ]

    assert find_conflicting_claim_pairs(claims) == []


# -- detect_conflicts ------------------------------------------------------


def test_detect_conflicts_persists_a_conflict_for_opposing_return_windows(conn):
    chunks = [
        _Chunk(1, "Fictional returns are accepted within 30 days of purchase."),
        _Chunk(2, "Fictional returns must be made within 14 days."),
    ]

    detected = detect_conflicts(conn, chunks)

    assert len(detected) == 1
    assert detected[0].entity == "return window"
    assert {detected[0].claim_a, detected[0].claim_b} == {
        chunks[0].text,
        chunks[1].text,
    }
    assert set(detected[0].claim_a_chunk_ids) | set(detected[0].claim_b_chunk_ids) == {1, 2}
    assert get_all_conflicts(conn) == detected


def test_detect_conflicts_is_idempotent_for_the_same_claim_pair(conn):
    chunks = [
        _Chunk(1, "Fictional returns are accepted within 30 days of purchase."),
        _Chunk(2, "Fictional returns must be made within 14 days."),
    ]

    first = detect_conflicts(conn, chunks)
    second = detect_conflicts(conn, chunks)

    assert len(first) == 1
    assert len(second) == 1
    assert first[0].id == second[0].id
    assert len(get_all_conflicts(conn)) == 1


def test_detect_conflicts_returns_empty_when_chunks_agree(conn):
    chunks = [
        _Chunk(1, "Fictional returns are accepted within 30 days of purchase."),
        _Chunk(2, "The fictional return window is 30 days."),
    ]

    assert detect_conflicts(conn, chunks) == []
    assert get_all_conflicts(conn) == []


def test_detect_conflicts_returns_empty_for_no_extractable_claims(conn):
    chunks = [_Chunk(1, "A fictional bakery introduced a new sourdough recipe.")]

    assert detect_conflicts(conn, chunks) == []


def test_extract_claims_reads_chunk_like_objects():
    chunks = [
        _Chunk(10, "Fictional shipping takes 2 days door to door."),
        _Chunk(11, "Fictional delivery arrives in 5 days."),
    ]

    claims = extract_claims(chunks)

    assert [claim.chunk_id for claim in claims] == [10, 11]
    assert {claim.value for claim in claims} == {"2 days", "5 days"}
