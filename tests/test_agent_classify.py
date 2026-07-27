"""Tests for memQrag.agent.classify (query classification, Phase 6 PR 1)."""

import pytest

from memQrag.agent.classify import QueryType, classify_query


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("What is the fictional return window?", QueryType.FACTUAL),
        ("How long does fictional shipping take?", QueryType.FACTUAL),
        ("When does the fictional warranty expire?", QueryType.FACTUAL),
        ("Tell me the fictional Northwind return policy.", QueryType.FACTUAL),
        ("Does fictional Northwind accept returns?", QueryType.FACTUAL),
        ("How many days is the fictional return window?", QueryType.FACTUAL),
    ],
)
def test_classify_query_factual_examples(query, expected):
    result = classify_query(query)
    assert result.query_type is expected
    assert result.normalized_query == query.strip()


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        (
            "Compare the fictional return window and the fictional shipping time.",
            QueryType.COMPARATIVE,
        ),
        ("What is the difference between warranty v1 and warranty v2?", QueryType.COMPARATIVE),
        ("Returns versus shipping: which policy is stricter?", QueryType.COMPARATIVE),
        ("How does the basic warranty differ from the premium warranty?", QueryType.COMPARATIVE),
        ("Which is better, 14-day returns or 30-day returns?", QueryType.COMPARATIVE),
        ("Contrast fictional economy shipping vs standard shipping.", QueryType.COMPARATIVE),
    ],
)
def test_classify_query_comparative_examples(query, expected):
    assert classify_query(query).query_type is expected


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        (
            "What is the return window for the product that ships in 2 days, "
            "and then what is its warranty?",
            QueryType.MULTI_HOP,
        ),
        (
            "Find the fictional product with a 14-day return window and then "
            "tell me its shipping time.",
            QueryType.MULTI_HOP,
        ),
        (
            "If fictional Northwind ships in 5 days, what is the return window?",
            QueryType.MULTI_HOP,
        ),
        (
            "What is the fictional return window and when does shipping arrive?",
            QueryType.MULTI_HOP,
        ),
        (
            "Identify the premium warranty policy based on that result.",
            QueryType.MULTI_HOP,
        ),
    ],
)
def test_classify_query_multi_hop_examples(query, expected):
    assert classify_query(query).query_type is expected


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("", QueryType.UNKNOWN),
        ("   ", QueryType.UNKNOWN),
        ("hello", QueryType.UNKNOWN),
        ("thanks!", QueryType.UNKNOWN),
        ("asdf qwerty", QueryType.UNKNOWN),
        ("please", QueryType.UNKNOWN),
    ],
)
def test_classify_query_unknown_examples(query, expected):
    assert classify_query(query).query_type is expected


def test_classify_query_prefers_comparative_over_multi_hop_when_both_match():
    # Explicit compare lexicon wins even with an "and then" connector.
    query = "Compare returns and shipping and then contrast their warranties."
    assert classify_query(query).query_type is QueryType.COMPARATIVE


def test_classify_query_compound_topic_with_one_interrogative_is_factual():
    # One "what" + compound nouns is a single-hop lookup, not multi-hop.
    query = "What are the fictional return and shipping policies?"
    assert classify_query(query).query_type is QueryType.FACTUAL


def test_classify_query_strips_surrounding_whitespace():
    result = classify_query("  What is the fictional warranty?  ")
    assert result.query_type is QueryType.FACTUAL
    assert result.normalized_query == "What is the fictional warranty?"
