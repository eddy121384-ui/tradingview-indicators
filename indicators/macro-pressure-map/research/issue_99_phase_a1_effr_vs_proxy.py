#!/usr/bin/env python3
"""Issue #99 A1: EFFR vs SF Fed Proxy Funds Rate policy-stance measurement test."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from issue_97_phase_a_policy_reaction import (
    build_source_frame,
    build_features,
    ols_fit_predict,
    classify,
    balanced_accuracy,
)
from issue_99_phase_a0_proxy_source_schema import (
    PAGE_URL,
    fetch as fetch_proxy,
    resolve_workbook_url,
    parse_monthly_proxy,
    canonical_proxy_payload,
    sha256_bytes,
)

HERE=Path(__file__).resolve().parent
PREREG=HERE/"decisions"/"issue-99-phase-a1-effr-vs-proxy-preregistered.json"
PROXY_FREEZE=HERE/"decisions"/"issue-99-phase-a0-proxy-source-freeze.json"
ISSUE97_PREREG=HERE/"decisions"/"issue-97-phase-a-policy-reaction-preregistered.json"
ISSUE97_FREEZE=HERE/"decisions"/"issue-97-phase-a0-source-freeze.json"
DECISION=HERE/"decisions"/"issue-99-phase-a1-decision.json"

MACRO_M1=["inflation_level_lag2","growth_level_lag2"]
MACRO_M2=MACRO_M1+["inflation_acceleration_lag2","growth_acceleration_lag2"]


def load_json(path:Path)->dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_contracts()->tuple[dict,dict,dict,dict]:
    p=load_json(PREREG)
    pf=load_json(PROXY_FREEZE)
    p97=load_json(ISSUE97_PREREG)
    f97=load_json(ISSUE97_FREEZE)
    if not p["created_before_A1_model_outcomes"] or not p["created_before_treasury_outcomes"]:
        raise RuntimeError("A1 prereg timing guard failed")
    if not pf["created_before_A1_model_outcomes"]:
        raise RuntimeError("proxy source freeze timing guard failed")
    if p["production_v66_modified"] or p["hmra_modified"]:
        raise RuntimeError("research boundary drift")
    if pf["model_outcomes_seen"] or pf["treasury_outcomes_seen"]:
        raise RuntimeError("proxy freeze outcome boundary drift")
    return p,pf,p97,f97


def fetch_proxy_frame(pf:dict)->pd.DataFrame:
    page,page_final,_=fetch_proxy(PAGE_URL)
    url=resolve_workbook_url(page,page_final)
    workbook,_,_=fetch_proxy(url)
    monthly=parse_monthly_proxy(workbook,"2025-12")
    canonical=canonical_proxy_payload(monthly)
    expected=pf["canonical_monthly_through_2025_12"]["canonical_sha256"]
    if sha256_bytes(canonical)!=expected:
        raise RuntimeError("Proxy Funds Rate canonical source drift")
    out=monthly.copy()
    out["date"]=out["date"].dt.to_period("M").dt.to_timestamp()
    return out[["date","proxy_rate","workbook_effr"]]


def build_a1_frame(p:dict,p97:dict,f97:dict,pf:dict)->pd.DataFrame:
    source=build_source_frame(p97,f97)
    base=build_features(source)
    proxy=fetch_proxy_frame(pf)
    x=base.merge(proxy,on="date",how="inner",validate="one_to_one").sort_values("date").reset_index(drop=True)

    x["proxy_6m_change_lag"]=x["proxy_rate"]-x["proxy_rate"].shift(6)
    x["proxy_change_6m"]=x["proxy_rate"].shift(-6)-x["proxy_rate"]
    # Issue #97 build_features already supplies:
    # effr_6m_change_lag and policy_change_6m.
    x=x.rename(columns={"policy_change_6m":"effr_change_6m"})

    start=pd.Timestamp(p["exact_common_sample"]["training_start"]+"-01")
    end=pd.Timestamp("2025-12-01")
    x=x.loc[x["date"].between(start,end)].copy()
    return x


def model_features(target:str,model:str)->list[str]:
    if target=="EFFR":
        controls=["effr","effr_6m_change_lag"]
    elif target=="Proxy":
        controls=["proxy_rate","proxy_6m_change_lag"]
    else:
        raise ValueError(target)
    if model=="M1":
        return controls+MACRO_M1
    if model=="M2":
        return controls+MACRO_M2
    raise ValueError(model)


def outcome_col(target:str)->str:
    return "effr_change_6m" if target=="EFFR" else "proxy_change_6m"


def expanding_predictions(data:pd.DataFrame,target:str,p:dict)->pd.DataFrame:
    start=pd.Timestamp(p["exact_common_sample"]["oos_first_forecast_origin"]+"-01")
    end=pd.Timestamp(p["exact_common_sample"]["oos_last_forecast_origin"]+"-01")
    origins=data.loc[data["date"].between(start,end)].copy()
    rows=[]
    for _,row in origins.iterrows():
        target_col=outcome_col(target)
        required=set(model_features(target,"M2"))|{target_col}
        if any(pd.isna(row[c]) for c in required):
            continue
        cutoff=row["date"]-pd.DateOffset(months=7)
        train=data.loc[data["date"].le(cutoff)].copy()
        out={
            "date":row["date"],
            "target":target,
            "actual":float(row[target_col]),
            "actual_class":classify(float(row[target_col])),
        }
        for model in ("M1","M2"):
            feats=model_features(target,model)
            pred,_=ols_fit_predict(train,row,feats,target_col)
            out[f"pred_{model}"]=pred
            out[f"class_{model}"]=classify(pred)
        rows.append(out)
    pred=pd.DataFrame(rows)
    if pred.empty:
        raise RuntimeError(f"no A1 predictions for {target}")
    return pred


def metrics(pred:pd.DataFrame,model:str)->dict:
    y=pred["actual"].to_numpy(float)
    p=pred[f"pred_{model}"].to_numpy(float)
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
        "direction_accuracy_ex_neutral":signacc,
    }


def segment_label(date:pd.Timestamp)->str:
    if date<=pd.Timestamp("2008-11-01"):
        return "Conventional_pre_Dec2008"
    if date<=pd.Timestamp("2019-12-01"):
        return "Unconventional_post_Dec2008"
    return "Pandemic_and_postpandemic"


def summarize(pred:pd.DataFrame)->pd.DataFrame:
    rows=[]
    target=str(pred["target"].iloc[0])
    for model in ("M1","M2"):
        rows.append({"target":target,"segment":"full","model":model,**metrics(pred,model)})
    tmp=pred.copy()
    tmp["segment"]=tmp["date"].map(segment_label)
    for seg,g in tmp.groupby("segment",sort=False):
        for model in ("M1","M2"):
            rows.append({"target":target,"segment":seg,"model":model,**metrics(g,model)})
    return pd.DataFrame(rows)


def incremental(summary:pd.DataFrame)->pd.DataFrame:
    rows=[]
    for (target,segment),g in summary.groupby(["target","segment"],sort=False):
        m1=g.loc[g["model"].eq("M1")].iloc[0]
        m2=g.loc[g["model"].eq("M2")].iloc[0]
        rows.append({
            "target":target,
            "segment":segment,
            "M2_minus_M1_RMSE":float(m2["RMSE"]-m1["RMSE"]),
            "M2_minus_M1_MAE":float(m2["MAE"]-m1["MAE"]),
            "M2_minus_M1_balanced_accuracy":float(m2["balanced_accuracy"]-m1["balanced_accuracy"]),
            "M2_minus_M1_direction_accuracy":float(m2["direction_accuracy_ex_neutral"]-m1["direction_accuracy_ex_neutral"]),
        })
    return pd.DataFrame(rows)


def leave_one_segment_out(pred:pd.DataFrame)->pd.DataFrame:
    target=str(pred["target"].iloc[0])
    tmp=pred.copy()
    tmp["segment"]=tmp["date"].map(segment_label)
    rows=[]
    for omitted in [
        "Conventional_pre_Dec2008",
        "Unconventional_post_Dec2008",
        "Pandemic_and_postpandemic",
    ]:
        g=tmp.loc[~tmp["segment"].eq(omitted)].copy()
        m1=metrics(g,"M1"); m2=metrics(g,"M2")
        rows.append({
            "target":target,
            "omitted_segment":omitted,
            "n":int(len(g)),
            "M2_minus_M1_RMSE":m2["RMSE"]-m1["RMSE"],
            "M2_minus_M1_MAE":m2["MAE"]-m1["MAE"],
            "M2_minus_M1_balanced_accuracy":m2["balanced_accuracy"]-m1["balanced_accuracy"],
            "M2_minus_M1_direction_accuracy":m2["direction_accuracy_ex_neutral"]-m1["direction_accuracy_ex_neutral"],
        })
    return pd.DataFrame(rows)


def target_divergence(frame:pd.DataFrame,p:dict)->pd.DataFrame:
    start=pd.Timestamp(p["exact_common_sample"]["oos_first_forecast_origin"]+"-01")
    end=pd.Timestamp(p["exact_common_sample"]["oos_last_forecast_origin"]+"-01")
    x=frame.loc[frame["date"].between(start,end),["date","effr","proxy_rate"]].dropna().copy()
    x["segment"]=x["date"].map(segment_label)
    rows=[]
    for seg,g in [("full",x),*list(x.groupby("segment",sort=False))]:
        rows.append({
            "segment":seg,
            "n":int(len(g)),
            "mean_proxy_minus_effr":float((g["proxy_rate"]-g["effr"]).mean()),
            "mean_abs_proxy_minus_effr":float((g["proxy_rate"]-g["effr"]).abs().mean()),
            "correlation":float(g["proxy_rate"].corr(g["effr"])),
        })
    return pd.DataFrame(rows)


def run(output_dir:Path)->dict:
    p,pf,p97,f97=validate_contracts()
    data=build_a1_frame(p,p97,f97,pf)

    effr=expanding_predictions(data,"EFFR",p)
    proxy=expanding_predictions(data,"Proxy",p)

    # Exact same OOS forecast origins are mandatory.
    if effr["date"].tolist()!=proxy["date"].tolist():
        raise RuntimeError("EFFR and Proxy prediction samples differ")

    summary=pd.concat([summarize(effr),summarize(proxy)],ignore_index=True)
    inc=incremental(summary)
    loeo=pd.concat([leave_one_segment_out(effr),leave_one_segment_out(proxy)],ignore_index=True)
    div=target_divergence(data,p)

    output_dir.mkdir(parents=True,exist_ok=True)
    effr.to_csv(output_dir/"issue-99-a1-predictions-effr.csv",index=False)
    proxy.to_csv(output_dir/"issue-99-a1-predictions-proxy.csv",index=False)
    summary.to_csv(output_dir/"issue-99-a1-summary.csv",index=False)
    inc.to_csv(output_dir/"issue-99-a1-incremental.csv",index=False)
    loeo.to_csv(output_dir/"issue-99-a1-leave-one-segment-out.csv",index=False)
    div.to_csv(output_dir/"issue-99-a1-target-divergence.csv",index=False)

    full=inc.loc[inc["segment"].eq("full")].set_index("target")
    post=inc.loc[inc["segment"].eq("Unconventional_post_Dec2008")].set_index("target")
    manifest={
        "schema_version":1,
        "issue":99,
        "phase":"A1-effr-vs-proxy-policy-stance",
        "preregistration_preceded_outcomes":True,
        "treasury_outcomes_loaded":False,
        "portfolio_results_computed":False,
        "production_v66_modified":False,
        "durable_A1_verdict_committed":DECISION.exists(),
        "oos":{
            "first_origin":effr["date"].min().strftime("%Y-%m"),
            "last_origin":effr["date"].max().strftime("%Y-%m"),
            "forecast_origins":int(len(effr)),
            "identical_target_samples":True,
        },
        "primary_full_M2_minus_M1":{
            "EFFR":full.loc["EFFR"].to_dict(),
            "Proxy":full.loc["Proxy"].to_dict(),
        },
        "post_Dec2008_M2_minus_M1":{
            "EFFR":post.loc["EFFR"].to_dict(),
            "Proxy":post.loc["Proxy"].to_dict(),
        },
        "output_files":{},
    }
    mp=output_dir/"issue-99-a1-manifest.json"
    mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    manifest["output_files"]={
        f.name:{"sha256":hashlib.sha256(f.read_bytes()).hexdigest(),"bytes":f.stat().st_size}
        for f in sorted(output_dir.glob("*.csv"))
    }
    mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    return manifest


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    print(json.dumps(run(args.output_dir),indent=2,ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
