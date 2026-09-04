#!/usr/bin/env python3
"""Issue #68 B3.12 Structure step / MA-cross audit. Diagnostic only."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
import diagnose_issue66_reciprocal_symmetry as phasea
import diagnose_issue68_phase_b38_raw_feature_attribution as b38
import diagnose_issue68_phase_b310_s5_vs_s2_local_duel as b310

GATE=0.99
TOL=1e-9

def f(m:pd.DataFrame,k:str)->np.ndarray:
    return pd.to_numeric(m[k],errors="coerce").to_numpy(float)

def stats(x:list[int])->dict[str,float|int|None]:
    a=np.asarray(x,float)
    return {"n":int(len(a)),"median":float(np.median(a)) if len(a) else None,"p90":float(np.percentile(a,90)) if len(a) else None,"max":float(np.max(a)) if len(a) else None}

def run_before(x:np.ndarray,t:int)->int:
    n=0;i=t-1
    while i>=0 and np.isfinite(x[i]) and x[i]>0:n+=1;i-=1
    return n

def audit(m:pd.DataFrame,direction:int,warmup:int)->dict[str,Any]:
    fr=b38.fresh_pair_components(m)["arrays"]
    duel=b310.direction_duel_from_arrays(fr,direction,warmup)
    hand=duel["_arrays"]["handoff"]
    hs=np.flatnonzero(hand)
    st=direction*np.asarray(fr["structure"],float)
    br=direction*np.asarray(fr["break"],float)
    direct=direction*np.asarray(fr["direct"],float)
    close=f(m,"close"); lc=np.log(np.where(close>0,close,np.nan))
    ma50=f(m,"issue66_b1_ma_log");ma200=f(m,"issue66_b1_maturity_ma_log")
    t50=(lc>ma50) if direction==1 else (lc<ma50)
    t200=(lc>ma200) if direction==1 else (lc<ma200)
    p50=np.roll(t50,1);p50[0]=False;p200=np.roll(t200,1);p200[0]=False
    pst=np.roll(st,1);pst[0]=np.nan
    improve=hand&(st>pst);c50=hand&t50&~p50;c200=hand&t200&~p200
    trans={f"{a}->{b}":0 for a in (-1,0,1) for b in (-1,0,1)}
    cross={"ma50_only":0,"ma200_only":0,"both":0,"neither":0}
    bprev=bnow=sprev=snow=early=unexpl=0;bruns=[];sruns=[]
    state=np.sign(np.where(np.abs(st)<1e-12,0,st)).astype(int)
    for t in hs:
        trans[f"{state[t-1]}->{state[t]}"]+=1
        a=bool(c50[t]);b=bool(c200[t]);cross["both" if a and b else "ma50_only" if a else "ma200_only" if b else "neither"]+=1
        unexpl+=int(improve[t] and not(a or b))
        bprev+=int(br[t-1]>0);bnow+=int(br[t]>0);sprev+=int(st[t-1]>0);snow+=int(st[t]>0)
        early+=int(br[t-1]>0 and st[t-1]<=0)
        bruns.append(run_before(br,t));sruns.append(run_before(st,t))
    recon=np.asarray(fr["reconstructed"],float)
    finite=np.isfinite(recon)&np.isfinite(fr["direct"])
    err=float(np.nanmax(np.abs(recon[finite]-np.asarray(fr["direct"])[finite]))) if np.any(finite) else 0.0
    n=len(hs)
    return {"handoffs":n,"structure_improves":int(np.sum(improve)),"structure_improve_share":float(np.sum(improve)/n) if n else 0.0,"cross":cross,"transitions":trans,"break_pos_prev":bprev,"break_pos_now":bnow,"structure_pos_prev":sprev,"structure_pos_now":snow,"break_pos_structure_not_prev":early,"break_pos_structure_not_prev_share":early/n if n else 0.0,"break_run_prev":stats(bruns),"structure_run_prev":stats(sruns),"unexplained_improvements":unexpl,"recon_error":err,"_a":{"handoff":hand,"improve":improve,"c50":c50,"c200":c200}}

def compare(a:dict[str,Any],b:dict[str,Any],warmup:int)->dict[str,Any]:
    ah=a["_a"]["handoff"][warmup:];bh=b["_a"]["handoff"][warmup:]
    both=ah&bh;n=int(np.sum(both))
    def q(k:str):
        x=a["_a"][k][warmup:][both];y=b["_a"][k][warmup:][both];m=int(np.sum(x==y)) if n else 0
        return m,n,m/n if n else 1.0
    im,_,ia=q("improve");m50,_,a50=q("c50");m200,_,a200=q("c200")
    return {"event_agreement":float(np.mean(ah==bh)) if len(ah) else 1.0,"comparable":n,"improve_matches":im,"improve_agreement":ia,"ma50_matches":m50,"ma50_agreement":a50,"ma200_matches":m200,"ma200_agreement":a200}

def clean(x):return {k:v for k,v in x.items() if k!="_a"}

def pair(frame:pd.DataFrame)->dict[str,Any]:
    inv=phasea.reciprocal_ohlc(frame);m,c=b38._compute(frame);im,ic=b38._compute(inv);w=int(c.rank_len-1)
    bull=audit(m,1,w);bear=audit(m,-1,w);ib=audit(im,1,w);ir=audit(im,-1,w)
    return {"warmup":w,"bull":clean(bull),"bear":clean(bear),"mirror":{"bull_inverse_bear":compare(bull,ir,w),"bear_inverse_bull":compare(bear,ib,w)}}

def build()->dict[str,Any]:
    ps={k:pair(v) for k,v in phasea.load_frozen_pairs().items()}
    a={"handoffs":0,"structure_improves":0,"ma50_only":0,"ma200_only":0,"both":0,"neither":0,"break_pos_prev":0,"break_pos_structure_not_prev":0,"unexplained":0,"recon_error":0.0,"min_event_agreement":1.0,"comp":0,"improve_matches":0,"ma50_matches":0,"ma200_matches":0}
    tr={f"{x}->{y}":0 for x in(-1,0,1) for y in(-1,0,1)};br=[];sr=[]
    for p in ps.values():
        for side in("bull","bear"):
            x=p[side];a["handoffs"]+=x["handoffs"];a["structure_improves"]+=x["structure_improves"];a["break_pos_prev"]+=x["break_pos_prev"];a["break_pos_structure_not_prev"]+=x["break_pos_structure_not_prev"];a["unexplained"]+=x["unexplained_improvements"];a["recon_error"]=max(a["recon_error"],x["recon_error"])
            for k in("ma50_only","ma200_only","both","neither"):a[k]+=x["cross"][k]
            for k,v in x["transitions"].items():tr[k]+=v
        for m in p["mirror"].values():
            a["min_event_agreement"]=min(a["min_event_agreement"],m["event_agreement"]);a["comp"]+=m["comparable"];a["improve_matches"]+=m["improve_matches"];a["ma50_matches"]+=m["ma50_matches"];a["ma200_matches"]+=m["ma200_matches"]
    n=a["handoffs"];c=a["comp"];a["structure_improve_share"]=a["structure_improves"]/n if n else 0;a["break_pos_prev_share"]=a["break_pos_prev"]/n if n else 0;a["break_pos_structure_not_prev_share"]=a["break_pos_structure_not_prev"]/n if n else 0;a["transitions"]=tr
    a["improve_agreement"]=a["improve_matches"]/c if c else 1;a["ma50_agreement"]=a["ma50_matches"]/c if c else 1;a["ma200_agreement"]=a["ma200_matches"]/c if c else 1
    ok=a["recon_error"]<=TOL and a["min_event_agreement"]>=GATE and a["improve_agreement"]>=GATE and a["ma50_agreement"]>=GATE and a["ma200_agreement"]>=GATE and a["unexplained"]==0
    return {"issue":68,"phase":"B3.12","primary_gate_pass":bool(ok),"aggregate":a,"pairs":ps,"boundary":"Frozen Structure/MA timing diagnostic only; no model or performance change."}

def md(r):
    a=r["aggregate"];return "\n".join(["# Issue #68 Phase B3.12 — Structure Step / MA-Cross Audit","",f"Primary engineering gate: **{'PASS' if r['primary_gate_pass'] else 'FAIL'}**",f"- handoffs: **{a['handoffs']}**",f"- Structure improves on handoff: **{a['structure_improves']}** ({100*a['structure_improve_share']:.1f}%)",f"- crosses: MA50 only **{a['ma50_only']}**, MA200 only **{a['ma200_only']}**, both **{a['both']}**, neither **{a['neither']}**",f"- Break already target-positive t-1: **{a['break_pos_prev']}** ({100*a['break_pos_prev_share']:.1f}%)",f"- Break+ while Structure<=0 t-1: **{a['break_pos_structure_not_prev']}** ({100*a['break_pos_structure_not_prev_share']:.1f}%)",f"- unexplained Structure improvements: **{a['unexplained']}**",f"- reconstruction error: **{a['recon_error']:.3e}**",f"- min handoff mirror: **{100*a['min_event_agreement']:.3f}%**",f"- pooled Structure-improve mirror: **{100*a['improve_agreement']:.3f}%**",f"- pooled MA50/MA200 mirror: **{100*a['ma50_agreement']:.3f}% / {100*a['ma200_agreement']:.3f}%**","",r["boundary"],""])
def main():
    p=argparse.ArgumentParser();p.add_argument("--report-json",type=Path);p.add_argument("--report-md",type=Path);z=p.parse_args();r=build()
    if z.report_json:z.report_json.parent.mkdir(parents=True,exist_ok=True);z.report_json.write_text(json.dumps(r,indent=2),encoding="utf-8")
    if z.report_md:z.report_md.parent.mkdir(parents=True,exist_ok=True);z.report_md.write_text(md(r),encoding="utf-8")
    print(md(r));raise SystemExit(0 if r["primary_gate_pass"] else 1)
if __name__=="__main__":main()
