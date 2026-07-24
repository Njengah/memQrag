"""End-to-end retrieval tests using a small fictional fixture corpus (Phase 3 PR 6).

Exercises the whole Phase 3 chain (dense -> sparse -> fusion -> rerank ->
confidence) against one small, fictional, topically varied corpus, using
real embeddings and the real cross-encoder (skips, not fails, if either
model can't be loaded — matching tests/test_retrieval_dense.py and
tests/test_retrieval_rerank.py), and asserts the two Phase 3 exit criteria
from docs/PRODUCT_TIMELINE.md directly:

- Retrieval returns ranked chunks with source references and confidence.
- Tests prove fusion and threshold behavior.

Each module already has its own focused unit tests (test_retrieval_*.py);
this file only proves the modules compose correctly together, so it stays
deliberately small and runs the whole chain once (module-scoped fixture),
reusing that result across all assertions instead of re-embedding per
test. See docs/DECISIONS.md ("End-To-End Retrieval Fixture Tests") for why
the corpus is shaped the way it is.
"""

import uuid
from dataclasses import dataclass

import chromadb
import pytest

from memQrag.ingestion.chunking import Chunk
from memQrag.ingestion.embeddings import embed_sentences
from memQrag.ingestion.vector_store import persist_chunk_vectors
from memQrag.retrieval.confidence import (
    ConfidenceLevel,
    ScoredRetrievalResult,
    assign_confidence,
    confidence_for_dense_score,
)
from memQrag.retrieval.dense import DenseRetrievalResult, dense_retrieve
from memQrag.retrieval.fusion import FusedRetrievalResult, reciprocal_rank_fusion
from memQrag.retrieval.rerank import RERANK_TOP_K, RerankedRetrievalResult, rerank
from memQrag.retrieval.sparse import SparseRetrievalResult, sparse_retrieve

QUERY = "How long are lighthouse logs kept?"

# One direct near-answer (strong on both signals), one same-meaning paraphrase
# with zero lexical overlap (dense-only signal), one same-words decoy about a
# different topic (strong lexical overlap, weak semantic match), and four
# unrelated filler chunks to push the corpus past RERANK_TOP_K.
_CORPUS = [
    (
        "lighthouse-log.pdf",
        "Fictional lighthouse logs are kept for a decade before they get archived.",
    ),
    (
        "beacon-notes.txt",
        "Fictional beacon tower entries stay on file for many years at the harbor.",
    ),
    (
        "paint-inventory.txt",
        "The fictional lighthouse crew kept a logs binder about paint supplies stored nearby.",
    ),
    (
        "market-report.txt",
        "Fictional stock markets fell sharply after a surprising earnings report.",
    ),
    ("bakery-notes.txt", "A fictional bakery introduced a new sourdough recipe this spring."),
    (
        "garden-guide.txt",
        "Fictional gardeners planted tulip bulbs before the first autumn frost.",
    ),
    (
        "sports-recap.txt",
        "The fictional local team won its championship match in overtime.",
    ),
]

_LIGHTHOUSE_CHUNK_ID = 1


@dataclass
class PipelineOutput:
    dense_results: list[DenseRetrievalResult]
    sparse_results: list[SparseRetrievalResult]
    fused_results: list[FusedRetrievalResult]
    reranked_results: list[RerankedRetrievalResult]
    scored_results: list[ScoredRetrievalResult]


@pytest.fixture(scope="module")
def pipeline_output() -> PipelineOutput:
    try:
        embed_sentences(["warm up"])
    except Exception as exc:
        pytest.skip(f"Could not load the sentence embedding model: {exc}")

    # chromadb.EphemeralClient() instances share underlying state within a
    # process, so this uses a uniquely named collection rather than
    # memQrag.ingestion.vector_store.get_collection()'s fixed
    # "memqrag_chunks" name, to stay isolated from other test files'
    # fixtures within the same pytest session; see tests/test_ingestion_vector_store.py
    # for the same pattern. hnsw:space="cosine" matches get_collection()'s
    # real configuration.
    client = chromadb.EphemeralClient()
    collection = client.get_or_create_collection(
        f"test-retrieval-pipeline-{uuid.uuid4().hex}", metadata={"hnsw:space": "cosine"}
    )

    chunks = [
        Chunk(
            text=text,
            token_count=len(text.split()),
            source_document=source_document,
            page_number=None,
            section_heading=None,
        )
        for source_document, text in _CORPUS
    ]
    chunk_ids = list(range(1, len(chunks) + 1))
    persist_chunk_vectors(collection, document_id=1, chunk_ids=chunk_ids, chunks=chunks)

    dense_results = dense_retrieve(collection, QUERY)
    sparse_results = sparse_retrieve(collection, QUERY)
    fused_results = reciprocal_rank_fusion(dense_results, sparse_results)

    try:
        reranked_results = rerank(fused_results, QUERY)
    except Exception as exc:
        pytest.skip(f"Could not load the cross-encoder model: {exc}")

    scored_results = assign_confidence(reranked_results)

    return PipelineOutput(
        dense_results=dense_results,
        sparse_results=sparse_results,
        fused_results=fused_results,
        reranked_results=reranked_results,
        scored_results=scored_results,
    )


def test_dense_and_sparse_both_return_ranked_candidates(pipeline_output: PipelineOutput):
    """Ranking: both retrieval methods return candidates for fusion to combine."""
    assert len(pipeline_output.dense_results) == len(_CORPUS)
    assert len(pipeline_output.sparse_results) >= 1
    assert pipeline_output.dense_results[0].chunk_id == _LIGHTHOUSE_CHUNK_ID


def test_fusion_ranks_the_dual_signal_chunk_first_without_truncating(
    pipeline_output: PipelineOutput,
):
    """Fusion behavior: the chunk strong on both signals outranks single-signal
    chunks, and the fused list keeps every corpus chunk (no truncation)."""
    assert len(pipeline_output.fused_results) == len(_CORPUS)
    assert pipeline_output.fused_results[0].chunk_id == _LIGHTHOUSE_CHUNK_ID
    assert pipeline_output.fused_results[0].fused_rank == 1


def test_reranking_truncates_to_the_final_top_5(pipeline_output: PipelineOutput):
    """Reranking behavior: unlike fusion, this step truncates the candidate list."""
    assert len(pipeline_output.reranked_results) == RERANK_TOP_K
    assert [result.final_rank for result in pipeline_output.reranked_results] == list(
        range(1, RERANK_TOP_K + 1)
    )


def test_final_results_carry_source_references(pipeline_output: PipelineOutput):
    """Exit criterion: retrieval returns ranked chunks with source references."""
    valid_sources = {source_document for source_document, _ in _CORPUS}
    assert len(pipeline_output.scored_results) > 0
    for result in pipeline_output.scored_results:
        assert result.source_document in valid_sources
        assert result.text


def test_final_results_carry_confidence_matching_their_dense_score(
    pipeline_output: PipelineOutput,
):
    """Exit criterion: confidence threshold behavior holds through the real pipeline,
    not just in confidence_for_dense_score's own isolated unit tests."""
    for result in pipeline_output.scored_results:
        assert result.confidence_level == confidence_for_dense_score(result.dense_score)


def test_top_result_is_the_direct_answer_and_not_low_confidence(
    pipeline_output: PipelineOutput,
):
    top_result = pipeline_output.scored_results[0]
    assert top_result.chunk_id == _LIGHTHOUSE_CHUNK_ID
    assert top_result.confidence_level != ConfidenceLevel.LOW
