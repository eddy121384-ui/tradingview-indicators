#!/usr/bin/env python3
"""Issue #95 Phase 3: preregistered absolute-inflation allocation overlay."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd

from issue_91_phase1_hmra_v01 import run as run_hmra
from issue_91_phase1_completion_validation import validate as validate_hmra_freeze
from issue_91_phase2_asset_validation import (
    DAMODARAN_URL,
    fetch_bytes,
    parse_damodaran_returns,
    sha256_bytes,
)

HERE=Path(__file__).resolve().parent
PREREG=HERE/"decisions"/"issue-95-phase3-inflation-overlay-preregistered.json"
PHASE2_PREREG=HERE/"decisions"/"issue-91-phase2-asset-validation-preregistered.json"
DECISION=HERE/"decisions"/"issue-95-phase3-decision.json"
ASSETS=["equity","treasury","cash","gold"]


def load_json(path:Path)->dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha_file(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_prereg()->dict:
    p=load_json(PREREG)
    if p["issue"]!=95 or p["phase"]!="3-inflation-conditioned-allocation-overlay-preregistration":
        raise RuntimeError("bad Issue #95 prereg identity")
    if p["created_before_phase3_portfolio_outcomes"] is not True:
        raise RuntimeError("Phase 3 prereg timing guard failed")
    if p["production_v66_modified"] or p["hmra_modified"] or p["base_policy_modified"]:
        raise RuntimeError("frozen research boundary violated")
    primary=p["sensitivity_discipline"]["primary"]
    if primary!={"inflation_threshold_pct":4.0,"treasury_redirect_fraction":0.5,"cost_bps":5.0}:
        raise RuntimeError("primary overlay parameters drifted")
    return p


def era_for_year(year:int,p:dict)->str:
    for e in p["temporal_validation"]["return_year_eras"]:
        if e["start"]<=year<=e["end"]:
            return e["label"]
    return "outside"


def base_weights(growth:str,inflation:str,p:dict)->np.ndarray:
    key=f"growth_{growth}|inflation_{inflation}"
    raw=p["base_policy"]["matrix"].get(key)
    if raw is None:
        raise RuntimeError(f"unmapped HMRA cell: {key}")
    e,t,g=map(float,raw)
    return np.array([e,t,0.0,g],dtype=float)


def overlay_weights(base:np.ndarray,active:bool,redirect:float)->np.ndarray:
    w=base.copy()
    if active:
        moved=w[1]*redirect
        w[1]-=moved
        w[2]+=moved
    if not np.isclose(w.sum(),1.0,atol=1e-12):
        raise RuntimeError("overlay weights do not sum to one")
    return w


def build_eval_frame(states:pd.DataFrame,assets:pd.DataFrame,p:dict)->pd.DataFrame:
    s=states.loc[
        states["year"].between(p["sample_and_timing"]["state_year_start"],p["sample_and_timing"]["state_year_end"])
        & states["core_regime"].ne("n/a")
    ].copy()
    s=s.rename(columns={"year":"state_year"})
    s["return_year"]=s["state_year"]+2
    a=assets.rename(columns={"year":"return_year"})
    f=s.merge(a,on="return_year",how="inner",validate="one_to_one")
    f=f.loc[f["return_year"].between(1975,2025)].sort_values("return_year").reset_index(drop=True)
    if f["return_year"].tolist()!=list(range(1975,2026)):
        raise RuntimeError("primary return years are not exactly 1975-2025")
    f["era"]=[era_for_year(int(y),p) for y in f["return_year"]]
    f["overlay_active"]=f["inflation_rate"].ge(4.0)
    return f


def targets_for_frame(frame:pd.DataFrame,p:dict,redirect:float)->tuple[pd.DataFrame,pd.DataFrame]:
    base_rows=[]
    overlay_rows=[]
    for r in frame.itertuples(index=False):
        b=base_weights(r.growth_state,r.inflation_state,p)
        o=overlay_weights(b,bool(r.overlay_active),redirect)
        base_rows.append(b); overlay_rows.append(o)
    idx=pd.Index(frame["return_year"].astype(int),name="return_year")
    return (
        pd.DataFrame(base_rows,index=idx,columns=ASSETS),
        pd.DataFrame(overlay_rows,index=idx,columns=ASSETS),
    )


def fixed_targets(years:pd.Index,weights:list[float])->pd.DataFrame:
    arr=np.tile(np.asarray(weights,dtype=float),(len(years),1))
    return pd.DataFrame(arr,index=years,columns=ASSETS)


def inverse_vol_targets(assets:pd.DataFrame,p:dict)->pd.DataFrame:
    c=p["required_strategies_and_controls"]["causal_inverse_vol"]
    lookback=int(c["lookback_completed_years"])
    start=int(c["evaluation_return_year_start"]); end=int(c["evaluation_return_year_end"])
    a=assets.set_index("year").sort_index()
    rows=[]; years=[]
    for year in range(start,end+1):
        hist=a.loc[year-lookback:year-1,["equity","treasury","gold"]]
        if len(hist)!=lookback:
            raise RuntimeError(f"inverse-vol missing history for {year}")
        vol=hist.std(ddof=1)
        if (vol<=0).any() or vol.isna().any():
            raise RuntimeError(f"inverse-vol invalid volatility for {year}")
        inv=1.0/vol
        w=inv/inv.sum()
        rows.append([float(w["equity"]),float(w["treasury"]),0.0,float(w["gold"])])
        years.append(year)
    return pd.DataFrame(rows,index=pd.Index(years,name="return_year"),columns=ASSETS)


def simulate(frame:pd.DataFrame,targets:pd.DataFrame,cost_bps:float,name:str)->pd.DataFrame:
    market=frame.set_index("return_year")[ASSETS].reindex(targets.index)
    if market.isna().any(axis=None):
        raise RuntimeError(f"market return missing for {name}")
    rows=[]; prev_end=None; wealth=1.0
    for pos,year in enumerate(targets.index):
        target=targets.loc[year,ASSETS].to_numpy(float)
        r=market.loc[year,ASSETS].to_numpy(float)
        if not np.isclose(target.sum(),1.0,atol=1e-10):
            raise RuntimeError(f"target weights invalid {name} {year}")
        turnover=0.0
        if pos==0:
            invested=target.copy()
        else:
            invested=prev_end.copy()
            turnover=float(0.5*np.abs(target-invested).sum())
            invested=target.copy()
        cost=float(turnover*cost_bps/10000.0)
        gross=float(np.dot(invested,r))
        net=(1.0-cost)*(1.0+gross)-1.0
        wealth*=1.0+net
        prev_end=invested*(1.0+r)/(1.0+gross)
        row={
            "return_year":int(year),"strategy":name,"net_return":net,"gross_return":gross,
            "cash_return":float(r[2]),"wealth":wealth,"turnover":turnover,"cost_fraction":cost,
        }
        for asset,w in zip(ASSETS,invested):
            row[f"invested_weight_{asset}"]=float(w)
        for asset,w in zip(ASSETS,prev_end):
            row[f"end_weight_{asset}"]=float(w)
        rows.append(row)
    return pd.DataFrame(rows).set_index("return_year")


def portfolio_metrics(sim:pd.DataFrame)->dict:
    r=sim["net_return"].to_numpy(float); n=len(r)
    if n==0: raise RuntimeError("empty simulation")
    ending=float(np.prod(1.0+r))
    cagr=float(ending**(1.0/n)-1.0)
    arithmetic=float(np.mean(r))
    vol=float(np.std(r,ddof=1)) if n>1 else float("nan")
    excess=r-sim["cash_return"].to_numpy(float)
    exvol=float(np.std(excess,ddof=1)) if n>1 else float("nan")
    sharpe=float(np.mean(excess)/exvol) if exvol>0 else float("nan")
    wealth=np.concatenate(([1.0],np.cumprod(1.0+r)))
    dd=wealth/np.maximum.accumulate(wealth)-1.0
    maxdd=float(np.min(dd))
    calmar=float(cagr/abs(maxdd)) if maxdd<0 else float("nan")
    neg=r[r<0]
    out={
        "observations":n,"CAGR":cagr,"arithmetic_annual_return":arithmetic,
        "annualized_volatility":vol,"Sharpe_using_TBill":sharpe,"maximum_drawdown":maxdd,
        "Calmar":calmar,"worst_calendar_year_return":float(np.min(r)),
        "mean_return_in_negative_portfolio_years":float(np.mean(neg)) if len(neg) else None,
        "annualized_turnover":float(sim["turnover"].sum()/n),
        "total_turnover":float(sim["turnover"].sum()),
        "rebalance_count":int((sim["turnover"]>0).sum()),
        "cumulative_estimated_cost_drag":float(1.0-np.prod(1.0-sim["cost_fraction"].to_numpy(float))),
        "ending_wealth":ending,
    }
    for asset in ASSETS:
        out[f"average_weight_{asset}"]=float(sim[f"invested_weight_{asset}"].mean())
    return out


def matched_static_targets(primary_sim:pd.DataFrame)->pd.DataFrame:
    weights=np.array([primary_sim[f"invested_weight_{a}"].mean() for a in ASSETS],dtype=float)
    weights=weights/weights.sum()
    return fixed_targets(primary_sim.index,weights.tolist())


def exposure_mismatch(a:pd.DataFrame,b:pd.DataFrame)->float:
    aw=np.array([a[f"invested_weight_{x}"].mean() for x in ASSETS])
    bw=np.array([b[f"invested_weight_{x}"].mean() for x in ASSETS])
    return float(np.max(np.abs(aw-bw)))


def simulate_primary_set(frame:pd.DataFrame,p:dict,cost:float,redirect:float)->tuple[dict[str,pd.DataFrame],dict]:
    base_t,over_t=targets_for_frame(frame,p,redirect)
    years=base_t.index
    targets={
        "inflation_overlay_50":over_t,
        "base_issue89_policy":base_t,
        "fixed_60_40":fixed_targets(years,[.60,.40,0,0]),
        "fixed_40_40_20":fixed_targets(years,[.40,.40,0,.20]),
        "equal_weight_3asset":fixed_targets(years,[1/3,1/3,0,1/3]),
    }
    sims={name:simulate(frame,t,cost,name) for name,t in targets.items()}
    matched_t=matched_static_targets(sims["inflation_overlay_50"])
    sims["matched_static_4asset"]=simulate(frame,matched_t,cost,"matched_static_4asset")
    mismatch=exposure_mismatch(sims["inflation_overlay_50"],sims["matched_static_4asset"])
    tol=float(p["required_strategies_and_controls"]["realized_exposure_matched_static_control"]["fail_closed_tolerance"])
    if mismatch>tol:
        raise RuntimeError(f"matched-static exposure mismatch {mismatch} > {tol}")
    inv_t=inverse_vol_targets(
        frame[["return_year",*ASSETS]].rename(columns={"return_year":"year"}),
        p,
    )
    inv_frame=frame.loc[frame["return_year"].isin(inv_t.index)].copy()
    sims["causal_inverse_vol_3asset"]=simulate(inv_frame,inv_t,cost,"causal_inverse_vol_3asset")
    return sims,{"matched_static_max_abs_exposure_mismatch":mismatch}


def summarize(sims:dict[str,pd.DataFrame])->pd.DataFrame:
    rows=[]
    for name,sim in sims.items():
        rows.append({"strategy":name,"segment":"full",**portfolio_metrics(sim)})
    return pd.DataFrame(rows)


def active_table(frame:pd.DataFrame,overlay:pd.DataFrame,base:pd.DataFrame,matched:pd.DataFrame)->pd.DataFrame:
    years=overlay.index
    meta=frame.set_index("return_year").loc[years,["state_year","growth_state","inflation_state","core_regime","inflation_rate","overlay_active","era"]].copy()
    out=meta.copy()
    out["overlay_return"]=overlay["net_return"]
    out["base_return"]=base["net_return"]
    out["matched_return"]=matched["net_return"]
    out["overlay_minus_base_log"]=np.log1p(out["overlay_return"])-np.log1p(out["base_return"])
    out["overlay_minus_matched_log"]=np.log1p(out["overlay_return"])-np.log1p(out["matched_return"])
    return out.reset_index()


def grouped_active(active:pd.DataFrame)->pd.DataFrame:
    rows=[]
    specs=[
        ("era",["era"]),
        ("hmra_cell",["growth_state","inflation_state","core_regime"]),
        ("inflation_background",["overlay_active"]),
    ]
    for group_type,cols in specs:
        for keys,g in active.groupby(cols,dropna=False,sort=True):
            if not isinstance(keys,tuple): keys=(keys,)
            row={"group_type":group_type,"years":int(len(g))}
            for c,v in zip(cols,keys): row[c]=v
            row["overlay_minus_base_active_log"]=float(g["overlay_minus_base_log"].sum())
            row["overlay_minus_matched_active_log"]=float(g["overlay_minus_matched_log"].sum())
            rows.append(row)
    return pd.DataFrame(rows)


def era_metrics(sims:dict[str,pd.DataFrame],p:dict)->pd.DataFrame:
    rows=[]
    for e in p["temporal_validation"]["return_year_eras"]:
        for name,sim in sims.items():
            sub=sim.loc[(sim.index>=e["start"])&(sim.index<=e["end"])]
            if sub.empty: continue
            rows.append({"era":e["label"],"strategy":name,"first_year":int(sub.index.min()),"last_year":int(sub.index.max()),**portfolio_metrics(sub)})
    return pd.DataFrame(rows)


def rerun_subset(frame:pd.DataFrame,p:dict,cost:float,redirect:float)->tuple[dict[str,pd.DataFrame],dict]:
    # Compressed jackknife sample per prereg.
    return simulate_primary_set(frame.reset_index(drop=True),p,cost,redirect)


def leave_one_era_out(frame:pd.DataFrame,p:dict,cost:float,redirect:float)->pd.DataFrame:
    rows=[]
    for e in p["temporal_validation"]["return_year_eras"]:
        sub=frame.loc[~frame["return_year"].between(e["start"],e["end"])].copy()
        sims,diag=rerun_subset(sub,p,cost,redirect)
        om=portfolio_metrics(sims["inflation_overlay_50"]); bm=portfolio_metrics(sims["base_issue89_policy"]); mm=portfolio_metrics(sims["matched_static_4asset"])
        active=active_table(sub,sims["inflation_overlay_50"],sims["base_issue89_policy"],sims["matched_static_4asset"])
        rows.append({
            "omitted_era":e["label"],"remaining_years":len(sub),
            "overlay_CAGR":om["CAGR"],"base_CAGR":bm["CAGR"],"matched_CAGR":mm["CAGR"],
            "delta_CAGR_vs_base":om["CAGR"]-bm["CAGR"],"delta_CAGR_vs_matched":om["CAGR"]-mm["CAGR"],
            "delta_Sharpe_vs_base":om["Sharpe_using_TBill"]-bm["Sharpe_using_TBill"],
            "delta_Sharpe_vs_matched":om["Sharpe_using_TBill"]-mm["Sharpe_using_TBill"],
            "delta_maxDD_vs_base":om["maximum_drawdown"]-bm["maximum_drawdown"],
            "delta_maxDD_vs_matched":om["maximum_drawdown"]-mm["maximum_drawdown"],
            "active_log_vs_base":float(active["overlay_minus_base_log"].sum()),
            "active_log_vs_matched":float(active["overlay_minus_matched_log"].sum()),
            **diag,
        })
    return pd.DataFrame(rows)


def episodes(active:pd.DataFrame)->pd.DataFrame:
    a=active.loc[active["overlay_active"]].sort_values("return_year").copy()
    if a.empty: return pd.DataFrame()
    rows=[]; current=[]; prev=None
    for row in a.itertuples(index=False):
        y=int(row.return_year)
        if prev is None or y==prev+1:
            current.append(row)
        else:
            rows.append(current); current=[row]
        prev=y
    if current: rows.append(current)
    out=[]
    for idx,ep in enumerate(rows,1):
        db=float(sum(r.overlay_minus_base_log for r in ep))
        dm=float(sum(r.overlay_minus_matched_log for r in ep))
        out.append({
            "episode_id":idx,"start_return_year":int(ep[0].return_year),"end_return_year":int(ep[-1].return_year),
            "episode_years":len(ep),"overlay_minus_base_active_log":db,
            "overlay_minus_matched_active_log":dm,
            "positive_or_negative":"positive" if db>0 else "negative" if db<0 else "zero",
        })
    return pd.DataFrame(out)


def episode_concentration(ep:pd.DataFrame)->dict:
    if ep.empty:
        return {"positive_episode_count":0,"top1_share_positive":None,"top3_share_positive":None}
    pos=ep.loc[ep["overlay_minus_base_active_log"]>0,"overlay_minus_base_active_log"].sort_values(ascending=False)
    total=float(pos.sum())
    return {
        "positive_episode_count":int(len(pos)),
        "top1_share_positive":float(pos.iloc[:1].sum()/total) if total>0 else None,
        "top3_share_positive":float(pos.iloc[:3].sum()/total) if total>0 else None,
    }


def largest_episode_leaveout(frame:pd.DataFrame,p:dict,cost:float,redirect:float,ep:pd.DataFrame)->dict:
    pos=ep.loc[ep["overlay_minus_base_active_log"]>0].sort_values("overlay_minus_base_active_log",ascending=False)
    if pos.empty: return {"performed":False}
    top=pos.iloc[0]
    sub=frame.loc[~frame["return_year"].between(int(top["start_return_year"]),int(top["end_return_year"]))].copy()
    sims,diag=rerun_subset(sub,p,cost,redirect)
    om=portfolio_metrics(sims["inflation_overlay_50"]); bm=portfolio_metrics(sims["base_issue89_policy"]); mm=portfolio_metrics(sims["matched_static_4asset"])
    active=active_table(sub,sims["inflation_overlay_50"],sims["base_issue89_policy"],sims["matched_static_4asset"])
    return {
        "performed":True,"omitted_start":int(top["start_return_year"]),"omitted_end":int(top["end_return_year"]),
        "remaining_years":len(sub),"delta_CAGR_vs_base":om["CAGR"]-bm["CAGR"],
        "delta_CAGR_vs_matched":om["CAGR"]-mm["CAGR"],
        "delta_Sharpe_vs_base":om["Sharpe_using_TBill"]-bm["Sharpe_using_TBill"],
        "delta_Sharpe_vs_matched":om["Sharpe_using_TBill"]-mm["Sharpe_using_TBill"],
        "active_log_vs_base":float(active["overlay_minus_base_log"].sum()),
        "active_log_vs_matched":float(active["overlay_minus_matched_log"].sum()),
        **diag,
    }


def sensitivities(frame:pd.DataFrame,p:dict)->pd.DataFrame:
    rows=[]
    for redirect in [0.25,0.50,0.75]:
        for cost in [0.0,5.0,10.0]:
            sims,diag=simulate_primary_set(frame,p,cost,redirect)
            om=portfolio_metrics(sims["inflation_overlay_50"]); bm=portfolio_metrics(sims["base_issue89_policy"]); mm=portfolio_metrics(sims["matched_static_4asset"])
            rows.append({
                "redirect_fraction":redirect,"cost_bps":cost,
                "is_primary":redirect==0.50 and cost==5.0,
                "overlay_CAGR":om["CAGR"],"base_CAGR":bm["CAGR"],"matched_CAGR":mm["CAGR"],
                "delta_CAGR_vs_base":om["CAGR"]-bm["CAGR"],"delta_CAGR_vs_matched":om["CAGR"]-mm["CAGR"],
                "delta_Sharpe_vs_base":om["Sharpe_using_TBill"]-bm["Sharpe_using_TBill"],
                "delta_Sharpe_vs_matched":om["Sharpe_using_TBill"]-mm["Sharpe_using_TBill"],
                "delta_maxDD_vs_base":om["maximum_drawdown"]-bm["maximum_drawdown"],
                "delta_maxDD_vs_matched":om["maximum_drawdown"]-mm["maximum_drawdown"],
                **diag,
            })
    return pd.DataFrame(rows)


def asset_contribution(frame:pd.DataFrame,sims:dict[str,pd.DataFrame])->pd.DataFrame:
    market=frame.set_index("return_year")[ASSETS]
    rows=[]
    for name,sim in sims.items():
        common=sim.index.intersection(market.index)
        for asset in ASSETS:
            contrib=sim.loc[common,f"invested_weight_{asset}"]*market.loc[common,asset]
            rows.append({"strategy":name,"asset":asset,"years":len(common),"mean_annual_gross_contribution":float(contrib.mean()),"cumulative_arithmetic_contribution":float(contrib.sum())})
    return pd.DataFrame(rows)


def run(output_dir:Path)->dict:
    p=validate_prereg()
    phase2=load_json(PHASE2_PREREG)
    with tempfile.TemporaryDirectory(prefix="issue95-hmra-") as td:
        d=Path(td); run_hmra(d); hmra_check=validate_hmra_freeze(d)
        states=pd.read_csv(d/"issue-91-hmra-v0.1-macro-states.csv")
    raw,final_url=fetch_bytes(DAMODARAN_URL)
    if sha256_bytes(raw)!=p["primary_underlying_asset_source"]["frozen_raw_sha256"]:
        raise RuntimeError("Damodaran source SHA drift")
    assets=parse_damodaran_returns(raw,phase2)
    frame=build_eval_frame(states,assets,p)

    cost=float(p["sensitivity_discipline"]["primary"]["cost_bps"])
    redirect=float(p["sensitivity_discipline"]["primary"]["treasury_redirect_fraction"])
    sims,diag=simulate_primary_set(frame,p,cost,redirect)
    summary=summarize(sims)
    era=era_metrics(sims,p)
    active=active_table(frame,sims["inflation_overlay_50"],sims["base_issue89_policy"],sims["matched_static_4asset"])
    grouped=grouped_active(active)
    loeo=leave_one_era_out(frame,p,cost,redirect)
    ep=episodes(active)
    ep_conc=episode_concentration(ep)
    ep_leaveout=largest_episode_leaveout(frame,p,cost,redirect,ep)
    sens=sensitivities(frame,p)
    contrib=asset_contribution(frame,sims)

    output_dir.mkdir(parents=True,exist_ok=True)
    summary.to_csv(output_dir/"issue-95-summary.csv",index=False)
    era.to_csv(output_dir/"issue-95-era-summary.csv",index=False)
    active.to_csv(output_dir/"issue-95-active-year.csv",index=False)
    grouped.to_csv(output_dir/"issue-95-active-attribution.csv",index=False)
    loeo.to_csv(output_dir/"issue-95-leave-one-era-out.csv",index=False)
    ep.to_csv(output_dir/"issue-95-active-episodes.csv",index=False)
    sens.to_csv(output_dir/"issue-95-sensitivity.csv",index=False)
    contrib.to_csv(output_dir/"issue-95-asset-contribution.csv",index=False)

    om=summary.loc[summary["strategy"].eq("inflation_overlay_50")].iloc[0]
    bm=summary.loc[summary["strategy"].eq("base_issue89_policy")].iloc[0]
    mm=summary.loc[summary["strategy"].eq("matched_static_4asset")].iloc[0]
    high_years=int(frame["overlay_active"].sum())
    high_early=int(frame.loc[frame["return_year"].between(1975,1984),"overlay_active"].sum())
    high_recent=int(frame.loc[frame["return_year"].between(2020,2025),"overlay_active"].sum())
    manifest={
        "schema_version":1,"issue":95,"phase":"3-inflation-conditioned-allocation-overlay",
        "preregistration_preceded_outcomes":True,"hmra_freeze_validated":bool(hmra_check["validated"]),
        "production_v66_modified":False,"hmra_modified":False,"base_policy_modified":False,"etfs_used":False,
        "portfolio_policy_evaluated":True,"durable_verdict_committed":DECISION.exists(),
        "source":{"url":final_url,"raw_sha256":sha256_bytes(raw)},
        "sample":{"first_return_year":int(frame["return_year"].min()),"last_return_year":int(frame["return_year"].max()),"years":len(frame),"overlay_active_years":high_years,"active_1975_1984":high_early,"active_2020_2025":high_recent},
        "primary":{"threshold_pct":4.0,"redirect_fraction":redirect,"cost_bps":cost},
        "matched_static_max_abs_exposure_mismatch":diag["matched_static_max_abs_exposure_mismatch"],
        "primary_deltas":{
            "CAGR_vs_base":float(om["CAGR"]-bm["CAGR"]),
            "CAGR_vs_matched":float(om["CAGR"]-mm["CAGR"]),
            "Sharpe_vs_base":float(om["Sharpe_using_TBill"]-bm["Sharpe_using_TBill"]),
            "Sharpe_vs_matched":float(om["Sharpe_using_TBill"]-mm["Sharpe_using_TBill"]),
            "maxDD_vs_base":float(om["maximum_drawdown"]-bm["maximum_drawdown"]),
            "maxDD_vs_matched":float(om["maximum_drawdown"]-mm["maximum_drawdown"]),
            "Calmar_vs_base":float(om["Calmar"]-bm["Calmar"]),
            "Calmar_vs_matched":float(om["Calmar"]-mm["Calmar"]),
            "active_log_vs_base":float(active["overlay_minus_base_log"].sum()),
            "active_log_vs_matched":float(active["overlay_minus_matched_log"].sum()),
        },
        "episode_concentration":ep_conc,
        "largest_positive_episode_leaveout":ep_leaveout,
        "output_files":{},
    }
    manifest_path=output_dir/"issue-95-manifest.json"
    manifest_path.write_text(json.dumps(manifest,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    manifest["output_files"]={
        path.name:{"sha256":sha_file(path),"bytes":path.stat().st_size}
        for path in sorted(output_dir.glob("*.csv"))
    }
    manifest_path.write_text(json.dumps(manifest,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    return manifest


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    print(json.dumps(run(args.output_dir),indent=2,ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
