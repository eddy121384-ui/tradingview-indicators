#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, glob, math, statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

MARKER="ISSUE76|schema=1"
TREND={2:"Markup",5:"Markdown"}
POLICIES=("full","proof_0_5","proof_1_0","proof_2_0","ladder")
ERAS=(("2010-2014",2010,2014),("2015-2019",2015,2019),("2020-2026",2020,2026))
EXPECTED_EVENTS=68118
EXPECTED_EPISODES=1624

def parse_marker(text):
    p=text.find(MARKER)
    if p<0:return None
    out={}
    for tok in text[p:].strip().split("|"):
        if "=" in tok:
            k,v=tok.split("=",1);out[k]=v
    return out

def read_events(paths):
    dedup={}
    for path in paths:
        with Path(path).open(encoding="utf-8-sig",newline="") as fh:
            for row in csv.reader(fh):
                f=None
                for cell in row:
                    f=parse_marker(cell)
                    if f:break
                if not f:continue
                rec={"ticker":f["ticker"],"repr":f["repr"],"event_time":int(f["event_time"]),
                     "event_bar":int(f["event_bar"]),"stage":int(f["stage"]),"fresh":int(f["fresh"]),
                     "scale":float(f["scale"]),"move1":float(f["move1"])}
                dedup[(rec["ticker"],rec["event_time"],rec["event_bar"])]=rec
    return sorted(dedup.values(),key=lambda r:(r["ticker"],r["event_bar"]))

def episodes(events):
    by=defaultdict(list)
    for e in events:by[e["ticker"]].append(e)
    out=[]
    for ticker,g in by.items():
        g.sort(key=lambda r:r["event_bar"])
        i=0;eid=0
        while i<len(g):
            r=g[i];st=r["stage"]
            if st in TREND and r["fresh"]==1:
                j=i+1
                while j<len(g) and g[j]["stage"]==st and g[j]["event_bar"]==g[j-1]["event_bar"]+1:
                    j+=1
                if j<len(g):out.append((ticker,st,eid,g[i:j]));eid+=1
                i=j
            else:i+=1
    return out

def aligned_steps(ep):
    ticker,st,eid,rows=ep
    d=1.0 if st==2 else -1.0
    den=rows[0]["scale"]*(100.0 if rows[0]["repr"]=="YIELD_LEVEL" else 1.0)
    return [d*r["move1"]/den for r in rows]

def era(ms):
    y=datetime.fromtimestamp(ms/1000,tz=timezone.utc).year
    for n,a,b in ERAS:
        if a<=y<=b:return n
    return "other"

def exposure(policy,peak):
    if policy=="full":return 1.0
    if policy=="proof_0_5":return 1.0 if peak>=0.5 else 0.25
    if policy=="proof_1_0":return 1.0 if peak>=1.0 else 0.25
    if policy=="proof_2_0":return 1.0 if peak>=2.0 else 0.25
    if policy=="ladder":
        if peak>=2.0:return 1.0
        if peak>=1.0:return 0.75
        if peak>=0.5:return 0.50
        return 0.25
    raise ValueError(policy)

def mean(xs):
    xs=[x for x in xs if isinstance(x,(int,float)) and math.isfinite(x)]
    return statistics.fmean(xs) if xs else math.nan

def simulate(ep):
    ticker,st,eid,rows=ep
    ss=aligned_steps(ep)
    x=0.0;cums=[0.0]
    for step in ss:
        x+=step;cums.append(x)
    mfe=max(cums)
    sl="failed" if mfe<4 else "large" if mfe>=8 else "middle"
    recs=[]
    for policy in POLICIES:
        cum=peak=harvest=0.0;exps=[]
        for step in ss:
            e=exposure(policy,peak)
            exps.append(e);harvest+=e*step
            cum+=step;peak=max(peak,cum)
        changes=[exps[0]]+[exps[i]-exps[i-1] for i in range(1,len(exps))]+[-exps[-1]]
        recs.append({"ticker":ticker,"stage":TREND[st],"episode_id":eid,"era":era(rows[0]["event_time"]),
                     "slice":sl,"policy":policy,"mfe":mfe,"harvest":harvest,
                     "avg_exposure":mean(exps),
                     "under_full_frac":mean([1.0 if e<1.0 else 0.0 for e in exps]),
                     "increase_count":sum(c>1e-12 for c in changes[1:-1]),
                     "turnover":sum(abs(c) for c in changes)})
    return recs

def summarize(records,group_fields):
    mg=defaultdict(list)
    for r in records:mg[tuple(r[f] for f in group_fields)+(r["ticker"],)].append(r)
    market=[]
    for key,g in mg.items():
        row={f:v for f,v in zip(group_fields,key[:-1])}
        row["ticker"]=key[-1];row["n"]=len(g)
        for m in ("harvest","avg_exposure","under_full_frac","increase_count","turnover"):
            row[m]=mean([r[m] for r in g])
        market.append(row)
    ug=defaultdict(list)
    for r in market:ug[tuple(r[f] for f in group_fields)].append(r)
    universal=[]
    for key,g in ug.items():
        row={f:v for f,v in zip(group_fields,key)}
        row["markets"]=len(g);row["pooled_n"]=sum(x["n"] for x in g)
        for m in ("harvest","avg_exposure","under_full_frac","increase_count","turnover"):
            row[m+"_eq_market_mean"]=mean([x[m] for x in g])
        universal.append(row)
    return market,universal

def write_csv(path,rows):
    if not rows:return
    with Path(path).open("w",encoding="utf-8",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("paths",nargs="*")
    ap.add_argument("--out",default="/mnt/data/issue78-progressive-proof-ladder")
    args=ap.parse_args()
    paths=args.paths or sorted(glob.glob("/mnt/data/pine-logs-#76 Forward Logger*.csv"))
    events=read_events(paths);eps=episodes(events)
    if len(events)!=EXPECTED_EVENTS:raise AssertionError(f"event count drift: {len(events)}")
    if len(eps)!=EXPECTED_EPISODES:raise AssertionError(f"episode count drift: {len(eps)}")
    records=[]
    for ep in eps:records.extend(simulate(ep))
    m_slice,u_slice=summarize(records,("slice","policy"))
    _,u_all=summarize(records,("policy",))
    _,u_temp=summarize(records,("era","policy"))
    _,u_dir=summarize(records,("stage","policy"))
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    write_csv(out/"issue78-progressive-proof-ladder-per-market.csv",m_slice)
    write_csv(out/"issue78-progressive-proof-ladder-slices.csv",u_slice)
    write_csv(out/"issue78-progressive-proof-ladder-universal.csv",u_all)
    write_csv(out/"issue78-progressive-proof-ladder-temporal.csv",u_temp)
    write_csv(out/"issue78-progressive-proof-ladder-direction.csv",u_dir)
    print("events",len(events),"episodes",len(eps),"records",len(records))

if __name__=="__main__":main()
