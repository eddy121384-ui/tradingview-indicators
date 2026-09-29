#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
FINDING = HERE / "decisions" / "issue-115-gold-defensive-sleeve-finding.json"


def close(a: float, b: float, tol: float = 1e-12) -> bool:
    return bool(np.isclose(float(a), float(b), rtol=0.0, atol=tol))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", type=Path, required=True)
    args = ap.parse_args()

    expected = json.loads(FINDING.read_text(encoding="utf-8"))
    actual = json.loads(args.result.read_text(encoding="utf-8"))

    assert actual["issue"] == 115
    assert actual["posthoc_selected"] is True
    assert actual["verdict"] == expected["verdict"]
    assert actual["production_authorized"] is expected["production_authorized"]
    assert actual["production_gate_pass_count"] == expected["gate_pass_count"]
    assert actual["production_gate"] == expected["production_gate"]

    assert actual["rows"]["monthly_completed"] == expected["sample"]["monthly_completed"]
    assert actual["rows"]["first_origin"] == expected["sample"]["first_origin"]
    assert actual["rows"]["last_origin"] == expected["sample"]["last_origin"]
    assert actual["rows"]["active_months"] == expected["sample"]["active_months"]
    assert actual["rows"]["episode_count"] == expected["sample"]["episode_count"]

    for scope in ("gold_only", "c0", "c1", "c2_issue113"):
        exp = expected["full"][scope]
        act = actual["full"][scope]
        assert close(act["cagr"], exp["cagr"])
        assert close(act["sharpe_excess_shv"], exp["sharpe"])
        assert close(act["max_drawdown"], exp["max_drawdown"])
        assert close(act["terminal_wealth"], exp["terminal_wealth"])
        if "annualized_tactical_turnover" in exp:
            assert close(act["annualized_tactical_turnover"], exp["annualized_tactical_turnover"])

    assert close(
        actual["full"]["cagr_advantage_vs_c0"],
        expected["full"]["cagr_advantage_vs_c0"],
    )
    assert close(
        actual["full"]["sharpe_advantage_vs_c0"],
        expected["full"]["sharpe_advantage_vs_c0"],
    )
    assert close(
        actual["full"]["maxdd_difference_vs_c0"],
        expected["full"]["maxdd_difference_vs_c0"],
    )
    assert close(
        actual["full"]["gold_minus_c2"]["cagr"],
        expected["full"]["gold_minus_c2_cagr"],
    )
    assert close(
        actual["full"]["gold_minus_c2"]["sharpe_excess_shv"],
        expected["full"]["gold_minus_c2_sharpe"],
    )

    for seg, exp in expected["segments"].items():
        assert close(actual["segment_cagr_advantage_vs_c0"][seg], exp["cagr_advantage"])
        observed_sharpe_adv = (
            actual["segments"][seg]["gold_only"]["sharpe_excess_shv"]
            - actual["segments"][seg]["c0"]["sharpe_excess_shv"]
        )
        assert close(observed_sharpe_adv, exp["sharpe_advantage"])

    strongest = actual["episode_robustness"]["strongest_positive_episode"]
    ep = expected["episode_robustness"]
    assert strongest["start_origin"] == ep["strongest_start"]
    assert strongest["end_origin"] == ep["strongest_end"]
    assert strongest["months"] == ep["strongest_months"]
    assert close(strongest["top_positive_share"], ep["top_positive_share"])
    assert close(
        actual["episode_robustness"]["leaveout_cagr_advantage_vs_c0"],
        ep["leaveout_cagr_advantage"],
    )

    for key, exp in expected["leave_one_state_out"].items():
        act = actual["leave_one_state_out"][key]
        assert close(act["cagr_advantage_vs_c0"], exp["cagr_advantage"])
        assert close(act["sharpe_advantage_vs_c0"], exp["sharpe_advantage"])

    for rid, exp in expected["state_contribution"].items():
        act = actual["state_contribution"][rid]
        assert act["active_months"] == exp["active_months"]
        assert close(act["gross_contribution_sum"], exp["gross_contribution_sum"])
        assert close(
            act["annualized_mean_over_full_sample"],
            exp["annualized_mean_over_full_sample"],
        )

    for asset, weight in expected["c1_average_weights"].items():
        assert close(actual["c1_average_weights"][asset], weight)

    assert (
        actual["output_hashes"]["monthly_portfolio_csv_sha256"]
        == expected["output_hashes"]["monthly_portfolio"]
    )
    assert (
        actual["output_hashes"]["active_episodes_csv_sha256"]
        == expected["output_hashes"]["active_episodes"]
    )

    print({
        "verdict": actual["verdict"],
        "gate_pass_count": actual["production_gate_pass_count"],
        "finding_bound": True,
    })


if __name__ == "__main__":
    main()
