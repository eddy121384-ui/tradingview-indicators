from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DECISIONS = HERE / "decisions"

EVIDENCE = DECISIONS / "issue-109-phase-a0-evidence-map.md"
PROTOCOL = DECISIONS / "issue-109-phase-a0-preregistered-protocol.md"
SOURCE = DECISIONS / "issue-109-phase-a0-source-contract.json"


def test_issue109_prereg_files_exist():
    assert EVIDENCE.exists()
    assert PROTOCOL.exists()
    assert SOURCE.exists()


def test_issue109_source_contract_is_preoutcome_and_fail_closed():
    m = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert m["created_before_issue109_payoff_results"] is True
    assert m["exact_v66_signal"]["transition_sha256"] == "80446bbcb91be8b18eb0b95e62466edf892e4c04087696a04532f0fe214698af"
    assert m["existing_modern_outcomes"]["csv_sha256"] == "3a7f590c146f9eda5920b6968fe86c9c3cc1887db35597f2d639a1c76b6e5a57"
    assert m["primary_horizon_common_trading_rows"] == 63
    assert m["diagnostic_horizons_common_trading_rows"] == [21, 126]
    assert m["a1_authorized"] is False
    assert m["a2_trajectory_authorized"] is False
    assert m["new_modern_outcomes"]["current_status"] == "PENDING_SNAPSHOT_DO_NOT_RUN_A1"
    assert "blocked" in m["exact_v66_signal"]["trajectory_gate"]


def test_issue109_pairwise_assets_are_frozen():
    m = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert m["pairwise_legs"] == {
        "equity_vs_duration": "SPY - TLT",
        "duration_vs_cash": "TLT - SHV",
        "gold_vs_cash": "GLD - SHV",
        "commodities_vs_cash": "GSG - SHV",
    }
    assert m["new_modern_outcomes"]["asset_roles_frozen_before_issue109_results"]["SHV"].startswith("0-1Y Treasury")
    assert "S&P GSCI" in m["new_modern_outcomes"]["asset_roles_frozen_before_issue109_results"]["GSG"]


def test_issue109_protocol_freezes_primary_questions():
    s = PROTOCOL.read_text(encoding="utf-8")
    assert "3M = 63 common trading rows" in s
    assert "1M = 21 common trading rows" in s
    assert "6M = 126 common trading rows" in s
    assert "fast_slope_X = (X_t - X_t-20) / 20" in s
    assert "mid_slope_X  = (X_t - X_t-63) / 63" in s
    assert "acceleration_X = fast_slope_X - mid_slope_X" in s
    assert "at least **84 complete monthly training rows**" in s
    assert "No interactions." in s
    assert "No FCPI input." in s


def test_issue109_keeps_inflation_threshold_diagnostic_only():
    m = json.loads(SOURCE.read_text(encoding="utf-8"))
    inf = m["absolute_inflation_diagnostic"]
    assert inf["diagnostic_threshold_percent"] == 4.0
    assert "not a production threshold" in inf["threshold_role"]
    s = PROTOCOL.read_text(encoding="utf-8")
    assert "No 3%, 5%, percentile, or optimized alternative threshold" in s


def test_issue109_no_production_authorization():
    s = PROTOCOL.read_text(encoding="utf-8").lower()
    assert "no v6.7 action layer pine is authorized by a0" in s
    assert "no portfolio optimizer" in s
    assert "retune v6.6" in s
