#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
FINDING = HERE / "decisions" / "issue-125-reflation-bridge-finding.json"

def close(a: float, b: float, tol: float = 1e-12) -> bool:
    return bool(np.isclose(float(a), float(b), rtol=0.0, atol=tol))

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--result",type=Path,required=True)
    args=ap.parse_args()

    expected=json.loads(FINDING.read_text(encoding="utf-8"))
    actual=json.loads(args.result.read_text(encoding="utf-8"))

    assert actual["issue"] == 125
    assert actual["verdict"] == expected["verdict"]
    assert actual["production_authorized"] is False
    assert actual["bridge"]["years"] == expected["years"]
    assert actual["bridge"]["hmra_reflation_years"] == expected["hmra_reflation_years"]
    assert actual["gate"] == expected["gate"]
    assert actual["gate_pass_count"] == expected["gate_pass_count"]
    assert actual["source_hashes"]["exact_v66_transitions_sha256"] == expected["transition_sha256"]

    for key in ("r3","growth_high","inflation_high"):
        act=actual["bridge"]["primary"][key]
        exp=expected["primary"][key]
        for metric in ("reflation_mean","other_mean","mean_lift","ci_low","ci_high"):
            assert close(act[metric],exp[metric])

    spec=actual["bridge"]["regime_specificity"]
    assert spec["r3_is_largest_positive"] is expected["r3_specificity"]["r3_is_largest_positive"]
    assert close(spec["largest_lift"],expected["r3_specificity"]["largest_lift"])

    loo=actual["bridge"]["leave_one_reflation_year_out"]
    assert set(loo)==set(expected["leaveout_lifts"])
    for year,val in expected["leaveout_lifts"].items():
        assert close(loo[year]["r3_mean_lift"],val)

    b=actual["binary_monthly_diagnostic"]
    for key in ("tp","fp","fn","tn"):
        assert b[key] == expected["binary"][key]
    for key in ("accuracy","precision","recall","jaccard"):
        assert close(b[key],expected["binary"][key])

    assert close(actual["timing_diagnostics"]["t_plus_1"]["r3"]["mean_lift"],expected["timing"]["t1_r3_lift"])
    assert close(actual["timing_diagnostics"]["t_plus_2"]["r3"]["mean_lift"],expected["timing"]["t2_r3_lift"])
    assert actual["output_hashes"] == expected["output_hashes"]

    print({
        "finding_bound":True,
        "verdict":actual["verdict"],
        "gate_pass_count":actual["gate_pass_count"],
        "r3_lift":actual["bridge"]["primary"]["r3"]["mean_lift"],
    })

if __name__=="__main__":
    main()
