#!/usr/bin/env python3
"""Issue #68 B3.16 counterfactual stale-range release audit. Diagnostic only."""
from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path
from typing import Any
import numpy as np, pandas as pd
import diagnose_issue66_reciprocal_symmetry as phasea
import diagnose_issue68_phase_b38_raw_feature_attribution as b38
import diagnose_issue68_phase_b310_s5_vs_s2_local_duel as b310
import diagnose_issue68_phase_b314_break_evidence_memory as b314
import diagnose_issue68_phase_b315_event_window_stale_memory as b315

GATE=0.99
TOL=1e-9
BREAK_ID=list(b310.COMPONENTS).index("break")
W=float(b38.COMPONENT_WEIGHTS["break"])

def sign(x: float, tol: float=1e-12)->str:
    return "nan" if not np.isfinite(x) else "target" if x>tol else "old" if x<-tol else "neutral"

def score(mode, r, m):
    return np.where(np.asarray(mode,bool),100.0,np.maximum(np.nan_to_num(r,nan=0.0),np.nan_to_num(m,nan=0.0)))

def arrays(model: pd.DataFrame, direction:int, warmup:int)->dict[str,Any]:
    fresh=b38.fresh_pair_components(model); a=fresh["arrays"]
    duel=b310.direction_duel_from_arrays(a,direction,warmup)
    events=np.flatnonzero(duel["_arrays"]["handoff"] & (duel["_arrays"]["final_blocker_id"]==BREAK_ID))
    sides=b314.side_arrays(model,direction)
    logp=b314.f(model,"b314_log_price"); ma=b314.f(model,"b314_ma_log")
    ma_target=logp>ma if direction==1 else logp<ma
    old_mem=np.isfinite(sides["old"]["recent_range"]) & (sides["old"]["recent_range"]>0)
    new_range=np.isfinite(sides["target"]["range"]) & (sides["target"]["range"]>0)
    overlap=ma_target & old_mem
    ts=score(sides["target"]["mode"],sides["target"]["range"],sides["target"]["ma"])
    os=score(sides["old"]["mode"],sides["old"]["range"],sides["old"]["ma"])
    shadow_r=np.asarray(sides["old"]["range"],float).copy(); shadow_r[overlap]=0.0
    sos=score(sides["old"]["mode"],shadow_r,sides["old"]["ma"])
    obs_b=direction*np.asarray(a["break"],float); rec_b=W*(ts-os); sh_b=W*(ts-sos)
    obs_d=direction*np.asarray(a["direct"],float)
    comps={k:direction*np.asarray(a[k],float) for k in b310.COMPONENTS}
    obs_sum=np.sum(np.column_stack([comps[k] for k in b310.COMPONENTS]),axis=1)
    sh_d=obs_d-obs_b+sh_b; comps["break"]=sh_b
    sh_sum=np.sum(np.column_stack([comps[k] for k in b310.COMPONENTS]),axis=1)
    def err(x,y):
        ok=np.isfinite(x)&np.isfinite(y)
        return float(np.max(np.abs(x[ok]-y[ok]))) if np.any(ok) else 0.0
    primary=[int(t) for t in events if ma_target[t-1] and old_mem[t-1]]
    return dict(events=events,primary=primary,ma_target=ma_target,old_mem=old_mem,new_range=new_range,
                overlap=overlap,obs_b=obs_b,sh_b=sh_b,obs_d=obs_d,sh_d=sh_d,
                break_err=err(obs_b,rec_b),obs_err=err(obs_d,obs_sum),shadow_err=err(sh_d,sh_sum))

