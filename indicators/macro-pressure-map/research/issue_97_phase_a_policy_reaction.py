#!/usr/bin/env python3
"""Issue #97 Phase A: preregistered Fed policy-reaction-function test."""
from __future__ import annotations
import argparse, hashlib, json, math, tempfile
from pathlib import Path
import numpy as np
import pandas as pd

from issue_91_phase1_hmra_v01 import (
    FED_IP_URL, fetch_bytes, fetch_bls_cpi_api, parse_fed_ip, canonical_monthly_payload
)
from issue_97_phase_a0_source_audit import EFFR_URL, parse_h15_effr

HERE=Path(__file__).resolve().parent
PREREG=HERE/"decisions"/"issue-97-phase-a-policy-reaction-preregistered.json"
FREEZE=HERE/"decisions"/"issue-97-phase-a0-source-freeze.json"
DECISION=HERE/"decisions"/"issue-97-phase-a-decision.json"

def load_json(path:Path)->dict:
    return json.loads(path.read_text(encoding="utf-8"))

def sha256_bytes(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def validate_contracts()->tuple[dict,dict]:
    p=load_json(PREREG); f=load_json(FREEZE)
    if not p["created_before_policy_model_outcomes"] or not p["created_before_treasury_outcomes"]:
        raise RuntimeError("pre-outcome timing guard failed")
    if p["production_v66_modified"] or p["hmra_modified"]:
        raise RuntimeError("research boundary drift")
    if f["policy_outcomes_seen"] or f["treasury_outcomes_seen"]:
        raise RuntimeError("source freeze timing guard failed")
    return p,f

def build_source_frame(p:dict,f:dict)->pd.DataFrame:
    ip_raw,_=fetch_bytes(FED_IP_URL)
    ip=parse_fed_ip(ip_raw)
    ip_canonical=canonical_monthly_payload(ip,"ip",2025)
    if sha256_bytes(ip_canonical)!=f["sources"]["industrial_production"]["canonical_used_through_2025_sha256"]:
        raise RuntimeError("IP canonical source drift")

    cpi,cpi_canonical,_=fetch_bls_cpi_api(start_year=1913,end_year=2025)
    if sha256_bytes(cpi_canonical)!=f["sources"]["cpi"]["canonical_1913_2025_sha256"]:
        raise RuntimeError("CPI canonical source drift")

    effr_raw,_=fetch_bytes(EFFR_URL)
    if sha256_bytes(effr_raw)!=f["sources"]["effective_federal_funds_rate"]["raw_sha256"]:
        raise RuntimeError("EFFR source drift")
    effr=parse_h15_effr(effr_raw)

    ip["date"]=pd.to_datetime(dict(year=ip.year,month=ip.month,day=1))
    cpi["date"]=pd.to_datetime(dict(year=cpi.year,month=cpi.month,day=1))
    effr=effr.rename(columns={"month":"date"})
    frame=ip[["date","ip"]].merge(cpi[["date","cpi"]],on="date",how="outer").merge(effr,on="date",how="outer")
    return frame.sort_values("date").reset_index(drop=True)

def build_features(frame:pd.DataFrame)->pd.DataFrame:
    x=frame.copy().set_index("date").sort_index()
    x["growth_level"]=100.0*np.log(x["ip"]/x["ip"].shift(12))
    x["growth_acceleration"]=x["growth_level"]-x["growth_level"].shift(6)
    x["inflation_level"]=100.0*np.log(x["cpi"]/x["cpi"].shift(12))
    x["inflation_acceleration"]=x["inflation_level"]-x["inflation_level"].shift(6)
    x["effr_6m_change_lag"]=x["effr"]-x["effr"].shift(6)
    x["policy_change_6m"]=x["effr"].shift(-6)-x["effr"]
    x["policy_change_12m"]=x["effr"].shift(-12)-x["effr"]

    # For decision month m, macro month k=m-2.
    for col in ["growth_level","growth_acceleration","inflation_level","inflation_acceleration"]:
        x[f"{col}_lag2"]=x[col].shift(2)
    return x.reset_index()

MODELS={
 "M0":["effr","effr_6m_change_lag","inflation_level_lag2"],
 "M1":["effr","effr_6m_change_lag","inflation_level_lag2","growth_level_lag2"],
 "M2":["effr","effr_6m_change_lag","inflation_level_lag2","growth_level_lag2","inflation_acceleration_lag2","growth_acceleration_lag2"],
}

def ols_fit_predict(train:pd.DataFrame,row:pd.Series,features:list[str],target:str)->tuple[float,dict]:
    cols=features+[target]
    tr=train.dropna(subset=cols).copy()
    if len(tr)<24:
        raise RuntimeError("insufficient OLS training observations")
    X=np.column_stack([np.ones(len(tr)),tr[features].to_numpy(float)])
    y=tr[target].to_numpy(float)
    beta=np.linalg.lstsq(X,y,rcond=None)[0]
    xr=np.array([1.0,*[float(row[c]) for c in features]],dtype=float)
    pred=float(xr@beta)
    names=["intercept",*features]
    return pred,{n:float(v) for n,v in zip(names,beta)}

def classify(v:float)->str:
    if v>0.25: return "tightening"
    if v<-0.25: return "easing"
    return "neutral"

def expanding_predictions(data:pd.DataFrame,target:str,rolling_months:int|None=None)->tuple[pd.DataFrame,pd.DataFrame]:
    latest=pd.Timestamp("2025-06-01") if target=="policy_change_6m" else pd.Timestamp("2024-12-01")
    origins=data.loc[data["date"].between("1970-01-01",latest)].copy()
    rows=[]; coef_rows=[]
    for _,r in origins.iterrows():
        required=set(sum(MODELS.values(),[])) | {target}
        if any(pd.isna(r[c]) for c in required):
            continue
        # outcome of a training origin must end before current forecast month.
        horizon=6 if target=="policy_change_6m" else 12
        cutoff=r["date"]-pd.DateOffset(months=horizon+1)
        train=data.loc[data["date"].le(cutoff)].copy()
        if rolling_months is not None:
            train=train.loc[train["date"].ge(cutoff-pd.DateOffset(months=rolling_months-1))]
        out={"date":r["date"],"actual":float(r[target]),"actual_class":classify(float(r[target]))}
        for model,features in MODELS.items():
            pred,coef=ols_fit_predict(train,r,features,target)
            out[f"pred_{model}"]=pred
            out[f"class_{model}"]=classify(pred)
            coef_rows.append({"date":r["date"],"target":target,"window":"expanding" if rolling_months is None else f"rolling_{rolling_months}","model":model,**coef})
        rows.append(out)
    return pd.DataFrame(rows),pd.DataFrame(coef_rows)

def balanced_accuracy(actual:pd.Series,pred:pd.Series)->float|None:
    classes=["tightening","neutral","easing"]; recalls=[]
    for c in classes:
        mask=actual.eq(c)
        if mask.any():
            recalls.append(float(pred.loc[mask].eq(c).mean()))
    return float(np.mean(recalls)) if recalls else None

def metrics(pred:pd.DataFrame,model:str)->dict:
    y=pred["actual"].to_numpy(float); p=pred[f"pred_{model}"].to_numpy(float)
    err=p-y
    corr=float(np.corrcoef(y,p)[0,1]) if len(y)>=2 and np.std(y)>0 and np.std(p)>0 else None
    nonneutral=pred["actual_class"].ne("neutral")
    signacc=float(pred.loc[nonneutral,f"class_{model}"].eq(pred.loc[nonneutral,"actual_class"]).mean()) if nonneutral.any() else None
    return {
      "n":int(len(pred)),
      "RMSE":float(np.sqrt(np.mean(err**2))),
      "MAE":float(np.mean(np.abs(err))),
      "correlation":corr,
      "balanced_accuracy":balanced_accuracy(pred["actual_class"],pred[f"class_{model}"]),
      "direction_accuracy_ex_neutral":signacc
    }

def era_label(d:pd.Timestamp)->str:
    y=d.year
    if y<=1984:return "Great_Inflation_Volcker"
    if y<=1999:return "Post_Volcker"
    if y<=2007:return "Pre_GFC"
    if y<=2019:return "GFC_QE"
    return "COVID_inflation_higher_rate"

def summarize(pred:pd.DataFrame,target:str,window:str)->pd.DataFrame:
    rows=[]
    for model in MODELS:
        rows.append({"target":target,"window":window,"segment":"full","model":model,**metrics(pred,model)})
    tmp=pred.copy(); tmp["era"]=tmp["date"].map(era_label)
    for era,g in tmp.groupby("era",sort=False):
        for model in MODELS:
            rows.append({"target":target,"window":window,"segment":era,"model":model,**metrics(g,model)})
    return pd.DataFrame(rows)

def incremental(summary:pd.DataFrame)->pd.DataFrame:
    rows=[]
    for (target,window,segment),g in summary.groupby(["target","window","segment"],sort=False):
        m1=g.loc[g.model.eq("M1")].iloc[0]; m2=g.loc[g.model.eq("M2")].iloc[0]
        rows.append({
          "target":target,"window":window,"segment":segment,
          "M2_minus_M1_RMSE":float(m2.RMSE-m1.RMSE),
          "M2_minus_M1_MAE":float(m2.MAE-m1.MAE),
          "M2_minus_M1_balanced_accuracy":float(m2.balanced_accuracy-m1.balanced_accuracy),
          "M2_minus_M1_direction_accuracy":float(m2.direction_accuracy_ex_neutral-m1.direction_accuracy_ex_neutral)
        })
    return pd.DataFrame(rows)

def leave_one_era_out(pred:pd.DataFrame,target:str)->pd.DataFrame:
    tmp=pred.copy(); tmp["era"]=tmp["date"].map(era_label)
    rows=[]
    for omitted in tmp["era"].drop_duplicates():
        g=tmp.loc[~tmp["era"].eq(omitted)]
        m1=metrics(g,"M1"); m2=metrics(g,"M2")
        rows.append({
          "target":target,"omitted_era":omitted,"n":len(g),
          "M2_minus_M1_RMSE":m2["RMSE"]-m1["RMSE"],
          "M2_minus_M1_MAE":m2["MAE"]-m1["MAE"],
          "M2_minus_M1_balanced_accuracy":m2["balanced_accuracy"]-m1["balanced_accuracy"],
          "M2_minus_M1_direction_accuracy":m2["direction_accuracy_ex_neutral"]-m1["direction_accuracy_ex_neutral"]
        })
    return pd.DataFrame(rows)

def coefficient_signs(coefs:pd.DataFrame)->pd.DataFrame:
    rows=[]
    focus=["inflation_level_lag2","growth_level_lag2","inflation_acceleration_lag2","growth_acceleration_lag2"]
    for (target,window,model),g in coefs.groupby(["target","window","model"]):
        for c in focus:
            if c not in g.columns: continue
            vals=pd.to_numeric(g[c],errors="coerce").dropna()
            if vals.empty: continue
            rows.append({"target":target,"window":window,"model":model,"coefficient":c,"n":len(vals),
                         "median":float(vals.median()),"positive_fraction":float((vals>0).mean())})
    return pd.DataFrame(rows)

def run(output_dir:Path)->dict:
    p,f=validate_contracts()
    data=build_features(build_source_frame(p,f))

    p6,c6=expanding_predictions(data,"policy_change_6m")
    p12,c12=expanding_predictions(data,"policy_change_12m")
    r6,rc6=expanding_predictions(data,"policy_change_6m",rolling_months=240)

    summary=pd.concat([
      summarize(p6,"policy_change_6m","expanding"),
      summarize(p12,"policy_change_12m","expanding"),
      summarize(r6,"policy_change_6m","rolling_240")
    ],ignore_index=True)
    inc=incremental(summary)
    loeo=leave_one_era_out(p6,"policy_change_6m")
    coefs=pd.concat([c6,c12,rc6],ignore_index=True)
    csign=coefficient_signs(coefs)

    output_dir.mkdir(parents=True,exist_ok=True)
    p6.to_csv(output_dir/"issue-97-phase-a-predictions-6m.csv",index=False)
    p12.to_csv(output_dir/"issue-97-phase-a-predictions-12m.csv",index=False)
    r6.to_csv(output_dir/"issue-97-phase-a-predictions-6m-rolling240.csv",index=False)
    summary.to_csv(output_dir/"issue-97-phase-a-summary.csv",index=False)
    inc.to_csv(output_dir/"issue-97-phase-a-incremental.csv",index=False)
    loeo.to_csv(output_dir/"issue-97-phase-a-leave-one-era-out.csv",index=False)
    csign.to_csv(output_dir/"issue-97-phase-a-coefficient-signs.csv",index=False)

    full=summary.loc[(summary.target=="policy_change_6m")&(summary.window=="expanding")&(summary.segment=="full")].set_index("model")
    primary_inc=inc.loc[(inc.target=="policy_change_6m")&(inc.window=="expanding")&(inc.segment=="full")].iloc[0]
    manifest={
      "schema_version":1,"issue":97,"phase":"A-policy-reaction-function",
      "preregistration_preceded_outcomes":True,"treasury_outcomes_loaded":False,"portfolio_results_computed":False,
      "production_v66_modified":False,"durable_phase_a_verdict_committed":DECISION.exists(),
      "oos":{"first_origin":p6.date.min().strftime("%Y-%m"),"last_origin":p6.date.max().strftime("%Y-%m"),"forecast_origins":len(p6)},
      "M0":full.loc["M0"].to_dict(),"M1":full.loc["M1"].to_dict(),"M2":full.loc["M2"].to_dict(),
      "primary_M2_minus_M1":primary_inc.to_dict(),
      "output_files":{}
    }
    mp=output_dir/"issue-97-phase-a-manifest.json"
    mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    manifest["output_files"]={x.name:{"sha256":hashlib.sha256(x.read_bytes()).hexdigest(),"bytes":x.stat().st_size} for x in sorted(output_dir.glob("*.csv"))}
    mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    return manifest

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args(); print(json.dumps(run(args.output_dir),indent=2,ensure_ascii=False)); return 0

if __name__=="__main__":
    raise SystemExit(main())
