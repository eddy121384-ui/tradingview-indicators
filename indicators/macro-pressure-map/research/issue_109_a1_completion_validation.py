#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
FINDING = HERE / "decisions" / "issue-109-a1-finding.json"


def close(a: float, b: float, tol: float = 1e-12) -> bool:
    return bool(np.isclose(float(a), float(b), rtol=0.0, atol=tol))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()

    expected = json.loads(FINDING.read_text(encoding="utf-8"))
    manifest = json.loads((args.evidence_dir / "issue-109-a1-manifest.json").read_text(encoding="utf-8"))
    cls = pd.read_csv(args.evidence_dir / "issue-109-a1-state-classification.csv")
    rob = pd.read_csv(args.evidence_dir / "issue-109-a1-episode-robustness.csv")

    assert manifest["leg_summary"] == expected["leg_summary"]
    assert manifest["trajectory_loaded"] is False
    assert expected["a2_exact_trajectory_authorized"] is False
    assert expected["production_authorized"] is False

    for item in expected["stable_state_candidates"]:
        row = cls.loc[
            cls["leg"].eq(item["leg"]) & cls["regime_id"].eq(item["regime_id"])
        ]
        assert len(row) == 1
        row = row.iloc[0]
        assert row["regime"] == item["regime"]
        assert int(row["primary_n"]) == item["n"]
        assert row["classification"] == item["classification"]
        assert close(row["primary_mean"], item["mean"])
        assert close(row["primary_ci_low"], item["ci_low"])
        assert close(row["primary_ci_high"], item["ci_high"])

        rr = rob.loc[
            rob["leg"].eq(item["leg"]) & rob["regime_id"].eq(item["regime_id"])
        ]
        assert len(rr) == 1
        rr = rr.iloc[0]
        assert close(rr["top_supporting_share"], item["top_supporting_share"])
        assert int(rr["leaveout_n"]) == item["leaveout_n"]
        assert close(rr["leaveout_mean"], item["leaveout_mean"])
        assert bool(rr["leaveout_sign_retained"]) is True

    r = expected["reflation_equity_vs_duration"]
    row = cls.loc[
        cls["leg"].eq("equity_vs_duration") & cls["regime_id"].eq(r["regime_id"])
    ]
    assert len(row) == 1
    row = row.iloc[0]
    assert int(row["primary_n"]) == r["n"]
    assert row["classification"] == r["classification"]
    assert close(row["primary_mean"], r["mean"])
    assert close(row["primary_ci_low"], r["ci_low"])
    assert close(row["primary_ci_high"], r["ci_high"])

    stable = cls.loc[cls["classification"].eq("stable_directional_candidate")]
    observed = set(zip(stable["leg"], stable["regime_id"].astype(int)))
    required = {(x["leg"], x["regime_id"]) for x in expected["stable_state_candidates"]}
    assert observed == required

    print({
        "leg_summary": manifest["leg_summary"],
        "stable_states": sorted(observed),
        "finding_bound": True,
    })


if __name__ == "__main__":
    main()
