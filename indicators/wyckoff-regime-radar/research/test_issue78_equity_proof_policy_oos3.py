from __future__ import annotations

import analyze_issue78_equity_proof_policy_oos3 as m


def test_proof1_crossing_applies_next_move():
    steps = [0.4, 0.4, 0.3, 0.2]
    assert m.proof_earned_exposures(steps, "proof1") == [
        0.25,
        0.25,
        0.25,
        1.0,
    ]


def test_progressive_crossings_apply_next_move():
    steps = [0.3, 0.3, 0.5, 1.0, -0.2]
    assert m.proof_earned_exposures(steps, "progressive") == [
        0.25,
        0.25,
        0.50,
        0.75,
        1.0,
    ]


def test_progressive_earned_levels_do_not_revoke():
    steps = [0.6, -0.5, 0.2, 1.0]
    assert m.proof_earned_exposures(steps, "progressive") == [
        0.25,
        0.50,
        0.50,
        0.50,
    ]


def test_policy_contract_is_frozen():
    assert m.POLICIES == (
        "R0_NoDerisk",
        "R0_WarningFirst",
        "Proof1_NoDerisk",
        "Proof1_WarningFirst",
        "ProgressiveProof_NoDerisk",
        "ProgressiveProof_WarningFirst",
    )
    assert m.EXPECTED_UNIVERSE_SHA == (
        "9d4a14d163ed308238737647b94e722c62fd023b641e1015e6d97679f9ba3b44"
    )
