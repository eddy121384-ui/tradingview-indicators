#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
FINDING = HERE / "decisions" / "issue-123-reflation-policy-finding.json"


def close(a: float, b: float, tol: float = 1e-12) -> bool:
    return bool(np.isclose(float(a), float(b), rtol=0.0, atol=tol))


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--result",type=Path,required=True)
    args=ap.parse_args()

    expected=json.loads(FINDING.read_text(encoding="utf-8"))
    actual=json.loads(args.result.read_text(encoding="utf-8"))

    assert actual["issue"] == 123
    assert actual["verdict"] == expected["verdict"]
    assert actual["production_authorized"] is expected["production_authorized"]
    assert actual["gate_pass_count"] == expected["gate_pass_count"]
    assert actual["gate"] == expected["gate"]

    assert actual["sample"] == expected["sample"]

    for asset in ("equity","treasury"):
        assert close(actual["c1_average_weights"][asset], expected["c1_average_weights"][asset])

    for scope in ("action","c0","c1"):
        act=actual["full"][scope]
        exp=expected["full"][scope]
        assert close(act["cagr"],exp["cagr"])
        assert close(act["sharpe_excess_cash"],exp["sharpe"])
        assert close(act["max_drawdown"],exp["max_drawdown"])
        assert close(act["terminal_wealth"],exp["terminal_wealth"])
        if scope=="action":
            assert close(act["annualized_tactical_turnover"],exp["annualized_tactical_turnover"])
            assert close(act["cumulative_tactical_cost"],exp["cumulative_tactical_cost"])

    for scope in ("action_minus_c0","action_minus_c1"):
        act=actual["full"][scope]
        exp=expected["full"][scope]
        assert close(act["cagr"],exp["cagr"])
        assert close(act["sharpe"],exp["sharpe"])
        if "max_drawdown" in exp:
            assert close(act["max_drawdown"],exp["max_drawdown"])

    for era_name, exp in expected["broad_era_cagr_advantage"].items():
        assert close(actual["broad_eras"][era_name]["action_minus_c0"]["cagr"],exp)

    strongest=actual["episode_robustness"]["strongest_positive_episode"]
    exp_ep=expected["episode"]
    assert strongest["start_return_year"] == exp_ep["start_return_year"]
    assert strongest["end_return_year"] == exp_ep["end_return_year"]
    assert strongest["active_years"] == exp_ep["active_years"]
    assert close(strongest["gross_contribution"],exp_ep["gross_contribution"])
    assert close(
        actual["episode_robustness"]["strongest_positive_episode_share"],
        exp_ep["positive_share"],
    )
    assert close(
        actual["episode_robustness"]["leaveout"]["action_minus_c0"]["cagr"],
        exp_ep["leaveout_cagr_advantage"],
    )
    assert close(
        actual["episode_robustness"]["leaveout"]["action_minus_c0"]["sharpe"],
        exp_ep["leaveout_sharpe_advantage"],
    )

    assert set(actual["fine_era_leaveouts"]) == set(expected["fine_leaveout_cagr_advantage"])
    for era_name, exp in expected["fine_leaveout_cagr_advantage"].items():
        assert close(actual["fine_era_leaveouts"][era_name]["cagr_advantage_vs_c0"],exp)

    assert actual["source_backbone"]["damodaran_raw_sha256"] == expected["source_backbone"]["damodaran_raw_sha256"]
    assert actual["source_backbone"]["jst_raw_sha256"] == expected["source_backbone"]["jst_raw_sha256"]
    assert actual["output_hashes"] == expected["output_hashes"]

    print({
        "finding_bound":True,
        "verdict":actual["verdict"],
        "gate_pass_count":actual["gate_pass_count"],
        "full_cagr_adv":actual["full"]["action_minus_c0"]["cagr"],
    })


if __name__=="__main__":
    main()
