#!/usr/bin/env python3
"""Issue #117 Phase 1 — preregistered long-history Gold vs Cash validation."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from issue_117_source_freeze import run as run_source_freeze

HERE = Path(__file__).resolve().parent
DECISIONS = HERE / "decisions"
SOURCE_FREEZE = DECISIONS / "issue-117-source-freeze.json"

DEFENSIVE = (
    "Slowdown / Disinflation",
    "Growth Slowdown / Stable Inflation",
    "Stagflation Pressure",
)
BOOTSTRAP_REPS = 10_000


def stable_seed(*parts: object) -> int:
    payload = "|".join(str(x) for x in parts).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & 0xFFFFFFFF


def month_ord(ts: pd.Timestamp) -> int:
    return ts.year * 12 + ts.month


def era(ts: pd.Timestamp) -> str:
    if ts <= pd.Timestamp("1989-12-01"):
        return "1975_1989"
    if ts <= pd.Timestamp("2006-12-01"):
        return "1990_2006"
    if ts <= pd.Timestamp("2019-12-01"):
        return "2007_2019"
    return "2020_latest"


def summarize(values: pd.Series | np.ndarray, *, seed: int) -> dict:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    n = int(len(arr))
    if n == 0:
        return {"n":0,"mean":math.nan,"median":math.nan,"std":math.nan,"positive_fraction":math.nan,"ci_low":math.nan,"ci_high":math.nan}
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(BOOTSTRAP_REPS, n))
    means = arr[idx].mean(axis=1)
    lo, hi = np.quantile(means, [0.025, 0.975])
    return {
        "n":n,
        "mean":float(arr.mean()),
        "median":float(np.median(arr)),
        "std":float(np.std(arr, ddof=1)) if n >= 2 else math.nan,
        "positive_fraction":float(np.mean(arr > 0)),
        "ci_low":float(lo),
        "ci_high":float(hi),
    }


def nonoverlap(df: pd.DataFrame, months: int = 3) -> pd.DataFrame:
    g = df.sort_values("decision_date").copy()
    keep = []
    last_ord = None
    for i, row in g.iterrows():
        o = month_ord(pd.Timestamp(row["decision_date"]))
        if last_ord is None or o - last_ord >= months:
            keep.append(i)
            last_ord = o
    return g.loc[keep].copy().reset_index(drop=True)


def load_frozen_sources() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    expected = json.loads(SOURCE_FREEZE.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        manifest = run_source_freeze(out)
        if manifest["source_hashes"] != expected["source_hashes"]:
            raise RuntimeError("Issue #117 source hashes changed after preregistration")
        actual_gen = {
            "monthly_hmra": manifest["files"]["macro"]["sha256"],
            "gold_monthly": manifest["files"]["gold"]["sha256"],
            "cash_rf_monthly": manifest["files"]["cash"]["sha256"],
        }
        if actual_gen != expected["generated_hashes"]:
            raise RuntimeError("Issue #117 generated source snapshots changed after preregistration")
        hmra = pd.read_csv(out/"issue-117-monthly-hmra.csv")
        gold = pd.read_csv(out/"issue-117-gold-monthly.csv")
        cash = pd.read_csv(out/"issue-117-cash-rf-monthly.csv")
    for df in (hmra,gold,cash):
        df["date"] = pd.to_datetime(df["date"], errors="raise")
    return hmra, gold, cash, manifest


def build_outcomes(hmra: pd.DataFrame, gold: pd.DataFrame, cash: pd.DataFrame) -> pd.DataFrame:
    gold_s = gold.set_index("date")["gold_usd"].astype(float)
    rf_s = cash.set_index("date")["rf_return"].astype(float)

    rows = []
    valid = hmra.loc[
        (hmra["date"] >= pd.Timestamp("1974-11-01"))
        & hmra["regime"].ne("n/a")
    ].copy()

    for _, r in valid.iterrows():
        source_date = pd.Timestamp(r["date"])
        decision = source_date + pd.DateOffset(months=2)
        if decision < pd.Timestamp("1975-01-01"):
            continue

        rec = {
            "source_date":source_date,
            "decision_date":decision,
            "growth_score":float(r["growth_score"]),
            "inflation_score":float(r["inflation_score"]),
            "regime":str(r["regime"]),
            "defensive":str(r["regime"]) in DEFENSIVE,
            "era":era(decision),
        }

        for label, h in (("1M",1),("3M",3),("6M",6)):
            start = decision + pd.DateOffset(months=1)
            end = decision + pd.DateOffset(months=h+1)
            months = [decision + pd.DateOffset(months=k) for k in range(1,h+1)]
            if start in gold_s.index and end in gold_s.index and all(m in rf_s.index for m in months):
                gret = float(gold_s.loc[end] / gold_s.loc[start] - 1.0)
                cret = float(np.prod([1.0 + float(rf_s.loc[m]) for m in months]) - 1.0)
                rec[f"gold_{label}"] = gret
                rec[f"cash_{label}"] = cret
                rec[f"spread_{label}"] = gret - cret
            else:
                rec[f"gold_{label}"] = math.nan
                rec[f"cash_{label}"] = math.nan
                rec[f"spread_{label}"] = math.nan
        rows.append(rec)

    out = pd.DataFrame(rows).sort_values("decision_date").reset_index(drop=True)
    return out


def assign_episodes(defensive: pd.DataFrame) -> pd.DataFrame:
    g = defensive.sort_values("decision_date").copy()
    ids=[]
    ep=0
    prev=None
    for d in g["decision_date"]:
        o=month_ord(pd.Timestamp(d))
        if prev is None or o-prev != 1:
            ep += 1
        ids.append(ep)
        prev=o
    g["episode_id"]=ids
    return g


def evaluate(outcomes: pd.DataFrame) -> dict:
    primary_all = outcomes.loc[
        outcomes["defensive"] & outcomes["spread_3M"].notna()
    ].copy()
    primary = nonoverlap(primary_all, 3)
    full = summarize(primary["spread_3M"], seed=stable_seed(117,"full","3M"))

    era_stats={}
    evaluable=[]
    for e in ("1975_1989","1990_2006","2007_2019","2020_latest"):
        s=primary.loc[primary["era"].eq(e)]
        st=summarize(s["spread_3M"], seed=stable_seed(117,"era",e))
        era_stats[e]=st
        if st["n"] >= 5:
            evaluable.append(e)

    eps = assign_episodes(primary_all)
    ep_rows=[]
    for eid, g in eps.groupby("episode_id"):
        ep_rows.append({
            "episode_id":int(eid),
            "start":g["decision_date"].min().date().isoformat(),
            "end":g["decision_date"].max().date().isoformat(),
            "months":int(len(g)),
            "contribution_sum":float(g["spread_3M"].sum()),
        })
    episodes=pd.DataFrame(ep_rows)

    positive=episodes.loc[episodes["contribution_sum"]>0].copy()
    if len(positive):
        strongest=positive.sort_values("contribution_sum",ascending=False).iloc[0]
        pos_total=float(positive["contribution_sum"].sum())
        top_share=float(strongest["contribution_sum"]/pos_total)
        start=pd.Timestamp(strongest["start"])
        end=pd.Timestamp(strongest["end"])
        leave=primary.loc[~((primary["decision_date"]>=start)&(primary["decision_date"]<=end))]
        leave_stats=summarize(leave["spread_3M"], seed=stable_seed(117,"leave_episode"))
        strongest_dict={
            "episode_id":int(strongest["episode_id"]),
            "start":strongest["start"],
            "end":strongest["end"],
            "months":int(strongest["months"]),
            "contribution_sum":float(strongest["contribution_sum"]),
            "top_positive_share":top_share,
        }
    else:
        leave_stats=summarize([],seed=1)
        strongest_dict={"episode_id":None,"top_positive_share":math.nan}

    loo={}
    for removed in DEFENSIVE:
        sample=primary_all.loc[~primary_all["regime"].eq(removed)]
        selected=nonoverlap(sample,3)
        loo[removed]=summarize(selected["spread_3M"],seed=stable_seed(117,"loo",removed))

    substates={}
    for state in DEFENSIVE:
        sample=primary.loc[primary["regime"].eq(state)]
        substates[state]=summarize(sample["spread_3M"],seed=stable_seed(117,"state",state))

    diagnostics={}
    for horizon in ("1M","6M"):
        s=outcomes.loc[outcomes["defensive"] & outcomes[f"spread_{horizon}"].notna()]
        diagnostics[horizon]=summarize(s[f"spread_{horizon}"],seed=stable_seed(117,"diag",horizon))

    sample_span=(primary_all["decision_date"].max()-primary_all["decision_date"].min()).days/365.2425 if len(primary_all) else 0
    positive_eras=sum(era_stats[e]["mean"]>0 for e in evaluable)
    min_era=min((era_stats[e]["mean"] for e in evaluable), default=math.nan)

    gates={
        "1_span_ge_45_years":sample_span >= 45,
        "2_primary_n_ge_30":full["n"] >= 30,
        "3_full_ci_positive":full["ci_low"] > 0,
        "4_at_least_3_evaluable_eras":len(evaluable) >= 3,
        "5_at_least_3_evaluable_eras_positive":positive_eras >= 3,
        "6_no_evaluable_era_below_minus_5pct":bool(evaluable) and min_era >= -0.05,
        "7_strongest_episode_leaveout_positive":leave_stats["mean"] > 0,
        "8_top_positive_episode_share_le_35pct":np.isfinite(strongest_dict.get("top_positive_share",math.nan)) and strongest_dict["top_positive_share"] <= 0.35,
        "9_all_leave_one_substate_out_positive":all(v["mean"] > 0 for v in loo.values()),
    }

    if sample_span < 45 or full["n"] < 30 or len(evaluable) < 3:
        verdict="inconclusive_data_or_definition_limitations"
    elif full["ci_low"] > 0:
        verdict="long_history_supports_structural_gold_cash_relationship" if all(gates.values()) else "long_history_relationship_era_dependent"
    else:
        verdict="long_history_no_material_gold_cash_relationship"

    return {
        "verdict":verdict,
        "gates":gates,
        "sample_span_years":float(sample_span),
        "primary_full":full,
        "eras":era_stats,
        "evaluable_eras":evaluable,
        "positive_evaluable_eras":int(positive_eras),
        "strongest_positive_episode":strongest_dict,
        "episode_leaveout":leave_stats,
        "leave_one_substate_out":loo,
        "substates":substates,
        "diagnostics":diagnostics,
        "episodes":episodes,
        "primary_rows":primary,
        "all_defensive_rows":primary_all,
    }


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)

    hmra,gold,cash,manifest=load_frozen_sources()
    outcomes=build_outcomes(hmra,gold,cash)
    ev=evaluate(outcomes)

    serial=outcomes.copy()
    for c in ("source_date","decision_date"):
        serial[c]=pd.to_datetime(serial[c]).dt.strftime("%Y-%m-%d")
    panel_path=args.output_dir/"issue-117-outcomes.csv"
    serial.to_csv(panel_path,index=False,float_format="%.12g")

    primary=ev.pop("primary_rows")
    all_def=ev.pop("all_defensive_rows")
    episodes=ev.pop("episodes")
    for df,name in ((primary,"issue-117-primary-nonoverlap.csv"),(all_def,"issue-117-defensive-allmonthly.csv"),(episodes,"issue-117-episodes.csv")):
        d=df.copy()
        for c in ("source_date","decision_date"):
            if c in d.columns:
                d[c]=pd.to_datetime(d[c]).dt.strftime("%Y-%m-%d")
        d.to_csv(args.output_dir/name,index=False,float_format="%.12g")

    result={
        "schema_version":1,
        "issue":117,
        "phase":"long-history-gold-cash-payoff",
        "source_freeze_hashes":manifest["source_hashes"],
        "source_coverage":manifest["common_source_coverage"],
        "result":ev,
    }
    # Convert any numpy bools/nans in nested structure.
    text=json.dumps(result,indent=2,ensure_ascii=False,allow_nan=True,default=lambda x: bool(x) if isinstance(x,np.bool_) else float(x))
    (args.output_dir/"issue-117-result.json").write_text(text+"\n",encoding="utf-8")
    print(json.dumps({
        "verdict":ev["verdict"],
        "gates":ev["gates"],
        "sample_span_years":ev["sample_span_years"],
        "primary_full":ev["primary_full"],
        "eras":ev["eras"],
        "episode_leaveout":ev["episode_leaveout"],
        "leave_one_substate_out":ev["leave_one_substate_out"],
    },indent=2,ensure_ascii=False,default=lambda x: bool(x) if isinstance(x,np.bool_) else float(x)))


if __name__=="__main__":
    main()
