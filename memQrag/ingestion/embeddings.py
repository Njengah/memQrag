"""Sentence embedding provider for semantic chunking (Phase 2 PR 3).

Wraps fastembed's default dense text model behind a plain function so
`memQrag.ingestion.chunking` depends only on a
`Callable[[Sequence[str]], Sequence[Sequence[float]]]` shape, not on
fastembed directly. See docs/DECISIONS.md ("Sentence Embedding Model For
Semantic Chunking") for why fastembed was chosen over sentence-transformers.

Loading the model downloads cached weights on first use, which needs network
access the first time it runs on a machine. `memQrag.ingestion.chunking`'s
own tests use a fake embedding function instead of this module, so its
algorithm is not affected if this module's model is unavailable.
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache

from fastembed import TextEmbedding

MODEL_NAME = "BAAI/bge-small-en-v1.5"


@lru_cache(maxsize=1)
def _model() -> TextEmbedding:
    return TextEmbedding(model_name=MODEL_NAME)


def embed_sentences(sentences: Sequence[str]) -> list[list[float]]:
    """Return one dense embedding vector per input sentence, in order."""
    if not sentences:
        return []
    return [vector.tolist() for vector in _model().embed(list(sentences))]
