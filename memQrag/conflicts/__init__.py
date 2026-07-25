"""Conflicts module boundary.

Planned responsibility, per docs/ARCHITECTURE.md and Phase 5 of
docs/PRODUCT_TIMELINE.md: contradiction record persistence, entity/claim
comparison over retrieved chunks, and surfacing conflicting factual claims
for human review (instead of letting the LLM silently choose).

Implemented so far (Phase 5 of docs/PRODUCT_TIMELINE.md):
- contradiction record schema and read/write in `memQrag.conflicts.records`
  (`connect`, `record_conflict`, `set_review_status`, `get_conflict_by_id`,
  `get_all_conflicts`, `ConflictRecord`, `ConflictReviewStatus`), storing
  one conflict's entity, opposing claims, source chunk id lists, detection
  timestamp, and review status.

Entity/claim comparison, response flagging, and the `GET /api/conflicts`
endpoint do not exist yet.
"""
