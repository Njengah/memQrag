"""Memory decay for old, low-value long-term memory (Phase 4 PR 4).

Reduces `decay_weight` for long-term memory records that are both old (no
match in `DECAY_AGE_DAYS`) and low-value (`hit_rate` below
`DECAY_HIT_RATE_THRESHOLD`), so `memQrag.memory.boost.apply_memory_boost()`
(which now scales its boost by `decay_weight`) gives them progressively
less retrieval influence over time, without ever hiding them outright. See
docs/DECISIONS.md ("Memory Decay For Old, Low-Hit-Rate Memories") for the
formula and threshold rationale.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

from memQrag.memory.long_term import (
    LongTermMemoryRecord,
    get_all_long_term_memory,
    update_long_term_memory,
)

DECAY_AGE_DAYS = 30
DECAY_HIT_RATE_THRESHOLD = 0.5
DECAY_FACTOR = 0.5
MIN_DECAY_WEIGHT = 0.1


def is_decay_eligible(
    record: LongTermMemoryRecord,
    now: datetime | None = None,
    age_days: int = DECAY_AGE_DAYS,
    hit_rate_threshold: float = DECAY_HIT_RATE_THRESHOLD,
) -> bool:
    """A record is decay-eligible once it is both old and low-value.

    "Old" means no match in over `age_days` days, measured from
    `last_used` (which `memQrag.memory.boost.remember_query_outcome()`
    refreshes on every match, not `id`/creation order) — a memory that
    keeps getting reused never ages out. "Low-value" means
    `hit_rate < hit_rate_threshold`; a record with no matches yet
    (`match_count == 0`, `hit_rate == 0.0`) counts as low-value too, since
    it has no evidence of being useful.
    """
    now = now or datetime.now(UTC)
    age = now - record.last_used
    return age >= timedelta(days=age_days) and record.hit_rate < hit_rate_threshold


def decay_weight_for(
    record: LongTermMemoryRecord,
    now: datetime | None = None,
    age_days: int = DECAY_AGE_DAYS,
    hit_rate_threshold: float = DECAY_HIT_RATE_THRESHOLD,
    decay_factor: float = DECAY_FACTOR,
    min_decay_weight: float = MIN_DECAY_WEIGHT,
) -> float:
    """Return the decay-adjusted weight for one record, without writing it.

    This recomputes `decay_weight` from scratch as a function of `now` and
    `record.last_used`/`record.hit_rate` — it deliberately ignores
    `record.decay_weight`'s currently stored value — so that:
    - calling `apply_memory_decay()` more than once for the same `now`
      never decays a record twice (idempotent, unlike multiplying the
      stored weight by `decay_factor` on every call would be);
    - a record that ages out, decays, and later gets reused (refreshing
      `last_used`) is no longer eligible and its weight is restored to
      `1.0`, not left stuck at its last decayed value.

    Not eligible -> `1.0` (full strength). Eligible -> `decay_factor`
    raised to the number of whole `age_days`-long periods past the
    eligibility threshold, floored at `min_decay_weight` so a memory's
    influence shrinks toward — but never reaches — zero. A decayed memory
    should read as "deprioritized," not "erased," per AGENTS.md's "do not
    silently suppress" spirit.
    """
    now = now or datetime.now(UTC)
    if not is_decay_eligible(
        record, now=now, age_days=age_days, hit_rate_threshold=hit_rate_threshold
    ):
        return 1.0

    age_past_threshold = (now - record.last_used) - timedelta(days=age_days)
    elapsed_periods = 1 + age_past_threshold // timedelta(days=age_days)
    return max(min_decay_weight, decay_factor**elapsed_periods)


def apply_memory_decay(
    conn: sqlite3.Connection,
    now: datetime | None = None,
) -> list[int]:
    """Recompute and persist `decay_weight` for every long-term memory
    record; return the ids whose stored weight actually changed.

    Not called automatically by anything yet — no scheduler/orchestration
    layer exists (same "call functions directly until a real need arises"
    precedent as ingestion, retrieval, and `memQrag.memory.boost`). A
    future scheduled job or the Phase 7 API layer is the eventual caller.
    """
    now = now or datetime.now(UTC)
    changed_ids = []
    for record in get_all_long_term_memory(conn):
        new_weight = decay_weight_for(record, now=now)
        if new_weight != record.decay_weight:
            update_long_term_memory(conn, record.id, decay_weight=new_weight)
            changed_ids.append(record.id)
    return changed_ids
