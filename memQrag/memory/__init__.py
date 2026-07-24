"""Memory module boundary.

Planned responsibility, per docs/ARCHITECTURE.md: SQLite-backed session
memory, long-term memory, memory-informed retrieval boosts, memory decay,
and staleness review signals.

Implemented so far (Phase 4 of docs/PRODUCT_TIMELINE.md):
- session memory schema and read/write in `memQrag.memory.session`
  (`connect`, `record_session_query`, `set_usefulness`,
  `get_session_memory`, `SessionMemoryRecord`), storing which chunks were
  retrieved for a query and whether that retrieval turned out useful;
- long-term memory schema and read/write in `memQrag.memory.long_term`
  (`connect`, `record_long_term_memory`, `update_long_term_memory`,
  `get_long_term_memory_by_id`, `get_all_long_term_memory`,
  `LongTermMemoryRecord`), storing a query's embedding, which documents
  were its best matches, and counters (success count, match count, hit
  rate, decay weight, last used);
- memory-informed retrieval boosts in `memQrag.memory.boost`
  (`promote_session_memory_to_long_term`, `remember_query_outcome`,
  `find_similar_successful_memory`, `apply_memory_boost`,
  `BoostedRetrievalResult`), which promotes useful session queries into
  long-term memory, finds a similar-enough previously-successful query for
  an incoming one, and boosts that query's best documents within a fused
  retrieval ranking.

Memory decay and staleness review do not exist yet.
"""
