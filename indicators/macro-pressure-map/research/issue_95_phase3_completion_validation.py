#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, hashlib, json
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from pathlib import Path
import pandas as pd

HERE=Path(__file__).resolve().parent
DECISION=HERE/"decisions"/"issue-95-phase3-decision.json"


def semantic_csv_sha(path:Path,decimals:int=8)->str:
    q=Decimal(1).scaleb(-decimals); rows=[]
    with path.open("r",encoding="utf-8",newline="") as fh:
        for row in csv.DictReader(fh):
            rec={}
            for k,v in row.items():
                if v is None or v=="": rec[k]=None; continue
                lv=v.strip().lower()
                if lv=="true": rec[k]=True; continue
                if lv=="false": rec[k]=False; continue
                try: rec[k]=format(Decimal(v).quantize(q,rounding=ROUND_HALF_EVEN),f".{decimals}f")
                except InvalidOperation: rec[k]=v
            rows.append(rec)
    payload=json.dumps(rows,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()


def require(x:bool,msg:str):
    if not x: raise RuntimeError(msg)


def close(a,b,tol=1e-6):
    return abs(float(a)-float(b))<=tol


def validate(evidence_dir:Path)->dict:
    d=json.loads(DECISION.read_text())
    m=json.loads((evidence_dir/"issue-95-manifest.json").read_text())
    require(d["final_verdict"]=="no_material_overlay_value","verdict drift")
    require(m["durable_verdict_committed"] is True,"manifest does not see decision")
    require(m["hmra_freeze_validated"] is True,"HMRA freeze failed")
    require(m["production_v66_modified"] is False and m["hmra_modified"] is False and m["base_policy_modified"] is False,"research boundary drift")
    require(m["etfs_used"] is False,"ETF leak")
    require(m["primary"]=={"threshold_pct":4.0,"redirect_fraction":0.5,"cost_bps":5.0},"primary parameter drift")
    require(m["sample"]["years"]==51 and m["sample"]["overlay_active_years"]==16,"sample drift")
    require(m["matched_static_max_abs_exposure_mismatch"]<=1e-9,"matched-static mismatch")

    for name,expected in d["evidence_binding"]["semantic_sha256"].items():
        actual=semantic_csv_sha(evidence_dir/name,d["evidence_binding"]["numeric_round_decimals"])
        require(actual==expected,f"semantic evidence drift: {name}")

    s=pd.read_csv(evidence_dir/"issue-95-summary.csv").set_index("strategy")
    o=s.loc["inflation_overlay_50"]; b=s.loc["base_issue89_policy"]; mt=s.loc["matched_static_4asset"]
    require(close(o["CAGR"]-b["CAGR"],0.00027164475340635263),"overlay/base CAGR drift")
    require(close(o["Sharpe_using_TBill"]-b["Sharpe_using_TBill"],0.00801324239323209),"overlay/base Sharpe drift")
    require(close(o["maximum_drawdown"]-b["maximum_drawdown"],0.0),"overlay/base maxDD drift")
    require(close(o["CAGR"]-mt["CAGR"],0.0013775208725415045),"overlay/matched CAGR drift")
    require(close(o["Sharpe_using_TBill"]-mt["Sharpe_using_TBill"],-0.013132338191186643),"overlay/matched Sharpe drift")
    require(close(o["maximum_drawdown"]-mt["maximum_drawdown"],-0.03067976125848848),"overlay/matched maxDD drift")

    ep=pd.read_csv(evidence_dir/"issue-95-active-episodes.csv")
    require(len(ep)==4,"episode count drift")
    pos=ep.loc[ep["overlay_minus_base_active_log"]>0,"overlay_minus_base_active_log"].sort_values(ascending=False)
    require(len(pos)==3,"positive episode count drift")
    require(close(float(pos.iloc[0]/pos.sum()),0.5279196322190152),"top episode concentration drift")

    lo=pd.read_csv(evidence_dir/"issue-95-leave-one-era-out.csv")
    require((lo["delta_CAGR_vs_base"]<0).any(),"leave-one-era-out no longer flips overlay/base CAGR sign")
    require((lo["delta_CAGR_vs_matched"]<0).any() and (lo["delta_CAGR_vs_matched"]>0).any(),"matched-static leaveout sign no longer unstable")

    return {
        "validated":True,
        "verdict":d["final_verdict"],
        "delta_CAGR_vs_base":float(o["CAGR"]-b["CAGR"]),
        "delta_Sharpe_vs_base":float(o["Sharpe_using_TBill"]-b["Sharpe_using_TBill"]),
        "delta_maxDD_vs_base":float(o["maximum_drawdown"]-b["maximum_drawdown"]),
        "top1_positive_episode_share":float(pos.iloc[0]/pos.sum()),
        "production_change_authorized":False,
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--evidence-dir",type=Path,required=True)
    print(json.dumps(validate(ap.parse_args().evidence_dir),indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
