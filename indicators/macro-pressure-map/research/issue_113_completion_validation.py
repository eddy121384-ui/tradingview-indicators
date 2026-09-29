#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
FINDING = HERE / "decisions" / "issue-113-action-layer-sizing-finding.json"


def close(a: float, b: float, tol: float = 1e-12) -> bool:
    return bool(np.isclose(float(a), float(b), rtol=0.0, atol=tol))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", type=Path, required=True)
    args = ap.parse_args()

    expected = json.loads(FINDING.read_text(encoding="utf-8"))
    actual = json.loads(args.result.read_text(encoding="utf-8"))

    assert actual["verdict"] == expected["verdict"]
    assert actual["production_authorized"] is expected["production_authorized"]
    assert actual["production_gate_pass_count"] == expected["gate_pass_count"]
    assert actual["production_gate"] == expected["production_gate"]

    assert actual["rows"]["monthly_completed"] == expected["sample"]["monthly_completed"]
    assert actual["rows"]["first_origin"] == expected["sample"]["first_origin"]
    assert actual["rows"]["last_origin"] == expected["sample"]["last_origin"]
    assert actual["rows"]["active_months"] == expected["sample"]["active_months"]
    assert actual["rows"]["episode_count"] == expected["sample"]["episode_count"]

    assert close(actual["full"]["action"]["cagr"], expected["full"]["action"]["cagr"])
    assert close(actual["full"]["action"]["sharpe_excess_shv"], expected["full"]["action"]["sharpe"])
    assert close(actual["full"]["action"]["max_drawdown"], expected["full"]["action"]["max_drawdown"])
    assert close(actual["full"]["c0"]["cagr"], expected["full"]["c0"]["cagr"])
    assert close(actual["full"]["c0"]["sharpe_excess_shv"], expected["full"]["c0"]["sharpe"])
    assert close(actual["full"]["c1"]["cagr"], expected["full"]["c1"]["cagr"])
    assert close(actual["full"]["c1"]["sharpe_excess_shv"], expected["full"]["c1"]["sharpe"])
    assert close(actual["full"]["cagr_advantage"], expected["full"]["cagr_advantage"])
    assert close(actual["full"]["sharpe_advantage"], expected["full"]["sharpe_advantage"])
    assert close(actual["full"]["maxdd_difference"], expected["full"]["maxdd_difference"])

    for seg, item in expected["segments"].items():
        assert close(actual["segment_cagr_advantage"][seg], item["cagr_advantage"])
        observed_sharpe_adv = (
            actual["segments"][seg]["action"]["sharpe_excess_shv"]
            - actual["segments"][seg]["c0"]["sharpe_excess_shv"]
        )
        assert close(observed_sharpe_adv, item["sharpe_advantage"])

    strongest = actual["episode_robustness"]["strongest_positive_episode"]
    exp_ep = expected["episode_robustness"]
    assert strongest["start_origin"] == exp_ep["strongest_start"]
    assert strongest["end_origin"] == exp_ep["strongest_end"]
    assert strongest["months"] == exp_ep["strongest_months"]
    assert close(strongest["top_positive_share"], exp_ep["top_positive_share"])
    assert close(actual["episode_robustness"]["leaveout_cagr_advantage"], exp_ep["leaveout_cagr_advantage"])

    for asset, weight in expected["c1_average_weights"].items():
        assert close(actual["c1_average_weights"][asset], weight)

    assert close(
        actual["sleeve_attribution"]["equity_duration_sum"],
        expected["sleeve_attribution"]["equity_duration_sum"],
    )
    assert close(
        actual["sleeve_attribution"]["gold_cash_sum"],
        expected["sleeve_attribution"]["gold_cash_sum"],
    )

    assert actual["source_provenance"]["old_prices"]["snapshot_csv_sha256"] == expected["source_hashes"]["issue64_spy_tlt_gld"]
    assert actual["source_provenance"]["shv_gsg_sha256"] == expected["source_hashes"]["issue109_shv_gsg"]
    assert actual["source_provenance"]["transition_sha256"] == expected["source_hashes"]["issue64_transitions"]
    assert actual["output_hashes"]["monthly_portfolio_csv_sha256"] == expected["output_hashes"]["monthly_portfolio"]
    assert actual["output_hashes"]["active_episodes_csv_sha256"] == expected["output_hashes"]["active_episodes"]

    print({
        "verdict": actual["verdict"],
        "gate_pass_count": actual["production_gate_pass_count"],
        "finding_bound": True,
    })


if __name__ == "__main__":
    main()
