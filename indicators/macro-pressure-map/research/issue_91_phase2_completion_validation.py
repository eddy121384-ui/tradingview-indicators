#!/usr/bin/env python3
"""Fail-closed durable decision validation for Issue #91 Phase 2."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

HERE=Path(__file__).resolve().parent
DECISION=HERE/"decisions"/"issue-91-phase2-decision.json"


def load(path:Path)->dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition:bool,message:str)->None:
    if not condition:
        raise RuntimeError(message)


def close(a:float,b:float,tol:float=1e-6)->bool:
    return abs(float(a)-float(b))<=tol


def find_metric(frame:pd.DataFrame, regime:str, metric:str)->pd.Series:
    row=frame.loc[frame["core_regime"].eq(regime)&frame["metric"].eq(metric)]
    require(len(row)==1,f"expected one metric row: {regime} / {metric}")
    return row.iloc[0]


def validate(evidence_dir:Path)->dict:
    d=load(DECISION)
    m=load(evidence_dir/"issue-91-phase2-manifest.json")
    require(d["final_structural_verdict"]=="inflation_regime_dependent_mapping","durable verdict drift")
    require(m["hmra_freeze_validated_before_asset_join"] is True,"HMRA freeze not validated")
    require(m["etfs_used"] is False,"ETF leaked into Phase 2")
    require(m["portfolio_policy_evaluated"] is False,"portfolio policy leaked into Phase 2")
    require(m["structural_verdict_committed"] is True,"evaluator does not see durable verdict")

    for name,expected in d["evidence_files"].items():
        path=evidence_dir/name
        require(path.exists(),f"missing evidence file: {name}")
        require(sha(path)==expected,f"evidence hash drift: {name}")

    structural=pd.read_csv(evidence_dir/"issue-91-phase2-structural-cell-summary.csv")
    causal=pd.read_csv(evidence_dir/"issue-91-phase2-causal-cell-summary.csv")
    absinf=pd.read_csv(evidence_dir/"issue-91-phase2-absolute-inflation-comparison.csv")
    cross=pd.read_csv(evidence_dir/"issue-91-phase2-cross-source-overall.csv")
    cross_cells=pd.read_csv(evidence_dir/"issue-91-phase2-cross-source-cells.csv")
    loeo=pd.read_csv(evidence_dir/"issue-91-phase2-leave-one-era-out.csv")

    r=find_metric(structural,"Reflation / Inflation Rising","equity_minus_treasury")
    require(int(r["n"])==22 and close(r["arithmetic_mean"],0.1172),"Reflation E-T drift")
    g=find_metric(structural,"Goldilocks / Disinflationary Expansion","equity_minus_treasury")
    require(int(g["n"])==20 and close(g["arithmetic_mean"],0.15308),"Goldilocks E-T drift")
    s=find_metric(structural,"Stagflation Pressure","treasury_minus_cash")
    require(int(s["n"])==19 and close(s["arithmetic_mean"],-0.021374),"Stagflation T-C drift")
    sd=find_metric(structural,"Slowdown / Disinflation","treasury_minus_cash")
    require(int(sd["n"])==15 and close(sd["arithmetic_mean"],0.06038),"Slowdown T-C drift")

    def absrow(regime:str,metric:str)->pd.Series:
        row=absinf.loc[absinf["core_regime"].eq(regime)&absinf["metric"].eq(metric)]
        require(len(row)==1,f"absolute inflation row missing: {regime}/{metric}")
        return row.iloc[0]

    ar=absrow("Reflation / Inflation Rising","treasury_minus_cash")
    require(bool(ar["eligible_both_n_ge_5"]),"Reflation abs-inflation comparison ceased eligible")
    require(close(ar["mean_difference_high_minus_low"],-0.051113),"Reflation inflation interaction drift")
    require(float(ar["bootstrap_difference_ci_high"])<0.0,"Reflation inflation interaction CI no longer excludes zero")

    ast=absrow("Stagflation Pressure","treasury_minus_cash")
    require(bool(ast["eligible_both_n_ge_5"]),"Stagflation abs-inflation comparison ceased eligible")
    require(close(ast["mean_difference_high_minus_low"],-0.061122),"Stagflation inflation interaction drift")
    require(float(ast["bootstrap_difference_ci_high"])<0.0,"Stagflation inflation interaction CI no longer excludes zero")

    cr=find_metric(causal,"Reflation / Inflation Rising","equity_minus_treasury")
    require(close(cr["arithmetic_mean"],0.138136) and float(cr["bootstrap_mean_ci_low"])>0.0,"causal Reflation drift")

    x=cross.iloc[0]
    require(int(x["overlap_years"])==93,"cross-source overlap drift")
    require(close(x["equity_minus_treasury_correlation"],0.9624718020320061,tol=1e-12),"cross-source spread correlation drift")
    eligible=cross_cells.loc[cross_cells["eligible_n_ge_5"]==True]
    require(len(eligible)==5 and eligible["mean_sign_agreement"].astype(bool).all(),"cross-source cell sign agreement drift")

    concentrated=loeo.loc[loeo["era_concentrated"]==True]
    require(len(loeo)==118 and len(concentrated)==17,"leave-one-era-out concentration counts drift")
    st_tc=concentrated.loc[
        concentrated["core_regime"].eq("Stagflation Pressure")
        & concentrated["metric"].eq("treasury_minus_cash")
    ]
    require(len(st_tc)==0,"Stagflation T-C became era-concentrated")

    return {
        "validated":True,
        "verdict":d["final_structural_verdict"],
        "reflation_treasury_cash_high_inflation_difference":float(ar["mean_difference_high_minus_low"]),
        "stagflation_treasury_cash_high_inflation_difference":float(ast["mean_difference_high_minus_low"]),
        "cross_source_cell_sign_agreement":"5/5",
        "portfolio_policy_evaluated":False,
    }


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--evidence-dir",type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(validate(args.evidence_dir),indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
