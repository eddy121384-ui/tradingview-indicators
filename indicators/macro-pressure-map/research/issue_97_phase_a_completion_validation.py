#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from decimal import Decimal,InvalidOperation,ROUND_HALF_EVEN
from pathlib import Path
import pandas as pd

HERE=Path(__file__).resolve().parent
DECISION=HERE/"decisions"/"issue-97-phase-a-decision.json"

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
    return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def req(x,msg):
    if not x: raise RuntimeError(msg)

def close(a,b,tol=1e-6): return abs(float(a)-float(b))<=tol

def validate(evidence_dir:Path)->dict:
    d=json.loads(DECISION.read_text())
    m=json.loads((evidence_dir/"issue-97-phase-a-manifest.json").read_text())
    req(d["final_phase_a_verdict"]=="policy_relation_era_dependent","verdict drift")
    req(m["treasury_outcomes_loaded"] is False,"Treasury outcome leak")
    req(m["portfolio_results_computed"] is False,"portfolio outcome leak")
    req(m["production_v66_modified"] is False,"V6.6 drift")
    req(m["durable_phase_a_verdict_committed"] is True,"manifest does not see durable decision")

    for name,expected in d["evidence_binding"]["semantic_sha256"].items():
        req(semantic_csv_sha(evidence_dir/name,8)==expected,f"semantic evidence drift: {name}")

    s=pd.read_csv(evidence_dir/"issue-97-phase-a-summary.csv")
    full=s.loc[(s.target=="policy_change_6m")&(s.window=="expanding")&(s.segment=="full")].set_index("model")
    m1=full.loc["M1"]; m2=full.loc["M2"]
    req(close(m1["RMSE"],1.623133),"M1 RMSE drift")
    req(close(m2["RMSE"],1.660240),"M2 RMSE drift")
    req(close(m2["RMSE"]-m1["RMSE"],0.037106),"M2-M1 RMSE drift")
    req(close(m2["MAE"]-m1["MAE"],0.024100),"M2-M1 MAE drift")
    req(close(m2["balanced_accuracy"]-m1["balanced_accuracy"],0.003243),"balanced accuracy drift")

    inc=pd.read_csv(evidence_dir/"issue-97-phase-a-incremental.csv")
    eras=inc.loc[(inc.target=="policy_change_6m")&(inc.window=="expanding")&(inc.segment!="full")]
    req((eras["M2_minus_M1_RMSE"]>0).all(),"M2 no longer worse RMSE across every era")

    lo=pd.read_csv(evidence_dir/"issue-97-phase-a-leave-one-era-out.csv")
    req((lo["M2_minus_M1_RMSE"]>0).all(),"leave-one-era-out RMSE result drift")
    req((lo["M2_minus_M1_MAE"]>0).all(),"leave-one-era-out MAE result drift")

    return {
      "validated":True,
      "verdict":d["final_phase_a_verdict"],
      "M2_minus_M1_RMSE":float(m2["RMSE"]-m1["RMSE"]),
      "M2_minus_M1_MAE":float(m2["MAE"]-m1["MAE"]),
      "treasury_outcomes_loaded":False,
      "phase_b_status":d["phase_b_status"]
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--evidence-dir",type=Path,required=True)
    print(json.dumps(validate(ap.parse_args().evidence_dir),indent=2)); return 0

if __name__=="__main__":
    raise SystemExit(main())
