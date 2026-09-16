#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, datetime as dt, math, random, statistics
from collections import defaultdict
from pathlib import Path

MARKER = 'ISSUE76|schema=1'
TREND = {2:'Markup', 5:'Markdown'}
GENTLE = (1.00,1.00,0.75,0.50,0.25)
POLICIES = ('b0_persistence_gentle','b1_e5_bonus','b2_e5_e10_bonus')
FRICTIONS = (0.00,0.01,0.02,0.05,0.10)
ERAS = (
    ('2010-2014', dt.datetime(2010,1,1,tzinfo=dt.timezone.utc), dt.datetime(2015,1,1,tzinfo=dt.timezone.utc)),
    ('2015-2019', dt.datetime(2015,1,1,tzinfo=dt.timezone.utc), dt.datetime(2020,1,1,tzinfo=dt.timezone.utc)),
    ('2020-2026', dt.datetime(2020,1,1,tzinfo=dt.timezone.utc), dt.datetime(2027,1,1,tzinfo=dt.timezone.utc)),
)
EPS=1e-12
BOOTSTRAP_SEED=8701
BOOTSTRAP_REPS=5000


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
                r={'ticker':f['ticker'],'repr':f['repr'],'event_time':int(f['event_time']),
                   'event_bar':int(f['event_bar']),'stage':int(f['stage']),'fresh':int(f['fresh']),
                   'scale':float(f['scale']),'move1':float(f['move1'])}
                dedup[(r['ticker'],r['event_time'],r['event_bar'])]=r
    return sorted(dedup.values(),key=lambda r:(r['ticker'],r['event_bar']))


def episodes(events):
    by=defaultdict(list)
    for r in events:by[r['ticker']].append(r)
    out=[]
    for ticker,g in by.items():
        g.sort(key=lambda r:r['event_bar']);i=0;eid=0
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


def steps_entry_atr(stage,rows):
    den=rows[0]['scale']*(100.0 if rows[0]['repr']=='YIELD_LEVEL' else 1.0)
    d=1.0 if stage==2 else -1.0
    return [r['move1']/den*d for r in rows]


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


def persistence_caps(steps):
    return [age_cap(i) for i in range(len(steps))]


def latch_series(steps):
    cum=0.0;peak=0.0;latch=1.0;prev_new=False
    out=[]
    for i,step in enumerate(steps):
        if i==0:latch=1.0
        elif prev_new:latch=1.0
        else:
            target=GENTLE[bucket(max(0.0,peak-cum))]
            if target<latch:latch=target
        out.append(latch)
        nc=cum+step
        prev_new=nc>peak+EPS
        if prev_new:peak=nc
        cum=nc
    return out


def e_stats(steps,k):
    if len(steps)<k:return None
    s=steps[:k];cum=0.0;path=0.0;peak=0.0;nh=0
    for x in s:
        cum+=x;path+=abs(x)
        if cum>peak+EPS:
            peak=cum;nh+=1
    return {'cum':cum,'dir_eff':cum/path if path>EPS else math.nan,'new_high_rate':nh/k}


def earned_tiers(steps):
    e5=e_stats(steps,5); e10=e_stats(steps,10)
    tier1=False;tier2=False
    if e5 and e5['cum']>=0.5 and math.isfinite(e5['dir_eff']) and e5['dir_eff']>=0.50:
        tier1=True
    if tier1 and e10 and e10['cum']>=1.0 and math.isfinite(e10['dir_eff']) and e10['dir_eff']>=0.50 and e10['new_high_rate']>=0.50:
        tier2=True
    return tier1,tier2,e5,e10


