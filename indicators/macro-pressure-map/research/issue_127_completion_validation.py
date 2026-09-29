#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
FINDING = HERE / "decisions" / "issue-127-exact-reflation-translation-finding.json"

def close(a: float, b: float, tol: float = 1e-12) -> bool:
    return bool(np.isclose(float(a), float(b), rtol=0.0, atol=tol))

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--result",type=Path,required=True)
    args=ap.parse_args()

    expected=json.loads(FINDING.read_text(encoding="utf-8"))
    actual=json.loads(args.result.read_text(encoding="utf-8"))

    assert actual["issue"] == 127
    assert actual["verdict"] == expected["verdict"]
    assert actual["production_authorized"] is False
    assert actual["gate"] == expected["gate"]
    assert actual["gate_pass_count"] == expected["gate_pass_count"]
    assert actual["sample"] == expected["sample"]

    for asset,val in expected["c1_average_weights"].items():
        assert close(actual["c1_average_weights"][asset],val)

    for scope in ("action","c0","c1"):
        act=actual["full"][scope]
        exp=expected["full"][scope]
        assert close(act["cagr"],exp["cagr"])
        assert close(act["sharpe_excess_shv"],exp["sharpe"])
        assert close(act["max_drawdown"],exp["max_drawdown"])
        assert close(act["terminal_wealth"],exp["terminal_wealth"])

    for scope in ("action_minus_c0","action_minus_c1"):
        act=actual["full"][scope]
        exp=expected["full"][scope]
        assert close(act["cagr"],exp["cagr"])
        assert close(act["sharpe"],exp["sharpe"])
        if "max_drawdown" in exp:
            assert close(act["max_drawdown"],exp["max_drawdown"])

    for name,exp in expected["segments"].items():
        act=actual["segments"][name]
        assert act["active_months"] == exp["active_months"]
        assert close(act["action_minus_c0"]["cagr"],exp["cagr_advantage"])
        assert close(act["action_minus_c0"]["sharpe"],exp["sharpe_advantage"])

    ep=actual["episode_robustness"]
    e=expected["episode"]
    assert ep["strongest_positive_episode"]["start_origin"] == e["start_origin"]
    assert ep["strongest_positive_episode"]["end_origin"] == e["end_origin"]
    assert ep["strongest_positive_episode"]["months"] == e["months"]
    assert close(ep["strongest_positive_episode"]["gross_contribution"],e["gross_contribution"])
    assert close(ep["top_positive_episode_share"],e["top_positive_share"])
    assert close(ep["leaveout_cagr_advantage_vs_c0"],e["leaveout_cagr_advantage"])

    assert actual["source_provenance"]["old_prices"]["snapshot_csv_sha256"] == expected["source_hashes"]["prices"]
    assert actual["source_provenance"]["shv_gsg_sha256"] == expected["source_hashes"]["shv"]
    assert actual["source_provenance"]["transition_sha256"] == expected["source_hashes"]["transitions"]
    assert actual["output_hashes"] == expected["output_hashes"]

    print({
        "finding_bound":True,
        "verdict":actual["verdict"],
        "gate_pass_count":actual["gate_pass_count"],
        "cagr_advantage":actual["full"]["action_minus_c0"]["cagr"],
    })

if __name__=="__main__":
    main()
