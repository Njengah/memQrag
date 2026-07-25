"""memQrag backend package.

This is a placeholder scaffold for the memQrag production RAG system. The
submodule boundaries mirror the planned runtime shape documented in
docs/ARCHITECTURE.md:

- memQrag.ingestion: document intake, extraction, chunking, persistence.
- memQrag.retrieval: dense/sparse retrieval, fusion, reranking, confidence.
- memQrag.memory: session and long-term memory, decay, staleness signals.
- memQrag.conflicts: contradiction records, claim comparison, review state.
- memQrag.agent: query analysis, orchestration, synthesis, citations.
- memQrag.api: FastAPI app, schemas, endpoint handlers, dependency wiring.

No runtime behavior has been implemented yet. See docs/PRODUCT_TIMELINE.md
for the implementation order that fills these modules in.
"""

__version__ = "0.1.0"
