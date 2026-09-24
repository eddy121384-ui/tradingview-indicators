from __future__ import annotations

import json
from pathlib import Path

from issue_109_a2s_current_feed_screen import screen_verdict

HERE = Path(__file__).resolve().parent
FINDING = HERE / "decisions" / "issue-109-a2s-finding.json"
PREREG = HERE / "decisions" / "issue-109-a2s-current-feed-trajectory-preregistered.md"


def test_a2s_finding_is_bound_to_hash_frozen_r4_source():
    finding = json.loads(FINDING.read_text(encoding="utf-8"))
    exact = finding["exact_a2"]
    assert exact["current_feed_r4_sha256"] == "6ceb8cf7ba0e9c17949a4d8892b91f9a8c3a94ea1f7462a5b0a4ce114cf5e1bc"
    assert exact["exact_payoff_was_run"] is False
    assert exact["checkpoint_regime_matches"] == 41
    assert exact["checkpoint_regime_total"] == 51
    assert exact["checkpoint_ipi_max_abs_discrepancy"] > 20.0


def test_a2s_all_pairwise_legs_are_negative():
    finding = json.loads(FINDING.read_text(encoding="utf-8"))
    assert finding["a2s"]["verdicts"] == {
        "equity_vs_duration": "trajectory_screen_negative",
        "duration_vs_cash": "trajectory_screen_negative",
        "gold_vs_cash": "trajectory_screen_negative",
        "commodities_vs_cash": "trajectory_screen_negative",
    }
    assert finding["research_decision"] == "stop_trajectory_rescue_keep_state_only_action_candidates"
    assert finding["trajectory_role"] == "descriptive_ui_context_only"
    assert finding["production_authorized"] is False


def test_a2s_full_sample_trajectory_does_not_improve_all_major_metrics():
    finding = json.loads(FINDING.read_text(encoding="utf-8"))
    for leg, item in finding["a2s"]["full_oos"].items():
        m0 = item["m0"]
        m1 = item["m1"]
        # Every leg has worse full-sample RMSE and MAE.
        assert m1["rmse"] > m0["rmse"], leg
        assert m1["mae"] > m0["mae"], leg


def test_screen_rule_rejects_full_sample_error_degradation():
    m0 = {"n": 100, "rmse": 0.10, "mae": 0.08, "corr": 0.10, "sign_agreement": 0.52}
    m1 = {"n": 100, "rmse": 0.11, "mae": 0.09, "corr": 0.20, "sign_agreement": 0.53}
    segments = [
        {"m0": m0, "m1": m1},
        {"m0": m0, "m1": m1},
        {"m0": m0, "m1": m1},
    ]
    assert screen_verdict(m0, m1, segments) == "trajectory_screen_negative"


def test_a2s_prereg_forbids_posthoc_rescue():
    s = PREREG.read_text(encoding="utf-8")
    assert "current TradingView-feed" in s
    assert "screening study only" in s
    assert "negative A2S result is sufficient to stop further trajectory rescue work" in s.lower()
    assert "Do not:" in s
    assert "change 20/63" in s
    assert "claim the current-feed r4 history is exact frozen V6.6" in s
