"""Tests for memQrag.ingestion.embeddings (Phase 2 PR 3).

This module downloads a small ONNX model from the Hugging Face Hub on first
use, which needs network access. These tests skip gracefully (instead of
failing) if that download is not possible, so CI network issues do not
block unrelated work; see docs/DECISIONS.md ("Sentence Embedding Model For
Semantic Chunking"). The chunking algorithm itself is tested separately in
tests/test_ingestion_chunking.py using a fake, network-free embedder.
"""

import pytest

from memQrag.ingestion.embeddings import embed_sentences


@pytest.fixture(scope="module")
def embedded_sentences():
    try:
        return embed_sentences(["The cat sat on the mat.", "The car is parked outside."])
    except Exception as exc:  # any failure here means "can't run this in this environment"
        pytest.skip(f"Could not load the sentence embedding model: {exc}")


def test_embed_sentences_returns_one_vector_per_sentence(embedded_sentences):
    assert len(embedded_sentences) == 2


def test_embed_sentences_returns_non_empty_float_vectors(embedded_sentences):
    for vector in embedded_sentences:
        assert len(vector) > 0
        assert all(isinstance(value, float) for value in vector)


def test_embed_sentences_returns_empty_list_for_no_input():
    assert embed_sentences([]) == []
