"""Small active-prereg tests; never loads a market forward outcome."""
from types import SimpleNamespace

from ptm_addon_policy import (
    ADDON_ALREADY_FULL, ADDON_DE_RISK, ADDON_PROMOTE,
    ADDON_WITHHOLD_CENSORED, PARENT_PATH_P0, ParentPlan,
)
from ptm_c1_prereg import (
    ACTIVE_CHALLENGERS, ALREADY_FULL, BASELINE_DE_RISK,
    PARENT_NOT_ELIGIBLE, PROMOTED, RIGHT_CENSORED, WITHHELD_THROUGH_EXPIRY,
    classify_c1_disposition, preprobe_range_state, synthetic_c1_audit,
)
from ptm_territory import Bar


def _plan(break_at=110):
    return ParentPlan(probe_bar=100, b3_break_bar=break_at, path=PARENT_PATH_P0)


def _observations(first, last):
    return [SimpleNamespace(bar_index=i) for i in range(first, last + 1)]


def _result(status=ADDON_WITHHOLD_CENSORED, delay=None):
    return SimpleNamespace(status=status, extra_delay_bars=delay)


def test_before_eligibility_is_right_censored_not_missed_addon():
    p = _plan(break_at=120)  # eligible=123
    row = classify_c1_disposition(p, _observations(120, 122), _result())
    assert row.status == RIGHT_CENSORED
    assert row.last_observed_bar < row.eligible_bar
    assert row.established_policy_missed_addon is False
    assert row.finite_delay_bars is None


def test_observed_after_eligibility_but_before_full_horizon_is_right_censored():
    row = classify_c1_disposition(_plan(), _observations(113, 160), _result())
    assert row.status == RIGHT_CENSORED
    assert not row.completed_full_policy_horizon
    assert not row.established_policy_missed_addon


def test_missing_interior_decision_bar_blocks_full_horizon_claim():
    obs = _observations(113, 233)
    obs.pop(50)
    row = classify_c1_disposition(_plan(), obs, _result())
    assert row.status == RIGHT_CENSORED
    assert row.last_observed_bar == row.expiry_bar
    assert not row.completed_full_policy_horizon


def test_true_full_expiry_establishes_policy_nonpromotion():
    row = classify_c1_disposition(_plan(), _observations(113, 233), _result())
    assert row.status == WITHHELD_THROUGH_EXPIRY
    assert row.completed_full_policy_horizon
    assert row.established_policy_missed_addon
    assert row.finite_delay_bars is None


def test_promotion_and_derisk_are_separate_from_right_censoring():
    p = _plan()
    promoted = classify_c1_disposition(p, _observations(113, 114),
                                        _result(ADDON_PROMOTE, delay=1))
    derisked = classify_c1_disposition(p, _observations(113, 114),
                                       _result(ADDON_DE_RISK))
    full = classify_c1_disposition(p, _observations(113, 114),
                                   _result(ADDON_ALREADY_FULL))
    assert promoted.status == PROMOTED and promoted.finite_delay_bars == 1
    assert derisked.status == BASELINE_DE_RISK
    assert full.status == ALREADY_FULL
    assert not any(x.established_policy_missed_addon
                   for x in (promoted, derisked, full))


def test_no_parent_entitlement_is_never_a_ptm_cost():
    from ptm_addon_policy import PARENT_PATH_P3
    p = ParentPlan(probe_bar=100, b3_break_bar=110, path=PARENT_PATH_P3)
    row = classify_c1_disposition(p, _observations(113, 233), _result())
    assert row.status == PARENT_NOT_ELIGIBLE
    assert row.expiry_bar is None
    assert not row.established_policy_missed_addon


def _triangle_reference():
    result = []
    for i in range(120):
        phase = i % 40
        close = 100.0 + (phase if phase <= 20 else 40 - phase)
        result.append(Bar(open=close, high=close + 0.25,
                          low=close - 0.25, close=close))
    return result


def test_preprobe_width_detects_nontrivial_wide_and_narrow_geometry():
    rotating = _triangle_reference()
    wide = preprobe_range_state(rotating, 120, 3.0)
    directional = preprobe_range_state(rotating, 120, 0.0)
    narrow = [Bar(open=100.0, high=100.5, low=99.5, close=100.0)] * 120
    low = preprobe_range_state(narrow, 120, 2.0)
    assert wide.regime == "WIDE_ROTATING"
    assert wide.width_atr14 >= 8
    assert directional.regime == "WIDE_UNCONFIRMED_ROTATION"
    assert low.regime == "NARROW"
    assert low.width_atr14 < 4
    assert wide.width_atr14 != low.width_atr14


def test_future_bars_do_not_affect_preprobe_stratification():
    reference = _triangle_reference()
    before = preprobe_range_state(reference, 120, 3.0)
    huge_future = [Bar(open=9999, high=10001, low=9998, close=10000)] * 40
    after = preprobe_range_state(reference + huge_future, 120, 3.0)
    assert before == after


def test_invalid_atr_fails_closed_and_never_divides_by_zero():
    flat = [Bar(open=100, high=100, low=100, close=100)] * 120
    row = preprobe_range_state(flat, 120, 0.0)
    assert row.regime == "UNKNOWN"
    assert row.width_atr14 is None


def test_synthetic_audit_has_one_active_challenger_and_no_future_outcomes():
    audit = synthetic_c1_audit()
    assert ACTIVE_CHALLENGERS == ("C1_PTM_GUARD",)
    assert audit["fixtures"] == 33
    rows = {r["fixture"]: r for r in audit["rows"]}
    for fixture in ("gappy_reference", "one_tick_breakout", "crossed_but_not_closed"):
        row = rows[fixture]["disposition"]
        assert row["status"] == RIGHT_CENSORED, row
        assert not row["established_policy_missed_addon"], row
        assert row["last_observed_bar"] < row["eligible_bar"], row
    counts = audit["disposition_counts"]
    assert sum(counts.values()) == 33
    assert counts[RIGHT_CENSORED] >= 3
    assert all("forward" in w.lower() or "outcome" in w.lower() or
               "administrative" in w.lower() or "C2" in w or "B3" in w or
               "Ex-post" in w
               for w in audit["warnings"])
