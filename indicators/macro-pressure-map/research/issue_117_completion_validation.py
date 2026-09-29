#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
FINDING = HERE / "decisions" / "issue-117-long-history-gold-cash-finding.json"


def close(a: float, b: float, tol: float = 1e-12) -> bool:
    return bool(np.isclose(float(a), float(b), rtol=0.0, atol=tol))


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--result",type=Path,required=True)
    args=ap.parse_args()

    expected=json.loads(FINDING.read_text(encoding="utf-8"))
    actual=json.loads(args.result.read_text(encoding="utf-8"))
    r=actual["result"]

    assert actual["issue"] == 117
    assert r["verdict"] == expected["formal_verdict"]
    assert r["gates"] == expected["gates"]

    p=r["primary_full"]
    ep=expected["primary"]
    assert p["n"] == ep["n"]
    for key in ("mean","median","std","positive_fraction","ci_low","ci_high"):
        assert close(p[key],ep[key])
    assert close(r["sample_span_years"],expected["primary"]["opportunity_span_years"])

    for era_name, exp in expected["eras"].items():
        act=r["eras"][era_name]
        assert act["n"] == exp["n"]
        assert close(act["mean"],exp["mean"])
        assert close(act["ci_low"],exp["ci_low"])
        assert close(act["ci_high"],exp["ci_high"])

    strong=r["strongest_positive_episode"]
    exp_strong=expected["strongest_episode"]
    assert strong["start"] == exp_strong["start"]
    assert strong["end"] == exp_strong["end"]
    assert strong["months"] == exp_strong["months"]
    assert close(strong["top_positive_share"],exp_strong["top_positive_share"])

    leave=r["episode_leaveout"]
    exp_leave=expected["episode_leaveout"]
    assert leave["n"] == exp_leave["n"]
    assert close(leave["mean"],exp_leave["mean"])
    assert close(leave["ci_low"],exp_leave["ci_low"])
    assert close(leave["ci_high"],exp_leave["ci_high"])

    for state,exp in expected["leave_one_substate_out"].items():
        act=r["leave_one_substate_out"][state]
        assert act["n"] == exp["n"]
        assert close(act["mean"],exp["mean"])

    assert actual["source_coverage"]["first"] == expected["source_freeze"]["common_first"]
    assert actual["source_coverage"]["last"] == expected["source_freeze"]["common_last"]
    assert actual["source_coverage"]["months"] == expected["source_freeze"]["common_months"]
    assert close(actual["source_coverage"]["span_years"],expected["source_freeze"]["common_span_years"])

    print({
        "verdict":r["verdict"],
        "primary_n":p["n"],
        "primary_mean":p["mean"],
        "finding_bound":True,
    })


if __name__=="__main__":
    main()
