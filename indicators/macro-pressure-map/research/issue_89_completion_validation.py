#!/usr/bin/env python3
"""Fail-closed completion validator for Issue #89 durable evidence."""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
import pandas as pd

HERE=Path(__file__).resolve().parent
DECISION=HERE/"decisions"/"issue-89-decision.json"
PRIMARY=HERE/"decisions"/"issue-89-preregistered-policy.json"
ROBUSTNESS=HERE/"decisions"/"issue-89-episode-robustness-preregistered.json"
STRATEGY="v66_ex_ante_regime_policy"
ALLOWED={"useful_regime_switching_policy","risk_management_value_only","allocation_mix_value_only_no_switching_value","no_material_policy_value","inconclusive_insufficient_evidence"}

def _reject(value:str)->None: raise ValueError(f"non-finite JSON constant: {value}")
def load_json(path:Path)->dict: return json.loads(path.read_text(encoding="utf-8"),parse_constant=_reject)
def sha256_file(path:Path)->str:
    d=hashlib.sha256()
    with path.open("rb") as h:
        for chunk in iter(lambda:h.read(1024*1024),b""): d.update(chunk)
    return d.hexdigest()
def finite(name:str,value:object)->float:
    x=float(value)
    if not math.isfinite(x): raise ValueError(f"{name} non-finite: {x}")
    return x
def close(name:str,actual:object,expected:object,tol:float=1e-12)->None:
    a,e=finite(name+".actual",actual),finite(name+".expected",expected)
    err=abs(a-e)
    if not math.isfinite(err) or err>tol: raise RuntimeError(f"{name} drifted: {a} != {e}, error={err}")
def one(frame:pd.DataFrame,**filters:object)->pd.Series:
    mask=pd.Series(True,index=frame.index)
    for col,val in filters.items(): mask &= frame[col].eq(val)
    rows=frame.loc[mask]
    if len(rows)!=1: raise RuntimeError(f"expected one row for {filters}, got {len(rows)}")
    return rows.iloc[0]