def exposure_series(policy,steps):
    caps=persistence_caps(steps); latch=latch_series(steps)
    t1,t2,e5,e10=earned_tiers(steps)
    exp=[]; bonus=[]
    for i,(cap,health) in enumerate(zip(caps,latch)):
        base=min(cap,health)
        b=0.0
        if health>=1.0-EPS:
            if policy in ('b1_e5_bonus','b2_e5_e10_bonus') and t1 and i>=5:
                b+=0.25
            if policy=='b2_e5_e10_bonus' and t2 and i>=10:
                b+=0.25
        limit=1.0 if policy=='b0_persistence_gentle' else (1.25 if policy=='b1_e5_bonus' else 1.50)
        total=min(limit,base+b)
        exp.append(total);bonus.append(max(0.0,total-base))
    return exp,bonus,t1,t2,e5,e10


def simulate_episode(ep):
    ticker,stage,eid,rows=ep;steps=steps_entry_atr(stage,rows)
    c=0.0;mfe=0.0
    for x in steps:c+=x;mfe=max(mfe,c)
    label='Failed' if mfe<4 else ('Large' if mfe>=8 else 'Middle')
    out=[]
    for policy in POLICIES:
        exp,bonus,t1,t2,e5,e10=exposure_series(policy,steps)
        weighted=[e*x for e,x in zip(exp,steps)]
        changes=[exp[0]]+[exp[i]-exp[i-1] for i in range(1,len(exp))]+[-exp[-1]] if exp else []
        out.append({
            'ticker':ticker,'stage_name':TREND[stage],'episode_id':eid,'start_time':rows[0]['event_time'],
            'bars':len(steps),'mfe':mfe,'label':label,'policy':policy,
            'gross_return':sum(weighted),'turnover':sum(abs(x) for x in changes),'step_returns':weighted,
            'avg_exposure':statistics.fmean(exp),'max_exposure':max(exp),
            'bonus_earned_e5':1.0 if t1 and policy!='b0_persistence_gentle' else 0.0,
            'bonus_earned_e10':1.0 if t2 and policy=='b2_e5_e10_bonus' else 0.0,
            'bonus_active_frac':statistics.fmean(1.0 if x>EPS else 0.0 for x in bonus),
            'avg_bonus':statistics.fmean(bonus),
            'e5_cum': e5['cum'] if e5 else math.nan,
            'e5_dir_eff': e5['dir_eff'] if e5 else math.nan,
            'e10_cum': e10['cum'] if e10 else math.nan,
            'e10_dir_eff': e10['dir_eff'] if e10 else math.nan,
            'e10_new_high_rate': e10['new_high_rate'] if e10 else math.nan,
        })
    return out


def finite(vals):return [x for x in vals if isinstance(x,(int,float)) and math.isfinite(x)]
def fmean(vals):
    x=finite(vals);return statistics.fmean(x) if x else math.nan

def pf(vals):
    pos=sum(x for x in vals if x>0);neg=-sum(x for x in vals if x<0)
    return pos/neg if neg>0 else (math.inf if pos>0 else math.nan)

def mdd(step_returns):
    eq=peak=dd=0.0
    for x in step_returns:eq+=x;peak=max(peak,eq);dd=max(dd,peak-eq)
    return dd

def quantile(vals,q):
    x=sorted(vals)
    if not x:return math.nan
    if len(x)==1:return x[0]
    p=(len(x)-1)*q;lo=math.floor(p);hi=math.ceil(p)
    if lo==hi:return x[lo]
    w=p-lo;return x[lo]*(1-w)+x[hi]*w


def summarize_market(records):
    by=defaultdict(list)
    for r in records:by[(r['policy'],r['ticker'])].append(r)
    out=[]
    for (policy,ticker),g in sorted(by.items()):
        g.sort(key=lambda r:r['start_time'])
        rets=[r['gross_return'] for r in g]; path=[x for r in g for x in r['step_returns']]
        turn=sum(r['turnover'] for r in g);gross=sum(rets)
        row={'policy':policy,'ticker':ticker,'n':len(g),'mean_episode_return':statistics.fmean(rets),
             'median_episode_return':statistics.median(rets),'profit_factor':pf(rets),'cumulative_return':gross,
             'max_drawdown':mdd(path),'turnover_per_episode':turn/len(g),'avg_exposure':statistics.fmean(r['avg_exposure'] for r in g),
             'max_exposure':max(r['max_exposure'] for r in g),'bonus_earned_e5':statistics.fmean(r['bonus_earned_e5'] for r in g),
             'bonus_earned_e10':statistics.fmean(r['bonus_earned_e10'] for r in g),'bonus_active_frac':statistics.fmean(r['bonus_active_frac'] for r in g),
             'avg_bonus':statistics.fmean(r['avg_bonus'] for r in g),'break_even_friction':gross/turn if gross>0 and turn>0 else math.nan}
        for fr in FRICTIONS:
            row[f'net_mean_friction_{fr:.2f}']=(gross-fr*turn)/len(g)
            row[f'net_cum_friction_{fr:.2f}']=gross-fr*turn
        out.append(row)
    return out


