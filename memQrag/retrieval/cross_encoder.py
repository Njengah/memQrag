"""Cross-encoder relevance scorer for reranking (Phase 3 PR 4).

Wraps fastembed's ONNX-runtime cross-encoder behind a plain function so
`memQrag.retrieval.rerank` depends only on a
`Callable[[str, Sequence[str]], Sequence[float]]` shape, not on fastembed
directly — mirroring `memQrag.ingestion.embeddings.embed_sentences`. See
docs/DECISIONS.md ("Cross-Encoder Reranking Model And Final Top-5
Selection") for why `Xenova/ms-marco-MiniLM-L-6-v2` was chosen.

Loading the model downloads cached weights on first use, which needs
network access the first time it runs on a machine. `memQrag.retrieval.rerank`'s
own tests use a fake scorer instead of this module, so its algorithm is not
affected if this module's model is unavailable.
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache

from fastembed.rerank.cross_encoder import TextCrossEncoder

MODEL_NAME = "Xenova/ms-marco-MiniLM-L-6-v2"


@lru_cache(maxsize=1)
def _model() -> TextCrossEncoder:
    return TextCrossEncoder(model_name=MODEL_NAME)


def score_pairs(query: str, documents: Sequence[str]) -> list[float]:
    """Return one cross-encoder relevance score per document, in order.

    Scores are raw model logits (unbounded, can be negative); higher means
    more relevant to `query`. Not a probability or a similarity in
    `[0, 1]`/`[-1, 1]` like dense_retrieve's cosine score.
    """
    if not documents:
        return []
    return list(_model().rerank(query, list(documents)))
