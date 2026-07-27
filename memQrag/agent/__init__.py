"""Agent module boundary.

Planned responsibility, per docs/ARCHITECTURE.md and Phase 6 of
docs/PRODUCT_TIMELINE.md: query analysis, multi-hop decomposition,
comparative retrieval orchestration, response synthesis, source citation
assembly, and low-confidence handling.

Implemented so far (Phase 6 of docs/PRODUCT_TIMELINE.md):
- query classification in `memQrag.agent.classify` (`classify_query`,
  `QueryType`, `QueryClassification`), which deterministically labels a
  query as FACTUAL / COMPARATIVE / MULTI-HOP / UNKNOWN without an LLM so
  later orchestration steps can route retrieval and synthesis.
"""