def validate(evidence_dir:Path)->dict:
    decision,primary,robustness=load_json(DECISION),load_json(PRIMARY),load_json(ROBUSTNESS)
    if decision.get("issue")!=89 or decision.get("post_evaluation_synthesis") is not True: raise ValueError("invalid Issue #89 decision")
    if primary.get("frozen_before_issue_89_portfolio_results_viewed") is not True: raise RuntimeError("primary policy was not frozen")
    if primary.get("return_fitted_weight_selection_allowed") is not False or primary.get("weight_tuning_after_results_allowed") is not False: raise RuntimeError("primary policy permits forbidden fitting/tuning")
    if robustness.get("primary_policy_modified") is not False or robustness.get("primary_portfolio_results_already_viewed") is not True or robustness.get("frozen_before_issue_89_episode_results_viewed") is not True: raise RuntimeError("invalid secondary robustness boundary")
    verdict=decision["decision"]; category=verdict["final_category"]
    if category not in ALLOWED or category!="inconclusive_insufficient_evidence": raise RuntimeError(f"final category drifted: {category}")
    if verdict["retune_policy_allowed"] is not False or verdict["production_allocator_validated"] is not False: raise RuntimeError("forbidden final decision flags")

    hashes={}
    for name,expected in decision["exact_generated_file_sha256"].items():
        path=evidence_dir/name
        if not path.exists(): raise FileNotFoundError(path)
        actual=sha256_file(path); hashes[name]=actual
        if actual!=expected: raise RuntimeError(f"generated evidence drifted: {name}: {actual} != {expected}")

    manifest=load_json(evidence_dir/"issue-89-manifest.json"); source=decision["source_evidence"]
    if manifest["durable_verdict_committed"] is not True: raise RuntimeError("manifest does not acknowledge durable verdict")
    for key in ("price_snapshot_csv_sha256","price_snapshot_archive_sha256","evaluation_first_date","evaluation_last_date","evaluation_rows","primary_cost_bps","policy_transition_count"):
        if manifest[key]!=source[key]: raise RuntimeError(f"manifest field drifted: {key}")

    summary=pd.read_csv(evidence_dir/"issue-89-summary.csv")
    exposure=pd.read_csv(evidence_dir/"issue-89-exposure-match.csv")
    costs=pd.read_csv(evidence_dir/"issue-89-cost-sensitivity.csv")
    episodes=load_json(evidence_dir/"issue-89-episode-robustness.json")
    keys=decision["key_metrics"]

    for segment,key in (("full_reused_history","policy_full_history"),("development_pre2020","policy_development_pre2020"),("post2019_reused_exploratory","policy_post2019_reused_exploratory")):
        row=one(summary,strategy=STRATEGY,segment=segment)
        for metric,expected in keys[key].items(): close(f"summary.{segment}.{metric}",row[metric],expected)

    for segment,expected in keys["exposure_matched_switching_attribution"].items():
        row=one(exposure,segment=segment)
        for metric,value in expected.items(): close(f"exposure.{segment}.{metric}",row[metric],value)

    full,pre,post=(one(exposure,segment=s) for s in ("full_reused_history","development_pre2020","post2019_reused_exploratory"))
    if not(full["delta_CAGR"]>0 and full["delta_Sharpe"]>0): raise RuntimeError("full switching value no longer positive")
    if not(pre["delta_CAGR"]>0 and pre["delta_Sharpe"]>0): raise RuntimeError("pre-2020 switching value no longer positive")
    if not(post["delta_CAGR"]<0 and post["delta_Sharpe"]<0): raise RuntimeError("post-2019 switching value no longer negative")
    if not full["delta_maximum_drawdown"]<0: raise RuntimeError("full drawdown no longer worse than matched static")
    tol=float(primary["benchmarks"]["realized_exposure_matched_static_control"]["max_abs_invested_weight_mismatch"])
    if exposure["max_abs_invested_weight_mismatch"].abs().max()>tol: raise RuntimeError("exposure-match tolerance exceeded")

    for label,expected in keys["policy_cost_sensitivity"].items():
        row=one(costs,strategy=STRATEGY,cost_bps=float(label.removesuffix("bp")))
        for metric,value in expected.items(): close(f"cost.{label}.{metric}",row[metric],value)

    rows={r["segment"]:r for r in episodes["summary_rows"]}
    for segment,expected in keys["episode_robustness"].items():
        actual=rows[segment]; win=actual["largest_positive_episode"]
        name=f"{win['regime']} | {win['start']} through {win['end']}"
        if name!=expected["largest_positive_episode"]: raise RuntimeError(f"largest positive episode drifted in {segment}")
        close(f"episode.{segment}.winner",win["active_log_return"],expected["largest_positive_active_log"])
        close(f"episode.{segment}.top1",actual["top1_share_of_positive_episode_contribution"],expected["top1_share_positive"])
        close(f"episode.{segment}.normal",actual["normal_active_log_return"],expected["normal_active_log"])
        close(f"episode.{segment}.leaveout",actual["active_log_after_removing_largest_positive_episode"],expected["leaveout_active_log"])
        close(f"episode.{segment}.leaveout_cagr",actual["incremental_after_leaveout"]["delta_CAGR"],expected["leaveout_delta_CAGR"])
        close(f"episode.{segment}.leaveout_sharpe",actual["incremental_after_leaveout"]["delta_Sharpe"],expected["leaveout_delta_Sharpe"])
        close(f"episode.{segment}.leaveout_mismatch",actual["leaveout_realized_exposure_matching"]["max_abs_invested_weight_mismatch"],expected["leaveout_max_abs_exposure_mismatch"])

    if not rows["full_reused_history"]["active_log_after_removing_largest_positive_episode"]>0: raise RuntimeError("full switching value does not survive leaveout")
    if not rows["development_pre2020"]["active_log_after_removing_largest_positive_episode"]>0: raise RuntimeError("pre-2020 switching value does not survive leaveout")
    if not(rows["post2019_reused_exploratory"]["normal_active_log_return"]<0 and rows["post2019_reused_exploratory"]["active_log_after_removing_largest_positive_episode"]<0): raise RuntimeError("post-2019 negative attribution contract drifted")
    return {"validated":True,"final_category":category,"evidence_files_bound":len(hashes),"full_delta_CAGR":float(full["delta_CAGR"]),"pre2020_delta_CAGR":float(pre["delta_CAGR"]),"post2019_delta_CAGR":float(post["delta_CAGR"]),"full_leaveout_active_log":float(rows["full_reused_history"]["active_log_after_removing_largest_positive_episode"]),"post2019_leaveout_active_log":float(rows["post2019_reused_exploratory"]["active_log_after_removing_largest_positive_episode"])}

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--evidence-dir",type=Path,required=True); a=p.parse_args()
    print(json.dumps(validate(a.evidence_dir),indent=2,allow_nan=False)); return 0
if __name__=="__main__": raise SystemExit(main())