def audit(model:pd.DataFrame,direction:int,warmup:int)->dict[str,Any]:
    x=arrays(model,direction,warmup); base=b315.audit_direction(model,direction,warmup)
    expected_primary=sum(r["population"]=="MA_TARGET_AT_BLOCKER" for r in base["_events"])
    rows=[]; ov_sign=Counter(); ov_obs_old=0; nr_release=0; ov_n=0
    for t in x["primary"]:
        p=t-1; flip,pop=b315.find_event_ma_flip(t,x["ma_target"],x["obs_d"],warmup)
        assert pop=="MA_TARGET_AT_BLOCKER" and flip is not None
        first=next((i for i in range(flip,p+1) if np.isfinite(x["sh_d"][i]) and x["sh_d"][i]>0),None)
        lead=None if first is None else int(t-first)
        idx=np.arange(flip,p+1); oi=idx[x["overlap"][flip:p+1]]; ov_n+=len(oi)
        for i in oi:
            old=np.isfinite(x["obs_b"][i]) and x["obs_b"][i]<0
            ov_obs_old+=int(old); s=sign(float(x["sh_b"][i])); ov_sign[s]+=1
            nr_release+=int(old and s=="target" and x["new_range"][i])
        rows.append(dict(index=int(t),blocker_index=int(p),ma_flip=int(flip),
            observed_break_sign=sign(float(x["obs_b"][p])),shadow_break_sign=sign(float(x["sh_b"][p])),
            observed_total_sign=sign(float(x["obs_d"][p])),shadow_total_sign=sign(float(x["sh_d"][p])),
            shadow_break_positive=bool(x["sh_b"][p]>0),shadow_total_positive=bool(x["sh_d"][p]>0),
            shadow_total_lead_bars=lead,new_range_at_blocker=bool(x["new_range"][p])))
    br=Counter(r["shadow_break_sign"] for r in rows); tr=Counter(r["shadow_total_sign"] for r in rows)
    leads=[r["shadow_total_lead_bars"] for r in rows if r["shadow_total_lead_bars"] is not None]
    return dict(direction="bull" if direction==1 else "bear",
        break_events=len(x["events"]),expected_break_events=base["break_final_blocker_events"],
        primary=len(rows),expected_primary=int(expected_primary),break_err=x["break_err"],obs_err=x["obs_err"],shadow_err=x["shadow_err"],
        shadow_break_signs=dict(br),shadow_total_signs=dict(tr),
        shadow_break_positive=sum(r["shadow_break_positive"] for r in rows),
        shadow_total_positive=sum(r["shadow_total_positive"] for r in rows),
        overlap_observations=int(ov_n),observed_old_break_overlap=int(ov_obs_old),
        shadow_break_overlap_signs=dict(ov_sign),new_range_release_observations=int(nr_release),
        leads=leads,events=rows)

def mirror(a,c):
    am={r["index"]:r for r in a["events"]}; cm={r["index"]:r for r in c["events"]}; common=sorted(set(am)&set(cm))
    keys=("shadow_break_sign","shadow_total_sign"); total=len(common)*len(keys)
    matches=sum(am[i][k]==cm[i][k] for i in common for k in keys)
    lc=[i for i in common if am[i]["shadow_total_lead_bars"] is not None and cm[i]["shadow_total_lead_bars"] is not None]
    lm=sum(am[i]["shadow_total_lead_bars"]==cm[i]["shadow_total_lead_bars"] for i in lc)
    return dict(comparable=len(common),sign_agreement=matches/total if total else 1.0,
                lead_comparable=len(lc),lead_matches=int(lm),lead_agreement=lm/len(lc) if lc else 1.0)

def pair(frame):
    inv=phasea.reciprocal_ohlc(frame); m,cfg=b314.compute(frame); im,icfg=b314.compute(inv)
    w=int(cfg.rank_len-1); assert w==int(icfg.rank_len-1)
    b=audit(m,1,w); s=audit(m,-1,w); ib=audit(im,1,w); is_=audit(im,-1,w)
    return dict(warmup=w,bull=b,bear=s,mirror=dict(bull_vs_inverse_bear=mirror(b,is_),bear_vs_inverse_bull=mirror(s,ib)))