def bootstrap95(records,policy):
    by=defaultdict(list)
    for r in records:
        if r['policy']==policy:by[r['ticker']].append(r['gross_return'])
    rng=random.Random(BOOTSTRAP_SEED);sims=[]
    for _ in range(BOOTSTRAP_REPS):
        mm=[]
        for t in sorted(by):
            vals=by[t];sample=[vals[rng.randrange(len(vals))] for _ in vals];mm.append(statistics.fmean(sample))
        sims.append(statistics.fmean(mm))
    return quantile(sims,.025),quantile(sims,.975)


def summarize_universal(records):
    mr=summarize_market(records);by=defaultdict(list)
    for r in mr:by[r['policy']].append(r)
    out=[]
    for policy,g in sorted(by.items()):
        means=[r['mean_episode_return'] for r in g];loo=[statistics.fmean(means[:i]+means[i+1:]) for i in range(len(means))]
        lo,hi=bootstrap95(records,policy);mdds=[r['max_drawdown'] for r in g]
        row={'policy':policy,'markets':len(g),'episodes':sum(r['n'] for r in g),'eq_market_mean_episode_return':statistics.fmean(means),
             'positive_mean_markets':sum(x>0 for x in means),'eq_market_median_profit_factor':statistics.median([r['profit_factor'] for r in g]),
             'eq_market_mean_max_drawdown':statistics.fmean(mdds),'return_per_mdd':statistics.fmean(means)/statistics.fmean(mdds),
             'eq_market_turnover_per_episode':statistics.fmean(r['turnover_per_episode'] for r in g),'eq_market_avg_exposure':statistics.fmean(r['avg_exposure'] for r in g),
             'eq_market_bonus_earned_e5':statistics.fmean(r['bonus_earned_e5'] for r in g),'eq_market_bonus_earned_e10':statistics.fmean(r['bonus_earned_e10'] for r in g),
             'eq_market_bonus_active_frac':statistics.fmean(r['bonus_active_frac'] for r in g),'eq_market_avg_bonus':statistics.fmean(r['avg_bonus'] for r in g),
             'bootstrap95_lo':lo,'bootstrap95_hi':hi,'loo_min_eq_mean':min(loo),'loo_positive_count':sum(x>0 for x in loo)}
        for fr in FRICTIONS:
            row[f'eq_market_net_mean_friction_{fr:.2f}']=statistics.fmean(r[f'net_mean_friction_{fr:.2f}'] for r in g)
            row[f'positive_markets_friction_{fr:.2f}']=sum(r[f'net_cum_friction_{fr:.2f}']>0 for r in g)
        out.append(row)
    return mr,out


def slice_summary(records,key,values):
    out=[]
    for v in values:
        subset=[r for r in records if r[key]==v]
        mr=summarize_market(subset);by=defaultdict(list)
        for r in mr:by[r['policy']].append(r)
        for policy,g in sorted(by.items()):
            out.append({key:v,'policy':policy,'markets':len(g),'episodes':sum(r['n'] for r in g),
                        'eq_market_mean_episode_return':statistics.fmean(r['mean_episode_return'] for r in g),
                        'positive_mean_markets':sum(r['mean_episode_return']>0 for r in g),
                        'eq_market_median_profit_factor':statistics.median(r['profit_factor'] for r in g),
                        'eq_market_mean_max_drawdown':statistics.fmean(r['max_drawdown'] for r in g),
                        'eq_market_avg_exposure':statistics.fmean(r['avg_exposure'] for r in g),
                        'eq_market_avg_bonus':statistics.fmean(r['avg_bonus'] for r in g)})
    return out


