#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from decimal import Decimal,InvalidOperation,ROUND_HALF_EVEN
from pathlib import Path
import pandas as pd

HERE=Path(__file__).resolve().parent
DECISION=HERE/"decisions"/"issue-101-decision.json"

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
    m=json.loads((evidence_dir/"issue-101-manifest.json").read_text())
    req(d["final_verdict"]=="state_dependence_not_enough_linear_speed_problem_persists","verdict drift")
    req(m["treasury_outcomes_loaded"] is False,"Treasury leak")
    req(m["portfolio_results_computed"] is False,"portfolio leak")
    req(m["production_v66_modified"] is False,"V6.6 drift")
    req(m["durable_verdict_committed"] is True,"manifest does not see decision")
    req(m["oos"]["forecast_origins"]==426,"OOS sample drift")

    for name,expected in d["evidence_binding"]["semantic_sha256"].items():
        req(semantic_csv_sha(evidence_dir/name,8)==expected,f"semantic evidence drift: {name}")

    inc=pd.read_csv(evidence_dir/"issue-101-incremental.csv")
    full=inc.loc[(inc["target"].eq("Proxy"))&(inc["segment"].eq("full"))].set_index("comparison")
    req(close(full.loc["M3_minus_M2","delta_RMSE"],0.030252687094787234),"Proxy M3-M2 RMSE drift")
    req(close(full.loc["M3_minus_M2","delta_MAE"],0.02132640706380884),"Proxy M3-M2 MAE drift")
    req(close(full.loc["M3_minus_M1","delta_RMSE"],0.15041777086679642),"Proxy M3-M1 RMSE drift")
    req(float(full.loc["M3_minus_M2","delta_RMSE"])>0 and float(full.loc["M3_minus_M2","delta_MAE"])>0,"M3 no longer worse full-sample")

    seg=inc.loc[(inc["target"].eq("Proxy"))&(inc["comparison"].eq("M3_minus_M2"))&(inc["segment"].ne("full"))]
    req((seg["delta_RMSE"]>0).all(),"M3 no longer worse RMSE in every segment")
    req((seg["delta_MAE"]>0).all(),"M3 no longer worse MAE in every segment")

    lo=pd.read_csv(evidence_dir/"issue-101-leave-one-segment-out.csv")
    p=lo.loc[lo["target"].eq("Proxy")]
    req((p["M3_minus_M2_RMSE"]>0).all(),"leaveout RMSE result drift")
    req((p["M3_minus_M2_MAE"]>0).all(),"leaveout MAE result drift")

    return {
      "validated":True,
      "verdict":d["final_verdict"],
      "proxy_M3_minus_M2_RMSE":float(full.loc["M3_minus_M2","delta_RMSE"]),
      "proxy_M3_minus_M1_RMSE":float(full.loc["M3_minus_M1","delta_RMSE"]),
      "treasury_outcomes_loaded":False
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--evidence-dir",type=Path,required=True)
    print(json.dumps(validate(ap.parse_args().evidence_dir),indent=2)); return 0

if __name__=="__main__":
    raise SystemExit(main())
