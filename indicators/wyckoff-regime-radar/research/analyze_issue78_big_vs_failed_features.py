#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, math, statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

MARKER='ISSUE76|schema=1'
TREND={2:'Markup',5:'Markdown'}
GENTLE=(1.00,1.00,0.75,0.50,0.25)
ERAS=(("2010-2014",2010,2014),("2015-2019",2015,2019),("2020-2026",2020,2026))

# +1 means higher feature value is hypothesized to indicate better trend quality.
# -1 means lower feature value is hypothesized to indicate better trend quality.
FEATURES={
    'e0_abs_er20':(+1,'E0'), 'e0_abs_er63':(+1,'E0'), 'e0_abs_er126':(+1,'E0'),
    'e0_dir_er20':(+1,'E0'), 'e0_dir_er63':(+1,'E0'), 'e0_dir_er126':(+1,'E0'),
    'e0_disp20_atr':(+1,'E0'), 'e0_disp63_atr':(+1,'E0'), 'e0_disp126_atr':(+1,'E0'),
    'e0_escape63_atr':(+1,'E0'), 'e0_escape126_atr':(+1,'E0'), 'e0_escape252_atr':(+1,'E0'),
    'e0_range_pos63':(+1,'E0'), 'e0_range_pos126':(+1,'E0'), 'e0_range_pos252':(+1,'E0'),
    'e0_stage_changes20':(-1,'E0'), 'e0_stage_changes63':(-1,'E0'),
    'e0_fresh_trend_entries63':(-1,'E0'), 'e0_fresh_trend_entries126':(-1,'E0'),
    'e0_trend_occupancy63':(+1,'E0'), 'e0_trend_occupancy126':(+1,'E0'),
    'e5_cum_atr':(+1,'E5'), 'e5_mfe_atr':(+1,'E5'), 'e5_giveback_atr':(-1,'E5'), 'e5_dir_eff':(+1,'E5'),
    'e10_cum_atr':(+1,'E10'), 'e10_mfe_atr':(+1,'E10'), 'e10_giveback_atr':(-1,'E10'), 'e10_dir_eff':(+1,'E10'),
}

def parse_marker(text):
    p=text.find(MARKER)
    if p<0:return None
    out={}
    for tok in text[p:].strip().split('|'):
        if '=' in tok:
            k,v=tok.split('=',1);out[k]=v
    return out

def read_events(paths):
    dedup={}
    for path in paths:
        with Path(path).open(encoding='utf-8-sig',newline='') as fh:
            for row in csv.reader(fh):
                f=None
                for cell in row:
                    f=parse_marker(cell)
                    if f:break
                if not f:continue
                rec={'ticker':f['ticker'],'repr':f['repr'],'event_time':int(f['event_time']),
                     'event_bar':int(f['event_bar']),'stage':int(f['stage']),'fresh':int(f['fresh']),
                     'scale':float(f['scale']),'move1':float(f['move1'])}
                dedup[(rec['ticker'],rec['event_time'],rec['event_bar'])]=rec
    return sorted(dedup.values(),key=lambda r:(r['ticker'],r['event_bar']))

def episodes(events):
    by=defaultdict(list)
    for e in events:by[e['ticker']].append(e)
    out=[]
    for ticker,g in by.items():
        g.sort(key=lambda r:r['event_bar'])
        i=0;eid=0
        while i<len(g):
            r=g[i];st=r['stage']
            if st in TREND and r['fresh']==1:
                j=i+1
                while j<len(g) and g[j]['stage']==st and g[j]['event_bar']==g[j-1]['event_bar']+1:
                    j+=1
                if j<len(g):out.append((ticker,st,eid,g[i:j]));eid+=1
                i=j
            else:i+=1
    return out

def denom_entry(row):
    return row['scale']*(100.0 if row['repr']=='YIELD_LEVEL' else 1.0)

def steps_entry_atr(stage,rows):
    den=denom_entry(rows[0]);d=1.0 if stage==2 else -1.0
    return [r['move1']/den*d for r in rows]

def bucket(g):
    if g<0.5:return 0
    if g<1:return 1
    if g<2:return 2
    if g<4:return 3
    return 4

def persistence_cap(age):
    if age<5:return .25
    if age<10:return .50
    if age<20:return .75
    return 1.0

