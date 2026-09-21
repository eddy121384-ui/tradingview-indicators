from __future__ import annotations

import math

import analyze_issue78_r0_warning_first_composition as m


def test_warning_first_mild_damage_does_not_cut():
    steps = [1.0, -0.5, 0.0]
    earned = [1.0, 1.0, 1.0]
    out = m.apply_management(steps, earned, "warning_first")
    assert out["actual"] == [1.0, 1.0, 1.0]


def test_warning_first_cuts_one_step_at_two_atr_giveback():
    steps = [3.0, -2.5, 0.0]
    earned = [1.0, 1.0, 1.0]
    out = m.apply_management(steps, earned, "warning_first")
    assert out["actual"] == [1.0, 1.0, 0.75]
    assert out["de_risk_count"] == 1


def test_warning_first_cuts_two_steps_at_four_atr_giveback():
    steps = [5.0, -4.5, 0.0]
    earned = [1.0, 1.0, 1.0]
    out = m.apply_management(steps, earned, "warning_first")
    assert out["actual"] == [1.0, 1.0, 0.50]


def test_warning_first_latch_survives_partial_recovery():
    steps = [3.0, -2.5, 1.0, 0.0]
    earned = [1.0, 1.0, 1.0, 1.0]
    out = m.apply_management(steps, earned, "warning_first")
    assert out["actual"][2] == 0.75
    assert out["actual"][3] == 0.75


def test_warning_first_new_extreme_resets_for_following_move_only():
    steps = [3.0, -2.5, 3.0, 0.0]
    earned = [1.0, 1.0, 1.0, 1.0]
    out = m.apply_management(steps, earned, "warning_first")
    assert out["actual"][2] == 0.75
    assert out["actual"][3] == 1.0
    assert out["re_risk_count"] == 1


def test_existing_latch_is_not_cleared_by_r0_promotion():
    steps = [3.0, -2.5, 0.0]
    earned = [0.25, 0.25, 1.0]
    out = m.apply_management(
        steps, earned, "warning_first", promotion_local=2
    )
    assert out["promotion_latched"] == 1
    assert math.isclose(out["promotion_exposure"], 0.75)
    assert math.isclose(out["actual"][2], 0.75)


def test_no_derisk_equals_earned_path():
    steps = [1.0, -3.0, 2.0]
    earned = [0.25, 1.0, 1.0]
    out = m.apply_management(steps, earned, "none")
    assert out["actual"] == earned
