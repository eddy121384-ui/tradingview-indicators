#!/usr/bin/env python3
"""Issue #117 diagnostic modern-overlap bridge.

Post-payoff diagnostic explicitly permitted by preregistration.
Does not alter the long-history verdict.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from issue_117_long_history_gold_cash import build_outcomes, load_frozen_sources, nonoverlap

HERE = Path(__file__).resolve().parent
TRANSITIONS = HERE / "data" / "issue-64-frozen-regime-transitions.csv"
EXPECTED_TRANSITION_SHA = "80446bbcb91be8b18eb0b95e62466edf892e4c04087696a04532f0fe214698af"
CUTOFF = pd.Timestamp("2026-08-14")


def sha256_file(path: Path) -> str:
    import hashlib
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def exact_state_on_date(transitions: pd.DataFrame, date: pd.Timestamp) -> int | None:
    if date > CUTOFF:
        return None
    starts=transitions["start_date"].to_numpy(dtype="datetime64[ns]")
    pos=int(np.searchsorted(starts,np.datetime64(date),side="right")-1)
    if pos < 0:
        return None
    return int(transitions.iloc[pos]["regime_id"])


def safe_mean(s: pd.Series) -> float | None:
    x=pd.to_numeric(s,errors="coerce").dropna()
    return float(x.mean()) if len(x) else None


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()

    if sha256_file(TRANSITIONS) != EXPECTED_TRANSITION_SHA:
        raise RuntimeError("frozen Issue #64 transition hash mismatch")

    hmra,gold,cash,_=load_frozen_sources()
    out=build_outcomes(hmra,gold,cash)
    out=out.loc[
        (out["decision_date"] >= pd.Timestamp("2007-01-01"))
        & (out["decision_date"] <= CUTOFF)
        & out["spread_3M"].notna()
    ].copy()

    tr=pd.read_csv(TRANSITIONS)
    tr["start_date"]=pd.to_datetime(tr["start_date"],errors="raise")
    tr=tr.sort_values("start_date").reset_index(drop=True)

    # Previous calendar day is a conservative proxy for "state known before decision month".
    out["exact_regime_id"]=[
        exact_state_on_date(tr,pd.Timestamp(d)-pd.Timedelta(days=1))
        for d in out["decision_date"]
    ]
    out=out.loc[out["exact_regime_id"].notna()].copy()
    out["exact_defensive"]=out["exact_regime_id"].astype(int).isin([7,8,9])
    out["hmra_defensive"]=out["defensive"].astype(bool)

    tp=int((out["exact_defensive"] & out["hmra_defensive"]).sum())
    fp=int((~out["exact_defensive"] & out["hmra_defensive"]).sum())
    fn=int((out["exact_defensive"] & ~out["hmra_defensive"]).sum())
    tn=int((~out["exact_defensive"] & ~out["hmra_defensive"]).sum())

    agreement=(tp+tn)/len(out) if len(out) else np.nan
    precision=tp/(tp+fp) if tp+fp else np.nan
    recall=tp/(tp+fn) if tp+fn else np.nan
    jaccard=tp/(tp+fp+fn) if tp+fp+fn else np.nan

    hmra_all=out.loc[out["hmra_defensive"]]
    exact_all=out.loc[out["exact_defensive"]]
    both_all=out.loc[out["hmra_defensive"] & out["exact_defensive"]]

    hmra_non=nonoverlap(hmra_all,3)
    exact_non=nonoverlap(exact_all,3)
    both_non=nonoverlap(both_all,3)

    result={
        "schema_version":1,
        "issue":117,
        "role":"post-payoff diagnostic modern overlap bridge; no verdict authority",
        "transition_sha256":EXPECTED_TRANSITION_SHA,
        "window":{
            "first":out["decision_date"].min().date().isoformat() if len(out) else None,
            "last":out["decision_date"].max().date().isoformat() if len(out) else None,
            "months":int(len(out)),
        },
        "confusion":{
            "tp":tp,"fp":fp,"fn":fn,"tn":tn,
            "agreement_rate":float(agreement),
            "precision_hmra_vs_exact":float(precision),
            "recall_hmra_vs_exact":float(recall),
            "jaccard_defensive_overlap":float(jaccard),
        },
        "all_monthly":{
            "hmra_defensive_n":int(len(hmra_all)),
            "hmra_defensive_mean_spread_3m":safe_mean(hmra_all["spread_3M"]),
            "exact_defensive_n":int(len(exact_all)),
            "exact_defensive_mean_spread_3m":safe_mean(exact_all["spread_3M"]),
            "both_defensive_n":int(len(both_all)),
            "both_defensive_mean_spread_3m":safe_mean(both_all["spread_3M"]),
        },
        "nonoverlap_3m":{
            "hmra_defensive_n":int(len(hmra_non)),
            "hmra_defensive_mean_spread_3m":safe_mean(hmra_non["spread_3M"]),
            "exact_defensive_n":int(len(exact_non)),
            "exact_defensive_mean_spread_3m":safe_mean(exact_non["spread_3M"]),
            "both_defensive_n":int(len(both_non)),
            "both_defensive_mean_spread_3m":safe_mean(both_non["spread_3M"]),
        },
        "interpretation_guard":[
            "Diagnostic only; do not tune monthly HMRA to improve overlap.",
            "Exact V6.6 transition state is sampled on the calendar day before each monthly decision.",
            "This bridge does not alter the preregistered long-history verdict."
        ],
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=="__main__":
    main()
