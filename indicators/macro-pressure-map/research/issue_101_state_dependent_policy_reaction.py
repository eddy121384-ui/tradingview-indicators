#!/usr/bin/env python3
"""Issue #101: preregistered state-dependent policy reaction test."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from issue_99_phase_a1_effr_vs_proxy import (
    validate_contracts as validate_issue99_contracts,
    build_a1_frame,
    classify,
    balanced_accuracy,
    segment_label,
)

HERE=Path(__file__).resolve().parent
PREREG=HERE/"decisions"/"issue-101-state-dependent-policy-reaction-preregistered.json"
DECISION=HERE/"decisions"/"issue-101-decision.json"

RAW_MACRO=[
    "inflation_level_lag2",
    "growth_level_lag2",
    "inflation_acceleration_lag2",
    "growth_acceleration_lag2",
]
ZMAP={
    "inflation_level_lag2":"z_inflation_level",
    "growth_level_lag2":"z_growth_level",
    "inflation_acceleration_lag2":"z_inflation_acceleration",
    "growth_acceleration_lag2":"z_growth_acceleration",
}


def load_json(path:Path)->dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_prereg()->dict:
    p=load_json(PREREG)
    if not p["created_before_model_outcomes"] or not p["created_before_treasury_outcomes"]:
        raise RuntimeError("Issue #101 prereg timing guard failed")
    if p["production_v66_modified"] or p["hmra_modified"]:
        raise RuntimeError("research boundary drift")
    return p


def target_columns(target:str)->tuple[str,str,str]:
    if target=="Proxy":
        return "proxy_rate","proxy_6m_change_lag","proxy_change_6m"
    if target=="EFFR":
        return "effr","effr_6m_change_lag","effr_change_6m"
    raise ValueError(target)


def causal_standardize(train:pd.DataFrame,row:pd.Series)->tuple[pd.DataFrame,pd.Series,dict]:
    complete=train.dropna(subset=RAW_MACRO)
    if len(complete)<24:
        raise RuntimeError("insufficient training rows for macro standardization")
    means=complete[RAW_MACRO].mean()
    sds=complete[RAW_MACRO].std(ddof=0)
    if sds.isna().any() or (sds<=0).any():
        raise RuntimeError("zero/invalid macro training standard deviation")

    out=train.copy()
    r=row.copy()
    moments={}
    for raw in RAW_MACRO:
        z=ZMAP[raw]
        out[z]=(out[raw]-means[raw])/sds[raw]
        r[z]=(float(r[raw])-float(means[raw]))/float(sds[raw])
        moments[raw]={"mean":float(means[raw]),"std":float(sds[raw])}

    out["z_inflation_level_x_z_inflation_acceleration"]=out["z_inflation_level"]*out["z_inflation_acceleration"]
    out["z_growth_level_x_z_growth_acceleration"]=out["z_growth_level"]*out["z_growth_acceleration"]
    r["z_inflation_level_x_z_inflation_acceleration"]=r["z_inflation_level"]*r["z_inflation_acceleration"]
    r["z_growth_level_x_z_growth_acceleration"]=r["z_growth_level"]*r["z_growth_acceleration"]
    return out,r,moments


def features(target:str,model:str)->list[str]:
    stance,inertia,_=target_columns(target)
    base=[stance,inertia,"z_inflation_level","z_growth_level"]
    if model=="M1":
        return base
    linear=base+["z_inflation_acceleration","z_growth_acceleration"]
    if model=="M2":
        return linear
    if model=="M3":
        return linear+[
            "z_inflation_level_x_z_inflation_acceleration",
            "z_growth_level_x_z_growth_acceleration",
        ]
    raise ValueError(model)


def fit_predict(train:pd.DataFrame,row:pd.Series,target:str,model:str)->tuple[float,dict]:
    _,_,outcome=target_columns(target)
    fs=features(target,model)
    tr=train.dropna(subset=fs+[outcome]).copy()
    if len(tr)<24:
        raise RuntimeError("insufficient OLS training observations")
    X=np.column_stack([np.ones(len(tr)),tr[fs].to_numpy(float)])
    y=tr[outcome].to_numpy(float)
    beta=np.linalg.lstsq(X,y,rcond=None)[0]
    xr=np.array([1.0,*[float(row[c]) for c in fs]],dtype=float)
    names=["intercept",*fs]
    return float(xr@beta),{n:float(v) for n,v in zip(names,beta)}


def expanding_predictions(data:pd.DataFrame,target:str,p:dict)->tuple[pd.DataFrame,pd.DataFrame]:
    start=pd.Timestamp(p["exact_oos_sample"]["first_forecast_origin"]+"-01")
    end=pd.Timestamp(p["exact_oos_sample"]["last_forecast_origin"]+"-01")
    origins=data.loc[data["date"].between(start,end)].copy()
    _,_,outcome=target_columns(target)
    rows=[]; coefs=[]
    for _,row in origins.iterrows():
        required=RAW_MACRO+[target_columns(target)[0],target_columns(target)[1],outcome]
        if any(pd.isna(row[c]) for c in required):
            continue
        cutoff=row["date"]-pd.DateOffset(months=7)
        raw_train=data.loc[data["date"].le(cutoff)].copy()
        train,r,_=causal_standardize(raw_train,row)
        out={"date":row["date"],"target":target,"actual":float(row[outcome]),"actual_class":classify(float(row[outcome]))}
        for model in ("M1","M2","M3"):
            pred,coef=fit_predict(train,r,target,model)
            out[f"pred_{model}"]=pred
            out[f"class_{model}"]=classify(pred)
            coefs.append({"date":row["date"],"target":target,"model":model,**coef})
        rows.append(out)
    pred=pd.DataFrame(rows)
    if pred.empty:
        raise RuntimeError(f"no Issue #101 predictions for {target}")
    return pred,pd.DataFrame(coefs)


def metrics(pred:pd.DataFrame,model:str)->dict:
    y=pred["actual"].to_numpy(float); p=pred[f"pred_{model}"].to_numpy(float)
    err=p-y
    corr=float(np.corrcoef(y,p)[0,1]) if len(y)>=2 and np.std(y)>0 and np.std(p)>0 else None
    nonneutral=pred["actual_class"].ne("neutral")
    direction=float(pred.loc[nonneutral,f"class_{model}"].eq(pred.loc[nonneutral,"actual_class"]).mean()) if nonneutral.any() else None
    return {
        "n":int(len(pred)),
        "RMSE":float(np.sqrt(np.mean(err**2))),
        "MAE":float(np.mean(np.abs(err))),
        "correlation":corr,
        "balanced_accuracy":balanced_accuracy(pred["actual_class"],pred[f"class_{model}"]),
        "direction_accuracy_ex_neutral":direction,
    }


def summarize(pred:pd.DataFrame)->pd.DataFrame:
    target=str(pred["target"].iloc[0])
    rows=[]
    for model in ("M1","M2","M3"):
        rows.append({"target":target,"segment":"full","model":model,**metrics(pred,model)})
    tmp=pred.copy(); tmp["segment"]=tmp["date"].map(segment_label)
    for seg,g in tmp.groupby("segment",sort=False):
        for model in ("M1","M2","M3"):
            rows.append({"target":target,"segment":seg,"model":model,**metrics(g,model)})
    return pd.DataFrame(rows)


def incremental(summary:pd.DataFrame)->pd.DataFrame:
    rows=[]
    for (target,segment),g in summary.groupby(["target","segment"],sort=False):
        g=g.set_index("model")
        for comparison,base,new in [("M3_minus_M2","M2","M3"),("M3_minus_M1","M1","M3")]:
            rows.append({
              "target":target,"segment":segment,"comparison":comparison,
              "delta_RMSE":float(g.loc[new,"RMSE"]-g.loc[base,"RMSE"]),
              "delta_MAE":float(g.loc[new,"MAE"]-g.loc[base,"MAE"]),
              "delta_balanced_accuracy":float(g.loc[new,"balanced_accuracy"]-g.loc[base,"balanced_accuracy"]),
              "delta_direction_accuracy":float(g.loc[new,"direction_accuracy_ex_neutral"]-g.loc[base,"direction_accuracy_ex_neutral"]),
            })
    return pd.DataFrame(rows)


def leave_one_segment_out(pred:pd.DataFrame)->pd.DataFrame:
    target=str(pred["target"].iloc[0])
    tmp=pred.copy(); tmp["segment"]=tmp["date"].map(segment_label)
    rows=[]
    for omitted in ["Conventional_pre_Dec2008","Unconventional_post_Dec2008","Pandemic_and_postpandemic"]:
        g=tmp.loc[~tmp["segment"].eq(omitted)]
        m1=metrics(g,"M1"); m2=metrics(g,"M2"); m3=metrics(g,"M3")
        rows.append({
          "target":target,"omitted_segment":omitted,"n":len(g),
          "M3_minus_M2_RMSE":m3["RMSE"]-m2["RMSE"],
          "M3_minus_M2_MAE":m3["MAE"]-m2["MAE"],
          "M3_minus_M1_RMSE":m3["RMSE"]-m1["RMSE"],
          "M3_minus_M1_MAE":m3["MAE"]-m1["MAE"],
        })
    return pd.DataFrame(rows)


def interaction_coefficients(coefs:pd.DataFrame)->pd.DataFrame:
    rows=[]
    names=[
      "z_inflation_level_x_z_inflation_acceleration",
      "z_growth_level_x_z_growth_acceleration",
    ]
    for target in ("Proxy","EFFR"):
        g=coefs.loc[(coefs["target"].eq(target))&(coefs["model"].eq("M3"))]
        for name in names:
            vals=pd.to_numeric(g[name],errors="coerce").dropna()
            rows.append({
              "target":target,"coefficient":name,"n":len(vals),
              "median":float(vals.median()),
              "positive_fraction":float((vals>0).mean()),
            })
    return pd.DataFrame(rows)


def run(output_dir:Path)->dict:
    p=validate_prereg()
    p99,pf,p97,f97=validate_issue99_contracts()
    data=build_a1_frame(p99,p97,f97,pf)

    proxy,cp=expanding_predictions(data,"Proxy",p)
    effr,ce=expanding_predictions(data,"EFFR",p)
    if proxy["date"].tolist()!=effr["date"].tolist():
        raise RuntimeError("Proxy/EFFR OOS sample mismatch")
    if len(proxy)!=p["exact_oos_sample"]["forecast_origins_expected"]:
        raise RuntimeError("unexpected OOS forecast-origin count")

    summary=pd.concat([summarize(proxy),summarize(effr)],ignore_index=True)
    inc=incremental(summary)
    loeo=pd.concat([leave_one_segment_out(proxy),leave_one_segment_out(effr)],ignore_index=True)
    icoef=interaction_coefficients(pd.concat([cp,ce],ignore_index=True))

    output_dir.mkdir(parents=True,exist_ok=True)
    proxy.to_csv(output_dir/"issue-101-predictions-proxy.csv",index=False)
    effr.to_csv(output_dir/"issue-101-predictions-effr.csv",index=False)
    summary.to_csv(output_dir/"issue-101-summary.csv",index=False)
    inc.to_csv(output_dir/"issue-101-incremental.csv",index=False)
    loeo.to_csv(output_dir/"issue-101-leave-one-segment-out.csv",index=False)
    icoef.to_csv(output_dir/"issue-101-interaction-coefficients.csv",index=False)

    proxy_full=inc.loc[
      inc["target"].eq("Proxy")&inc["segment"].eq("full")
    ].set_index("comparison")
    manifest={
      "schema_version":1,
      "issue":101,
      "phase":"state-dependent-policy-reaction",
      "preregistration_preceded_outcomes":True,
      "treasury_outcomes_loaded":False,
      "portfolio_results_computed":False,
      "production_v66_modified":False,
      "durable_verdict_committed":DECISION.exists(),
      "oos":{
        "first_origin":proxy["date"].min().strftime("%Y-%m"),
        "last_origin":proxy["date"].max().strftime("%Y-%m"),
        "forecast_origins":len(proxy),
        "identical_proxy_effr_samples":True,
      },
      "proxy_primary_deltas":{
        "M3_minus_M2":proxy_full.loc["M3_minus_M2"].to_dict(),
        "M3_minus_M1":proxy_full.loc["M3_minus_M1"].to_dict(),
      },
      "output_files":{},
    }
    mp=output_dir/"issue-101-manifest.json"
    mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    manifest["output_files"]={
      f.name:{"sha256":hashlib.sha256(f.read_bytes()).hexdigest(),"bytes":f.stat().st_size}
      for f in sorted(output_dir.glob("*.csv"))
    }
    mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    return manifest


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    print(json.dumps(run(args.output_dir),indent=2,ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