def build_report():
    pairs={n:pair(f) for n,f in phasea.load_frozen_pairs().items()}
    agg=dict(break_events=0,expected_break_events=0,primary=0,expected_primary=0,
             max_break_err=0.0,max_obs_err=0.0,max_shadow_err=0.0,
             shadow_break_signs=Counter(),shadow_total_signs=Counter(),shadow_break_positive=0,shadow_total_positive=0,
             overlap_observations=0,observed_old_break_overlap=0,shadow_break_overlap_signs=Counter(),
             new_range_release_observations=0,leads=[],min_sign_mirror=1.0,lead_matches=0,lead_comparable=0)
    for p in pairs.values():
        for side in ("bull","bear"):
            x=p[side]; agg["break_events"]+=x["break_events"]; agg["expected_break_events"]+=x["expected_break_events"]
            agg["primary"]+=x["primary"]; agg["expected_primary"]+=x["expected_primary"]
            agg["max_break_err"]=max(agg["max_break_err"],x["break_err"]); agg["max_obs_err"]=max(agg["max_obs_err"],x["obs_err"])
            agg["max_shadow_err"]=max(agg["max_shadow_err"],x["shadow_err"])
            agg["shadow_break_signs"].update(x["shadow_break_signs"]); agg["shadow_total_signs"].update(x["shadow_total_signs"])
            agg["shadow_break_positive"]+=x["shadow_break_positive"]; agg["shadow_total_positive"]+=x["shadow_total_positive"]
            agg["overlap_observations"]+=x["overlap_observations"]; agg["observed_old_break_overlap"]+=x["observed_old_break_overlap"]
            agg["shadow_break_overlap_signs"].update(x["shadow_break_overlap_signs"])
            agg["new_range_release_observations"]+=x["new_range_release_observations"]; agg["leads"].extend(x["leads"])
        for m in p["mirror"].values():
            agg["min_sign_mirror"]=min(agg["min_sign_mirror"],m["sign_agreement"])
            agg["lead_matches"]+=m["lead_matches"]; agg["lead_comparable"]+=m["lead_comparable"]
    leads=agg.pop("leads"); agg["shadow_break_signs"]=dict(agg["shadow_break_signs"]); agg["shadow_total_signs"]=dict(agg["shadow_total_signs"])
    agg["shadow_break_overlap_signs"]=dict(agg["shadow_break_overlap_signs"])
    agg["break_reproduction_delta"]=agg["break_events"]-agg["expected_break_events"]; agg["primary_reproduction_delta"]=agg["primary"]-agg["expected_primary"]
    agg["shadow_break_positive_share"]=agg["shadow_break_positive"]/agg["primary"] if agg["primary"] else 0
    agg["shadow_total_positive_share"]=agg["shadow_total_positive"]/agg["primary"] if agg["primary"] else 0
    agg["lead_observed"]=len(leads); agg["lead_median"]=float(np.median(leads)) if leads else None
    agg["lead_p75"]=float(np.percentile(leads,75)) if leads else None; agg["lead_max"]=int(np.max(leads)) if leads else None
    agg["lead_mirror_agreement"]=agg["lead_matches"]/agg["lead_comparable"] if agg["lead_comparable"] else 1.0
    gate=(agg["break_reproduction_delta"]==0 and agg["primary_reproduction_delta"]==0 and
          agg["max_break_err"]<=TOL and agg["max_obs_err"]<=TOL and agg["max_shadow_err"]<=TOL and agg["min_sign_mirror"]>=GATE)
    return dict(issue=68,phase="B3.16",status="COUNTERFACTUAL_STALE_RANGE_RELEASE_NO_PERFORMANCE",
                primary_gate_pass=bool(gate),aggregate=agg,pairs=pairs,
                boundary="One fixed shadow removes only old-direction range-memory evidence during MA-target stale overlap; production C-2 and parameters unchanged.")