def temporal(records):
    out=[]
    for era,start,end in ERAS:
        sub=[]
        for r in records:
            when=dt.datetime.fromtimestamp(r['start_time']/1000,dt.timezone.utc)
            if start<=when<end:sub.append(r)
        mr=summarize_market(sub);by=defaultdict(list)
        for r in mr:by[r['policy']].append(r)
        for policy,g in sorted(by.items()):
            out.append({'era':era,'policy':policy,'markets':len(g),'episodes':sum(r['n'] for r in g),
                        'eq_market_mean_episode_return':statistics.fmean(r['mean_episode_return'] for r in g),
                        'positive_mean_markets':sum(r['mean_episode_return']>0 for r in g),
                        'eq_market_median_profit_factor':statistics.median(r['profit_factor'] for r in g),
                        'eq_market_mean_max_drawdown':statistics.fmean(r['max_drawdown'] for r in g)})
    return out


def decomposition(records):
    rows=slice_summary(records,'label',['Failed','Middle','Large'])
    lookup={(r['label'],r['policy']):r for r in rows};b0L=lookup[('Large','b0_persistence_gentle')]['eq_market_mean_episode_return'];b0F=lookup[('Failed','b0_persistence_gentle')]['eq_market_mean_episode_return']
    for r in rows:
        if r['label']=='Large':
            r['vs_b0_delta']=r['eq_market_mean_episode_return']-b0L;r['vs_b0_ratio']=r['eq_market_mean_episode_return']/b0L
        elif r['label']=='Failed':
            r['vs_b0_delta']=r['eq_market_mean_episode_return']-b0F;r['vs_b0_ratio']=abs(r['eq_market_mean_episode_return'])/abs(b0F)
        else:r['vs_b0_delta']=math.nan;r['vs_b0_ratio']=math.nan
    return rows


def write_csv(path,rows):
    if not rows:return
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('inputs',nargs='+');ap.add_argument('--output-dir',required=True);a=ap.parse_args()
    ev=read_events(a.inputs);eps=episodes(ev)
    if len(ev)!=68118:raise SystemExit(f'event count drift: {len(ev)}')
    if len(eps)!=1624:raise SystemExit(f'episode count drift: {len(eps)}')
    rec=[r for ep in eps for r in simulate_episode(ep)]
    market,univ=summarize_universal(rec);direc=slice_summary(rec,'stage_name',['Markup','Markdown']);temp=temporal(rec);decomp=decomposition(rec)
    out=Path(a.output_dir)
    write_csv(out/'issue87-bonus-overlay-per-market.csv',market);write_csv(out/'issue87-bonus-overlay-universal.csv',univ)
    write_csv(out/'issue87-bonus-overlay-direction.csv',direc);write_csv(out/'issue87-bonus-overlay-temporal.csv',temp);write_csv(out/'issue87-bonus-overlay-decomposition.csv',decomp)
    print('events',len(ev),'episodes',len(eps))
    for r in univ:
        print(r['policy'],f"mean={r['eq_market_mean_episode_return']:+.4f}",f"pos={r['positive_mean_markets']}/9",f"pf={r['eq_market_median_profit_factor']:.3f}",f"mdd={r['eq_market_mean_max_drawdown']:.2f}",f"rpmdd={r['return_per_mdd']:.6f}",f"bonus={r['eq_market_avg_bonus']:.3f}")
    print('DECOMP')
    for r in decomp:print(r['label'],r['policy'],f"ret={r['eq_market_mean_episode_return']:+.3f}",f"vs={r['vs_b0_delta']:+.3f}",f"ratio={r['vs_b0_ratio']:.3f}" if math.isfinite(r['vs_b0_ratio']) else '')

if __name__=='__main__':main()