def gentle_latch(steps):
    cum=peak=0.0;latch=1.0;prev_new=False;out=[]
    for i,step in enumerate(steps):
        if i==0:latch=1.0
        elif prev_new:latch=1.0
        else:latch=min(latch,GENTLE[bucket(max(0.0,peak-cum))])
        out.append(latch)
        new=cum+step;prev_new=new>peak+1e-12
        if prev_new:peak=new
        cum=new
    return out

def era(ms):
    y=datetime.fromtimestamp(ms/1000,tz=timezone.utc).year
    for name,a,b in ERAS:
        if a<=y<=b:return name
    return 'other'

def auc(pos,neg):
    if not pos or not neg:return math.nan
    wins=0.0
    for p in pos:
        for n in neg:
            wins += 1.0 if p>n else 0.5 if p==n else 0.0
    return wins/(len(pos)*len(neg))

def mean(xs):
    xs=[x for x in xs if isinstance(x,(int,float)) and math.isfinite(x)]
    return statistics.fmean(xs) if xs else math.nan

def median(xs):
    xs=[x for x in xs if isinstance(x,(int,float)) and math.isfinite(x)]
    return statistics.median(xs) if xs else math.nan

def percentile_ranks(vals):
    n=len(vals);order=sorted(range(n),key=lambda i:vals[i]);ranks=[0.0]*n;i=0
    while i<n:
        j=i+1
        while j<n and vals[order[j]]==vals[order[i]]:j+=1
        av=(i+j-1)/2;pct=av/(n-1) if n>1 else .5
        for k in range(i,j):ranks[order[k]]=pct
        i=j
    return ranks

def trailing_rows(index_by_bar,entry_bar,h):
    rows=[]
    for b in range(entry_bar-h,entry_bar):
        r=index_by_bar.get(b)
        if r is None:return None
        rows.append(r)
    return rows

def path_features(rows,direction,den):
    moves=[r['move1'] for r in rows];net=sum(moves);path=sum(abs(x) for x in moves)
    return (abs(net)/path if path>0 else math.nan,
            direction*net/path if path>0 else math.nan,
            direction*net/den)

def range_features(rows,direction,den):
    closes=[0.0];x=0.0
    for r in rows:
        x+=r['move1'];closes.append(x)
    entry=closes[-1];prior=closes[:-1];lo=min(prior);hi=max(prior)
    escape=(entry-hi)/den if direction>0 else (lo-entry)/den
    width=hi-lo
    if width<=0:pos=math.nan
    elif direction>0:pos=(entry-lo)/width
    else:pos=(hi-entry)/width
    return escape,pos

def stage_hist_features(rows):
    stages=[r['stage'] for r in rows]
    changes=sum(stages[i]!=stages[i-1] for i in range(1,len(stages)))
    fresh=sum(r['fresh']==1 and r['stage'] in TREND for r in rows)
    occ=sum(r['stage'] in TREND for r in rows)/len(rows)
    return changes,fresh,occ

def early_features(steps,k):
    if len(steps)<k:return (math.nan,)*4
    s=steps[:k];cum=0.0;peak=0.0
    for x in s:
        cum+=x;peak=max(peak,cum)
    path=sum(abs(x) for x in s)
    return cum,peak,peak-cum,(cum/path if path>0 else math.nan)

