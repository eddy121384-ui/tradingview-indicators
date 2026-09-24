#!/usr/bin/env python3
from __future__ import annotations
import csv, glob, math, statistics
from collections import defaultdict
from pathlib import Path

MARKER='ISSUE76|schema=1'
TREND={2:'Markup',5:'Markdown'}
LADDERS={
 'gentle':(1.00,1.00,0.75,0.50,0.25),
 'balanced':(1.00,0.75,0.50,0.25,0.00),
}


def parse_marker(text):
    p=text.find(MARKER)
    if p<0: return None
    out={}
    for tok in text[p:].strip().split('|'):
        if '=' in tok:
            k,v=tok.split('=',1); out[k]=v
    return out


def read_events(paths):
    dedup={}
    for path in paths:
        with open(path,encoding='utf-8-sig',newline='') as fh:
            for row in csv.reader(fh):
                f=None
                for cell in row:
                    f=parse_marker(cell)
                    if f: break
                if not f: continue
                rec={
                    'ticker':f['ticker'],'repr':f['repr'],'event_time':int(f['event_time']),
                    'event_bar':int(f['event_bar']),'stage':int(f['stage']),'fresh':int(f['fresh']),
                    'scale':float(f['scale']),'move1':float(f['move1'])
                }
                dedup[(rec['ticker'],rec['event_time'],rec['event_bar'])]=rec
    return sorted(dedup.values(), key=lambda r:(r['ticker'],r['event_bar']))


def episodes(events):
    by=defaultdict(list)
    for e in events: by[e['ticker']].append(e)
    out=[]
    for ticker,g in by.items():
        g.sort(key=lambda r:r['event_bar'])
        i=0; eid=0
        while i<len(g):
            r=g[i]; st=r['stage']
            if st in TREND and r['fresh']==1:
                j=i+1
                while j<len(g) and g[j]['stage']==st and g[j]['event_bar']==g[j-1]['event_bar']+1:
                    j+=1
                # right-censored terminal spell excluded
                if j<len(g): out.append((ticker,st,eid,g[i:j])); eid+=1
                i=j
            else: i+=1
    return out


def steps_entry_atr(stage, rows):
    scale=rows[0]['scale']; denom=scale*(100.0 if rows[0]['repr']=='YIELD_LEVEL' else 1.0)
    d=1.0 if stage==2 else -1.0
    return [r['move1']/denom*d for r in rows]


def bucket(g):
    if g<0.5:return 0
    if g<1.0:return 1
    if g<2.0:return 2
    if g<4.0:return 3
    return 4


def age_cap(age):
    if age<5:return .25
    if age<10:return .50
    if age<20:return .75
    return 1.0


def participation_caps(steps, mode):
    if mode=='full': return [1.0]*len(steps)
    caps=[]; cum=0.0; peak=0.0; earned=.25
    for age,step in enumerate(steps):
        giveback=max(0.0,peak-cum)
        if mode=='persistence':
            earned=age_cap(age)
        elif mode=='excursion':
            # use favorable excursion observed through current close only
            if peak>=2.0: earned=1.0
            elif peak>=1.0: earned=.75
            elif peak>=.5: earned=.50
            else: earned=.25
        elif mode=='persist_health':
            eligible=age_cap(age)
            if eligible>earned and giveback<1.0:
                earned=eligible
        else: raise ValueError(mode)
        caps.append(earned)
        cum += step
        peak=max(peak,cum)
    return caps


def latch_series(steps, mapping):
    # causal: exposure for step t uses health through current close; reset after prior step made new favorable extreme
    cum=0.0; peak=0.0; latch=1.0; prev_new_extreme=False
    series=[]; derisk=rerisk=0
    for i,step in enumerate(steps):
        before=latch
        if i==0:
            latch=1.0
        elif prev_new_extreme:
            latch=1.0
        else:
            target=mapping[bucket(max(0.0,peak-cum))]
            if target<latch: latch=target
        if latch<before-1e-12: derisk+=1
        if latch>before+1e-12: rerisk+=1
        series.append(latch)
        newcum=cum+step
        prev_new_extreme=newcum>peak+1e-12
        if prev_new_extreme: peak=newcum
        cum=newcum
    return series,derisk,rerisk


