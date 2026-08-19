"""memQrag: RAG with persistent retrieval memory.

Implemented: ingestion, hybrid retrieval, memory, conflicts, query
classification, and a small FastAPI surface (`/health`, `GET /api/conflicts`).
Ingest/query HTTP endpoints and the chat UI are not wired yet.
See docs/PRODUCT_TIMELINE.md.
"""

__version__ = "0.1.0"