def build_episode_rows(events,eps):
    by=defaultdict(dict)
    for r in events:by[r['ticker']][r['event_bar']]=r
    out=[]
    for ticker,stage,eid,rows in eps:
        ent=rows[0];eb=ent['event_bar'];direction=1.0 if stage==2 else -1.0;den=denom_entry(ent)
        steps=steps_entry_atr(stage,rows);cum=0.0;mfe=0.0
        for x in steps:
            cum+=x;mfe=max(mfe,cum)
        if mfe<4:label='Failed'
        elif mfe>=8:label='Large'
        else:label='Middle'
        latch=gentle_latch(steps);exp=[min(persistence_cap(i),l) for i,l in enumerate(latch)]
        pg=sum(e*x for e,x in zip(exp,steps))
        rec={'ticker':ticker,'stage':TREND[stage],'stage_id':stage,'episode_id':eid,'entry_time':ent['event_time'],'entry_bar':eb,
             'era':era(ent['event_time']),'bars':len(steps),'mfe':mfe,'label':label,'persistence_gentle_return':pg}
        for h in (20,63,126):
            tr=trailing_rows(by[ticker],eb,h)
            if tr:
                a,d,disp=path_features(tr,direction,den)
                rec[f'e0_abs_er{h}']=a;rec[f'e0_dir_er{h}']=d;rec[f'e0_disp{h}_atr']=disp
            else:rec[f'e0_abs_er{h}']=rec[f'e0_dir_er{h}']=rec[f'e0_disp{h}_atr']=math.nan
        for h in (63,126,252):
            tr=trailing_rows(by[ticker],eb,h)
            if tr:
                esc,pos=range_features(tr,direction,den)
                rec[f'e0_escape{h}_atr']=esc;rec[f'e0_range_pos{h}']=pos
            else:rec[f'e0_escape{h}_atr']=rec[f'e0_range_pos{h}']=math.nan
        for h in (20,63):
            tr=trailing_rows(by[ticker],eb,h)
            rec[f'e0_stage_changes{h}']=stage_hist_features(tr)[0] if tr else math.nan
        for h in (63,126):
            tr=trailing_rows(by[ticker],eb,h)
            if tr:
                _,fr,oc=stage_hist_features(tr);rec[f'e0_fresh_trend_entries{h}']=fr;rec[f'e0_trend_occupancy{h}']=oc
            else:rec[f'e0_fresh_trend_entries{h}']=rec[f'e0_trend_occupancy{h}']=math.nan
        for k in (5,10):
            c,m,g,ef=early_features(steps,k)
            rec[f'e{k}_cum_atr']=c;rec[f'e{k}_mfe_atr']=m;rec[f'e{k}_giveback_atr']=g;rec[f'e{k}_dir_eff']=ef
        out.append(rec)
    return out

def separation_rows(ep_rows):
    rows=[]
    for feat,(orient,info) in FEATURES.items():
        for scope,subset in [('all',list(ep_rows))]+[(e,[r for r in ep_rows if r['era']==e]) for e,_,_ in ERAS]:
            markets=[]
            for t in sorted(set(r['ticker'] for r in subset)):
                g=[r for r in subset if r['ticker']==t and math.isfinite(r.get(feat,math.nan)) and r['label'] in ('Large','Failed')]
                pos=[orient*r[feat] for r in g if r['label']=='Large'];neg=[orient*r[feat] for r in g if r['label']=='Failed']
                if len(pos)>=3 and len(neg)>=3:
                    markets.append({'ticker':t,'auc':auc(pos,neg),'large_n':len(pos),'failed_n':len(neg),
                                    'large_median':median([r[feat] for r in g if r['label']=='Large']),
                                    'failed_median':median([r[feat] for r in g if r['label']=='Failed'])})
            if markets:
                rows.append({'feature':feat,'information_set':info,'orientation':orient,'scope':scope,'markets':len(markets),
                             'large_n':sum(m['large_n'] for m in markets),'failed_n':sum(m['failed_n'] for m in markets),
                             'eq_market_mean_auc':mean([m['auc'] for m in markets]),'eq_market_median_auc':median([m['auc'] for m in markets]),
                             'markets_auc_gt_0_5':sum(m['auc']>.5 for m in markets),
                             'eq_market_large_median':mean([m['large_median'] for m in markets]),
                             'eq_market_failed_median':mean([m['failed_median'] for m in markets])})
    return rows

def per_market_separation(ep_rows):
    rows=[]
    for feat,(orient,info) in FEATURES.items():
        for scope,subset in [('all',list(ep_rows))]+[(e,[r for r in ep_rows if r['era']==e]) for e,_,_ in ERAS]:
            for t in sorted(set(r['ticker'] for r in subset)):
                g=[r for r in subset if r['ticker']==t and math.isfinite(r.get(feat,math.nan)) and r['label'] in ('Large','Failed')]
                pos=[orient*r[feat] for r in g if r['label']=='Large'];neg=[orient*r[feat] for r in g if r['label']=='Failed']
                if len(pos)>=3 and len(neg)>=3:
                    rows.append({'feature':feat,'information_set':info,'orientation':orient,'scope':scope,'ticker':t,
                                 'large_n':len(pos),'failed_n':len(neg),'auc':auc(pos,neg),
                                 'large_median':median([r[feat] for r in g if r['label']=='Large']),
                                 'failed_median':median([r[feat] for r in g if r['label']=='Failed'])})
    return rows