def md(r):
    a=r["aggregate"]; b=a["shadow_break_signs"]; t=a["shadow_total_signs"]; o=a["shadow_break_overlap_signs"]
    L=["# Issue #68 Phase B3.16 — Counterfactual Stale-Range Release","",
       "Status: **diagnostic shadow only / frozen C-2 / no performance use**","",
       f"Primary engineering gate: **{'PASS' if r['primary_gate_pass'] else 'FAIL'}**",
       f"- Break final-blocker reproduction: **{a['break_events']} / {a['expected_break_events']}** (delta {a['break_reproduction_delta']})",
       f"- strict B3.15 primary reproduction: **{a['primary']} / {a['expected_primary']}** (delta {a['primary_reproduction_delta']})",
       f"- max Break reconstruction error: **{a['max_break_err']:.3e}**",
       f"- max observed/shadow six-component reconstruction error: **{a['max_obs_err']:.3e} / {a['max_shadow_err']:.3e}**",
       f"- minimum reciprocal shadow-sign agreement: **{100*a['min_sign_mirror']:.3f}%**","",
       "## Strict primary blocker-bar counterfactual","",
       f"- shadow Break target-positive: **{a['shadow_break_positive']} / {a['primary']} ({100*a['shadow_break_positive_share']:.1f}%)**",
       f"- shadow Break signs: target **{b.get('target',0)}**, neutral **{b.get('neutral',0)}**, old **{b.get('old',0)}**",
       f"- shadow total raw target-positive at `t-1`: **{a['shadow_total_positive']} / {a['primary']} ({100*a['shadow_total_positive_share']:.1f}%)**",
       f"- shadow total signs: target **{t.get('target',0)}**, neutral **{t.get('neutral',0)}**, old **{t.get('old',0)}**","",
       "## Lead before observed handoff","",
       f"- events with any shadow-total target-positive bar from MA flip through `t-1`: **{a['lead_observed']} / {a['primary']}**",
       f"- lead bars: median **{a['lead_median']}**, p75 **{a['lead_p75']}**, max **{a['lead_max']}**",
       f"- reciprocal lead agreement: **{100*a['lead_mirror_agreement']:.3f}%** ({a['lead_matches']}/{a['lead_comparable']})","",
       "## Primary event-window overlap accounting","",
       f"- stale-overlap observations: **{a['overlap_observations']}**",
       f"- observed Break old-negative observations: **{a['observed_old_break_overlap']}**",
       f"- shadow Break during overlap: target **{o.get('target',0)}**, neutral **{o.get('neutral',0)}**, old **{o.get('old',0)}**",
       f"- NEW RANGE present + observed Break old + shadow Break target: **{a['new_range_release_observations']}**","",
       "## Per-pair strict primary summary","",
       "| Pair | Primary | Shadow Break + | Shadow raw + @ blocker | Overlap obs | New-range release obs |",
       "|---|---:|---:|---:|---:|---:|"]
    for n,p in r["pairs"].items():
        xs=[p["bull"],p["bear"]]
        L.append(f"| {n} | {sum(x['primary'] for x in xs)} | {sum(x['shadow_break_positive'] for x in xs)} | {sum(x['shadow_total_positive'] for x in xs)} | {sum(x['overlap_observations'] for x in xs)} | {sum(x['new_range_release_observations'] for x in xs)} |")
    return "\n".join(L+["","## Boundary","",r["boundary"],""])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--report-json",type=Path,required=True); ap.add_argument("--report-md",type=Path,required=True); z=ap.parse_args()
    r=build_report(); z.report_json.parent.mkdir(parents=True,exist_ok=True); z.report_md.parent.mkdir(parents=True,exist_ok=True)
    z.report_json.write_text(json.dumps(r,indent=2,ensure_ascii=False),encoding="utf-8"); z.report_md.write_text(md(r),encoding="utf-8")
    if not r["primary_gate_pass"]: raise SystemExit("B3.16 engineering gate failed")
    print(md(r))
if __name__=="__main__": main()
