#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json
from decimal import Decimal,InvalidOperation,ROUND_HALF_EVEN
from pathlib import Path
import pandas as pd

HERE=Path(__file__).resolve().parent
DECISION=HERE/"decisions"/"issue-99-phase-a1-decision.json"

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

def req(x,msg):
    if not x: raise RuntimeError(msg)

def close(a,b,tol=1e-6): return abs(float(a)-float(b))<=tol

def validate(evidence_dir:Path)->dict:
    d=json.loads(DECISION.read_text())
    m=json.loads((evidence_dir/"issue-99-a1-manifest.json").read_text())
    req(d["final_A1_verdict"]=="effr_measurement_not_the_main_problem","verdict drift")
    req(m["treasury_outcomes_loaded"] is False,"Treasury leak")
    req(m["portfolio_results_computed"] is False,"portfolio leak")
    req(m["production_v66_modified"] is False,"V6.6 drift")
    req(m["durable_A1_verdict_committed"] is True,"manifest does not see durable decision")
    req(m["oos"]["forecast_origins"]==426 and m["oos"]["identical_target_samples"] is True,"sample drift")

    for name,expected in d["evidence_binding"]["semantic_sha256"].items():
        req(semantic_csv_sha(evidence_dir/name,8)==expected,f"semantic evidence drift: {name}")

    inc=pd.read_csv(evidence_dir/"issue-99-a1-incremental.csv")
    full=inc.loc[inc["segment"].eq("full")].set_index("target")
    post=inc.loc[inc["segment"].eq("Unconventional_post_Dec2008")].set_index("target")
    req(close(full.loc["EFFR","M2_minus_M1_RMSE"],0.04097091875313841),"EFFR full RMSE delta drift")
    req(close(full.loc["Proxy","M2_minus_M1_RMSE"],0.1201650837720094),"Proxy full RMSE delta drift")
    req(close(full.loc["Proxy","M2_minus_M1_MAE"],0.07510290674883702),"Proxy full MAE delta drift")
    req(float(post.loc["Proxy","M2_minus_M1_RMSE"])>0,"Proxy post-2008 RMSE no longer worse")
    req(float(post.loc["Proxy","M2_minus_M1_MAE"])>0,"Proxy post-2008 MAE no longer worse")

    lo=pd.read_csv(evidence_dir/"issue-99-a1-leave-one-segment-out.csv")
    for target in ("EFFR","Proxy"):
        g=lo.loc[lo["target"].eq(target)]
        req((g["M2_minus_M1_RMSE"]>0).all(),f"{target} leaveout RMSE stability drift")
        req((g["M2_minus_M1_MAE"]>0).all(),f"{target} leaveout MAE stability drift")

    return {
      "validated":True,
      "verdict":d["final_A1_verdict"],
      "proxy_full_M2_minus_M1_RMSE":float(full.loc["Proxy","M2_minus_M1_RMSE"]),
      "proxy_post2008_M2_minus_M1_RMSE":float(post.loc["Proxy","M2_minus_M1_RMSE"]),
      "treasury_outcomes_loaded":False
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--evidence-dir",type=Path,required=True)
    print(json.dumps(validate(ap.parse_args().evidence_dir),indent=2)); return 0

if __name__=="__main__":
    raise SystemExit(main())
