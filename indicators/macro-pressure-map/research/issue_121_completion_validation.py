#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
FINDING = HERE / "decisions" / "issue-121-phase1-long-history-rematch-finding.json"


def close(a: float, b: float, tol: float = 1e-12) -> bool:
    return bool(np.isclose(float(a), float(b), rtol=0.0, atol=tol))


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--result",type=Path,required=True)
    args=ap.parse_args()

    expected=json.loads(FINDING.read_text(encoding="utf-8"))
    actual=json.loads(args.result.read_text(encoding="utf-8"))

    assert actual["issue"] == 121
    assert actual["phase"] == "phase1-ultra-long-history-rematch"
    assert actual["production_authorized"] is False
    assert actual["commodity_status"] == "source_gate_pending_no_payoff"

    src=actual["source_backbone"]
    exp_src=expected["source_backbone"]
    assert src["issue_91_hmra_freeze_validated"] is True
    assert src["damodaran_raw_sha256"] == exp_src["damodaran_raw_sha256"]
    assert src["jst_raw_sha256"] == exp_src["jst_raw_sha256"]
    assert src["structural_rows"] == exp_src["structural_rows"]
    assert src["causal_rows"] == exp_src["causal_rows"]

    assert actual["classification_counts"] == expected["classification_counts"]
    assert len(actual["results"]) == 27
    assert len(actual["revived_candidates"]) == 1

    revived=actual["revived_candidates"][0]
    exp=expected["revived_candidate"]
    assert revived["spread"] == exp["spread"]
    assert revived["core_regime"] == exp["core_regime"]
    assert revived["causal_direction"] == exp["direction"]
    assert revived["causal_n"] == exp["causal_n"]
    assert close(revived["causal_mean"],exp["causal_mean"])
    assert close(revived["causal_ci_low"],exp["causal_ci_low"])
    assert close(revived["causal_ci_high"],exp["causal_ci_high"])
    assert close(revived["structural_mean"],exp["structural_mean"])
    assert revived["eligible_eras"] == exp["eligible_eras"]
    assert revived["same_sign_eras"] == exp["same_sign_eras"]
    assert close(revived["strongest_era_share"],exp["strongest_era_share"])

    # Bind the classification identity of every cell/spread, independent of CSV bytes.
    classification_map={
        (r["spread"],r["core_regime"]):r["classification"]
        for r in actual["results"]
    }
    assert classification_map[(
        "equity_minus_treasury","Reflation / Inflation Rising"
    )] == "revived_long_history_candidate"
    assert classification_map[(
        "equity_minus_treasury","Disinflationary Drift"
    )] == "long_history_era_dependent"
    assert classification_map[(
        "equity_minus_treasury","Goldilocks / Disinflationary Expansion"
    )] == "long_history_structural_but_timing_unstable"
    assert classification_map[(
        "treasury_minus_cash","Disinflationary Drift"
    )] == "long_history_structural_but_timing_unstable"
    assert classification_map[(
        "gold_minus_cash","Reflation / Inflation Rising"
    )] == "long_history_structural_but_timing_unstable"

    print({
        "finding_bound":True,
        "classification_counts":actual["classification_counts"],
        "revived":revived,
    })


if __name__=="__main__":
    main()
