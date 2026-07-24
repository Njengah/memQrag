"""Tests for memQrag.memory.decay (memory decay, Phase 4 PR 4).

Uses hand-picked `last_used`/`hit_rate` values (via `update_long_term_memory`)
rather than waiting on real time, so these tests are deterministic and
never touch the real clock except through an explicit `now=` argument.
"""

from datetime import UTC, datetime, timedelta

import pytest

from memQrag.memory.decay import (
    DECAY_FACTOR,
    MIN_DECAY_WEIGHT,
    apply_memory_decay,
    decay_weight_for,
    is_decay_eligible,
)
from memQrag.memory.long_term import (
    connect,
    get_long_term_memory_by_id,
    record_long_term_memory,
    update_long_term_memory,
)

_EMBEDDING = [0.1, 0.2, 0.3]
_NOW = datetime(2026, 7, 24, tzinfo=UTC)


@pytest.fixture
def conn():
    connection = connect(":memory:")
    yield connection
    connection.close()


def _record(conn, *, last_used: datetime, hit_rate: float, decay_weight: float = 1.0):
    long_term_memory_id = record_long_term_memory(conn, "query", _EMBEDDING, [1])
    update_long_term_memory(
        conn,
        long_term_memory_id,
        match_count=1,
        hit_rate=hit_rate,
        decay_weight=decay_weight,
        last_used=last_used,
    )
    return get_long_term_memory_by_id(conn, long_term_memory_id)


# -- is_decay_eligible ---------------------------------------------------


def test_is_decay_eligible_false_for_recent_low_hit_rate_memory(conn):
    record = _record(conn, last_used=_NOW - timedelta(days=1), hit_rate=0.2)

    assert is_decay_eligible(record, now=_NOW) is False


def test_is_decay_eligible_false_for_old_high_hit_rate_memory(conn):
    record = _record(conn, last_used=_NOW - timedelta(days=60), hit_rate=0.9)

    assert is_decay_eligible(record, now=_NOW) is False


def test_is_decay_eligible_true_for_old_low_hit_rate_memory(conn):
    record = _record(conn, last_used=_NOW - timedelta(days=60), hit_rate=0.2)

    assert is_decay_eligible(record, now=_NOW) is True


def test_is_decay_eligible_true_exactly_at_the_age_threshold(conn):
    record = _record(conn, last_used=_NOW - timedelta(days=30), hit_rate=0.2)

    assert is_decay_eligible(record, now=_NOW) is True


def test_is_decay_eligible_true_for_never_matched_memory_past_the_age_threshold(conn):
    # match_count == 0 / hit_rate == 0.0 (the default) is "low-value" too.
    long_term_memory_id = record_long_term_memory(conn, "query", _EMBEDDING, [1])
    update_long_term_memory(conn, long_term_memory_id, last_used=_NOW - timedelta(days=31))

    record = get_long_term_memory_by_id(conn, long_term_memory_id)
    assert is_decay_eligible(record, now=_NOW) is True


# -- decay_weight_for ------------------------------------------------------


def test_decay_weight_for_not_eligible_returns_full_strength(conn):
    record = _record(conn, last_used=_NOW - timedelta(days=1), hit_rate=0.9)

    assert decay_weight_for(record, now=_NOW) == pytest.approx(1.0)


def test_decay_weight_for_just_past_threshold_applies_one_decay_factor(conn):
    record = _record(conn, last_used=_NOW - timedelta(days=30), hit_rate=0.2)

    assert decay_weight_for(record, now=_NOW) == pytest.approx(DECAY_FACTOR)


def test_decay_weight_for_two_periods_past_threshold_applies_factor_squared(conn):
    record = _record(conn, last_used=_NOW - timedelta(days=60), hit_rate=0.2)

    assert decay_weight_for(record, now=_NOW) == pytest.approx(DECAY_FACTOR**2)


def test_decay_weight_for_floors_at_min_decay_weight(conn):
    record = _record(conn, last_used=_NOW - timedelta(days=365), hit_rate=0.0)

    assert decay_weight_for(record, now=_NOW) == pytest.approx(MIN_DECAY_WEIGHT)


def test_decay_weight_for_ignores_the_currently_stored_decay_weight(conn):
    # Recomputed from (age, hit_rate) every time, not multiplied onto the
    # stored value -- this is what makes apply_memory_decay() idempotent.
    record = _record(conn, last_used=_NOW - timedelta(days=30), hit_rate=0.2, decay_weight=0.01)

    assert decay_weight_for(record, now=_NOW) == pytest.approx(DECAY_FACTOR)


# -- apply_memory_decay ----------------------------------------------------


def test_apply_memory_decay_updates_eligible_records(conn):
    record = _record(conn, last_used=_NOW - timedelta(days=60), hit_rate=0.2)

    changed_ids = apply_memory_decay(conn, now=_NOW)

    assert changed_ids == [record.id]
    updated = get_long_term_memory_by_id(conn, record.id)
    assert updated.decay_weight == pytest.approx(DECAY_FACTOR**2)


def test_apply_memory_decay_leaves_ineligible_records_unchanged(conn):
    record = _record(conn, last_used=_NOW - timedelta(days=1), hit_rate=0.9)

    changed_ids = apply_memory_decay(conn, now=_NOW)

    assert changed_ids == []
    updated = get_long_term_memory_by_id(conn, record.id)
    assert updated.decay_weight == pytest.approx(1.0)


def test_apply_memory_decay_is_idempotent_for_the_same_now(conn):
    _record(conn, last_used=_NOW - timedelta(days=60), hit_rate=0.2)

    apply_memory_decay(conn, now=_NOW)
    second_run_changed_ids = apply_memory_decay(conn, now=_NOW)

    assert second_run_changed_ids == []


def test_apply_memory_decay_restores_full_strength_after_a_memory_is_reused(conn):
    record = _record(conn, last_used=_NOW - timedelta(days=60), hit_rate=0.2, decay_weight=0.25)

    # Reuse refreshes last_used and hit_rate, as remember_query_outcome() would.
    update_long_term_memory(conn, record.id, last_used=_NOW, hit_rate=0.9)

    changed_ids = apply_memory_decay(conn, now=_NOW)

    assert changed_ids == [record.id]
    updated = get_long_term_memory_by_id(conn, record.id)
    assert updated.decay_weight == pytest.approx(1.0)