def sim_episode(ep):
    ticker,stage,eid,rows=ep
    steps=steps_entry_atr(stage,rows)
    cum=[0.0]; x=0.0
    for s in steps: x+=s; cum.append(x)
    mfe=max(cum)
    records=[]

    policy_specs=[('formal_hold','full',None)]
    for pmode in ['full','persistence','excursion','persist_health']:
        for lname in ['gentle','balanced']:
            policy_specs.append((f'{pmode}_{lname}_latch',pmode,lname))

    for pname,pmode,lname in policy_specs:
        pcaps=participation_caps(steps,pmode)
        p_up=sum(1 for i in range(1,len(pcaps)) if pcaps[i]>pcaps[i-1]+1e-12)
        full_idx=next((i for i,v in enumerate(pcaps) if v>=1-1e-12),None)
        if lname is None:
            latch=[1.0]*len(steps); dcount=rcount=0
        else:
            latch,dcount,rcount=latch_series(steps,LADDERS[lname])
        exp=[min(p,l) for p,l in zip(pcaps,latch)]
        weighted=[e*s for e,s in zip(exp,steps)]
        eq=[0.0]; q=0.0
        for v in weighted:q+=v;eq.append(q)
        changes=[exp[0]]+[exp[i]-exp[i-1] for i in range(1,len(exp))]+[-exp[-1]] if exp else []
        actual_up=sum(1 for c in changes[1:-1] if c>1e-12)
        actual_dn=sum(1 for c in changes[1:-1] if c<-1e-12)
        records.append({
            'ticker':ticker,'stage_name':TREND[stage],'episode_id':eid,'bars':len(steps),'mfe':mfe,
            'policy':pname,'harvest':eq[-1],'capture_ratio':eq[-1]/mfe if mfe>0 else math.nan,
            'terminal_giveback':max(eq)-eq[-1], 'avg_exposure':statistics.fmean(exp),
            'underexposed_frac':statistics.fmean(1.0 if e<1-1e-12 else 0.0 for e in exp),
            'turnover':sum(abs(c) for c in changes), 'participation_upgrade_count':p_up,
            'damage_derisk_count':dcount,'damage_rerisk_count':rcount,
            'actual_increase_count':actual_up,'actual_decrease_count':actual_dn,
            'bars_to_full_cap':float(full_idx) if full_idx is not None else math.nan,
            'never_full_cap':1.0 if full_idx is None else 0.0,
            'ever_full_actual':1.0 if any(e>=1-1e-12 for e in exp) else 0.0,
        })
    return records


def finite(vals):return [v for v in vals if isinstance(v,(int,float)) and math.isfinite(v)]
def med(vals):
    v=finite(vals); return statistics.median(v) if v else math.nan
def mean(vals):
    v=finite(vals); return statistics.fmean(v) if v else math.nan

METRICS=[
 'harvest','capture_ratio','terminal_giveback','avg_exposure','underexposed_frac','turnover',
 'participation_upgrade_count','damage_derisk_count','damage_rerisk_count','actual_increase_count','actual_decrease_count',
 'bars_to_full_cap','never_full_cap','ever_full_actual'
]

def summarize(records,slice_name,pred):
    sel=[r for r in records if pred(r['mfe'])]
    by=defaultdict(list)
    for r in sel: by[(r['stage_name'],r['policy'],r['ticker'])].append(r)
    market=[]
    for (st,pol,t),g in by.items():
        row={'slice':slice_name,'stage_name':st,'policy':pol,'ticker':t,'n':len(g),'episode_bars_median':med([r['bars'] for r in g]),'mfe_median':med([r['mfe'] for r in g])}
        for m in METRICS:
            # use mean for binary/rate/count operational metrics, median for outcome/path metrics
            if m in {'never_full_cap','ever_full_actual','participation_upgrade_count','damage_derisk_count','damage_rerisk_count','actual_increase_count','actual_decrease_count','avg_exposure','underexposed_frac','turnover'}:
                row[m]=mean([r[m] for r in g])
            else:
                row[m]=med([r[m] for r in g])
        market.append(row)
    uby=defaultdict(list)
    for r in market: uby[(r['stage_name'],r['policy'])].append(r)
    universal=[]
    for (st,pol),g in uby.items():
        row={'slice':slice_name,'stage_name':st,'policy':pol,'markets':len(g),'pooled_n':sum(r['n'] for r in g)}
        for k in ['episode_bars_median','mfe_median']+METRICS:
            row[k]=mean([r[k] for r in g])
        universal.append(row)
    return market,universal


def write_csv(path,rows):
    if not rows:return
    with open(path,'w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)


def main():
    paths=sorted(glob.glob('/mnt/data/pine-logs-#76 Forward Logger*.csv'))
    ev=read_events(paths); eps=episodes(ev)
    rec=[]
    for ep in eps: rec.extend(sim_episode(ep))
    print('files',len(paths),'events',len(ev),'episodes',len(eps),'records',len(rec))
    out=Path('/mnt/data/issue78-participation');out.mkdir(exist_ok=True)
    slices=[('all',lambda x:True),('mfe_lt4',lambda x:x<4),('mfe_ge4',lambda x:x>=4),('mfe_ge8',lambda x:x>=8)]
    mr=[];ur=[]
    for name,p in slices:
        a,b=summarize(rec,name,p);mr+=a;ur+=b
    write_csv(out/'issue78-participation-ramp-per-market.csv',mr)
    write_csv(out/'issue78-participation-ramp-universal.csv',ur)
    write_csv(out/'issue78-participation-ramp-episodes.csv',rec)
    # print compact key table
    policies=['formal_hold','full_gentle_latch','persistence_gentle_latch','excursion_gentle_latch','persist_health_gentle_latch','full_balanced_latch','persistence_balanced_latch','excursion_balanced_latch','persist_health_balanced_latch']
    for sl in ['all','mfe_lt4','mfe_ge8']:
        print('\n',sl)
        for st in ['Markup','Markdown']:
            print(st)
            rows=[r for r in ur if r['slice']==sl and r['stage_name']==st and r['policy'] in policies]
            rows=sorted(rows,key=lambda r:policies.index(r['policy']))
            for r in rows:
                print(f"{r['policy']:32s} n={r['pooled_n']:4d} harvest={r['harvest']:+.3f} giveback={r['terminal_giveback']:.3f} avgexp={r['avg_exposure']:.3f} turn={r['turnover']:.2f} neverfull={r['never_full_cap']:.3f} fullactual={r['ever_full_actual']:.3f}")

if __name__=='__main__':main()