def direction_rows(ep_rows):
    out=[]
    for feat,(orient,info) in FEATURES.items():
        for stage in ('Markup','Markdown'):
            subset=[r for r in ep_rows if r['stage']==stage];markets=[]
            for t in sorted(set(r['ticker'] for r in subset)):
                g=[r for r in subset if r['ticker']==t and math.isfinite(r.get(feat,math.nan)) and r['label'] in ('Large','Failed')]
                pos=[orient*r[feat] for r in g if r['label']=='Large'];neg=[orient*r[feat] for r in g if r['label']=='Failed']
                if len(pos)>=3 and len(neg)>=3:markets.append({'auc':auc(pos,neg),'large_n':len(pos),'failed_n':len(neg)})
            if markets:
                out.append({'feature':feat,'information_set':info,'stage':stage,'markets':len(markets),
                            'large_n':sum(m['large_n'] for m in markets),'failed_n':sum(m['failed_n'] for m in markets),
                            'eq_market_mean_auc':mean([m['auc'] for m in markets]),
                            'markets_auc_gt_0_5':sum(m['auc']>.5 for m in markets)})
    return out

def quintile_rows(ep_rows):
    out=[]
    for feat,(orient,info) in FEATURES.items():
        market_q=[]
        for t in sorted(set(r['ticker'] for r in ep_rows)):
            g=[r for r in ep_rows if r['ticker']==t and math.isfinite(r.get(feat,math.nan))]
            if len(g)<20:continue
            scores=[orient*r[feat] for r in g];pcts=percentile_ranks(scores)
            for r,p in zip(g,pcts):market_q.append((t,min(5,int(p*5)+1),r))
        for q in range(1,6):
            per=[]
            for t in sorted(set(x[0] for x in market_q)):
                gg=[r for tt,qq,r in market_q if tt==t and qq==q]
                if not gg:continue
                per.append({'large_share':mean([1.0 if r['label']=='Large' else 0.0 for r in gg]),
                            'failed_share':mean([1.0 if r['label']=='Failed' else 0.0 for r in gg]),
                            'pg_return':mean([r['persistence_gentle_return'] for r in gg]),'n':len(gg)})
            if per:
                out.append({'feature':feat,'information_set':info,'quality_quintile':q,'markets':len(per),'episodes':sum(x['n'] for x in per),
                            'eq_market_large_share':mean([x['large_share'] for x in per]),
                            'eq_market_failed_share':mean([x['failed_share'] for x in per]),
                            'eq_market_pg_return':mean([x['pg_return'] for x in per])})
    return out

def write_csv(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:return
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('inputs',nargs='+');ap.add_argument('--output-dir',required=True);args=ap.parse_args()
    ev=read_events(args.inputs);eps=episodes(ev)
    if len(ev)!=68118:raise SystemExit(f'event count drift: {len(ev)}')
    if len(eps)!=1624:raise SystemExit(f'episode count drift: {len(eps)}')
    rows=build_episode_rows(ev,eps);sep=separation_rows(rows);pm=per_market_separation(rows);dr=direction_rows(rows);q=quintile_rows(rows)
    out=Path(args.output_dir)
    write_csv(out/'issue78-big-vs-failed-episodes.csv',rows)
    write_csv(out/'issue78-big-vs-failed-separation.csv',sep)
    write_csv(out/'issue78-big-vs-failed-per-market.csv',pm)
    write_csv(out/'issue78-big-vs-failed-direction.csv',dr)
    write_csv(out/'issue78-big-vs-failed-quintiles.csv',q)
    print('events',len(ev),'episodes',len(eps),'large',sum(r['label']=='Large' for r in rows),'failed',sum(r['label']=='Failed' for r in rows),'middle',sum(r['label']=='Middle' for r in rows))
    alls=sorted([r for r in sep if r['scope']=='all'],key=lambda r:r['eq_market_mean_auc'],reverse=True)
    for r in alls:print(f"{r['feature']:28s} {r['information_set']:3s} auc={r['eq_market_mean_auc']:.3f} med={r['eq_market_median_auc']:.3f} gt50={r['markets_auc_gt_0_5']}/{r['markets']} n={r['large_n']}/{r['failed_n']}")
if __name__=='__main__':main()
