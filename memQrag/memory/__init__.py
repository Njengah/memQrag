"""Memory module boundary.

Planned responsibility, per docs/ARCHITECTURE.md: SQLite-backed session
memory, long-term memory, memory-informed retrieval boosts, memory decay,
and staleness review signals.

Implemented so far (Phase 4 of docs/PRODUCT_TIMELINE.md):
- session memory schema and read/write in `memQrag.memory.session`
  (`connect`, `record_session_query`, `set_usefulness`,
  `get_session_memory`, `SessionMemoryRecord`), storing which chunks were
  retrieved for a query and whether that retrieval turned out useful.

Long-term memory, memory-informed boosts, memory decay, and staleness
review do not exist yet.
"""
