from __future__ import annotations
import csv, glob, math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

MARKER='ISSUE76|schema=1'
EXPECTED_EVENTS=68118
EXPECTED_EPISODES=1624
LOOKBACK=5
RULES=('R1_CloseExtreme','R2_PriceExtreme','R3_RetestStructure','R4_Progress05')

def parse_marker(text):
    p=text.find(MARKER)
    if p<0:return None
    out={}
    for tok in text[p:].strip().split('|'):
        if '=' in tok:
            k,v=tok.split('=',1);out[k]=v
    return out

def read_events(paths):
    d={}
    for path in paths:
        with open(path,encoding='utf-8-sig',newline='') as fh:
            for row in csv.reader(fh):
                f=None
                for cell in row:
                    f=parse_marker(cell)
                    if f:break
                if not f:continue
                r={'ticker':f['ticker'],'repr':f['repr'],'event_time':int(f['event_time']),'event_bar':int(f['event_bar']),
                   'stage':int(f['stage']),'fresh':int(f['fresh']),'scale':float(f['scale']),
                   'move1':float(f['move1']),'mfe1':float(f['mfe1']),'mae1':float(f['mae1'])}
                d[(r['ticker'],r['event_time'],r['event_bar'])]=r
    return sorted(d.values(),key=lambda r:(r['ticker'],r['event_bar']))

def era_name(ms):
    y=datetime.fromtimestamp(ms/1000,tz=timezone.utc).year
    if 2010<=y<=2014:return '2010-2014'
    if 2015<=y<=2019:return '2015-2019'
    if 2020<=y<=2026:return '2020-2026'
    return 'pre-2010' if y<2010 else 'other'

def reconstruct(events):
    by=defaultdict(list)
    for e in events:by[e['ticker']].append(e)
    frames={};errs=[]
    for ticker,g in by.items():
        g=sorted(g,key=lambda r:r['event_bar']);rows=[];c=0.0
        for i,e in enumerate(g):
            if i==0 or e['event_bar']!=g[i-1]['event_bar']+1:
                c=0.0;rows.append({**e,'close_coord':c,'high_coord':math.nan,'low_coord':math.nan});continue
            prev=g[i-1];pc=rows[-1]['close_coord']
            c=pc+prev['move1'];h=pc+prev['mfe1'];l=pc+prev['mae1']
            rows.append({**e,'close_coord':c,'high_coord':h,'low_coord':l})
            errs.extend([abs((c-pc)-prev['move1']),abs((h-pc)-prev['mfe1']),abs((l-pc)-prev['mae1'])])
        frames[ticker]=pd.DataFrame(rows)
    return frames,max(errs) if errs else math.nan

def build_episodes(frames):
    out=[]
    for ticker,df in frames.items():
        recs=df.to_dict('records');i=0;eid=0
        while i<len(recs):
            st=recs[i]['stage']
            if st in (2,5) and recs[i]['fresh']==1:
                j=i+1
                while j<len(recs) and recs[j]['stage']==st and recs[j]['event_bar']==recs[j-1]['event_bar']+1:j+=1
                if j<len(recs):out.append((ticker,st,eid,i,recs[i:j]));eid+=1
                i=j
            else:i+=1
    return out

def raw_scale(row):return row['scale']*(100.0 if row['repr']=='YIELD_LEVEL' else 1.0)

def build_candidates(frames,eps):
    candidates=[];stats=defaultdict(int)
    for ticker,st,eid,start,ep in eps:
        if len(ep)<7:stats['too_short']+=1;continue
        df=frames[ticker];direction=1 if st==2 else -1;found=False
        for lt in range(6,len(ep)):
            gi=start+lt;pre=df.iloc[gi-LOOKBACK:gi];cur=df.iloc[gi]
            if len(pre)!=LOOKBACK or pre[['high_coord','low_coord']].isna().any().any() or pd.isna(cur.high_coord) or pd.isna(cur.low_coord):continue
            bh=float(pre.high_coord.max());bl=float(pre.low_coord.min())
            if not bh>bl:continue
            c=float(cur.close_coord)
            if not(c>bh if direction==1 else c<bl):continue
            sc=raw_scale(df.iloc[gi-1])
            if not(math.isfinite(sc) and sc>0):continue
            found=True;stats['breakouts']+=1
            rem=len(ep)-1-lt
            if rem<3:stats['b3_ineligible']+=1;break
            early=df.iloc[gi+1:gi+4]
            if len(early)!=3 or early[['close_coord','high_coord','low_coord']].isna().any().any():stats['b3_missing']+=1;break
            closes=early.close_coord.to_numpy(float);highs=early.high_coord.to_numpy(float);lows=early.low_coord.to_numpy(float)
            if direction==1:
                touch=lows<=bh;reentry=closes<=bh;final_out=closes[-1]>bh
            else:
                touch=highs>=bl;reentry=closes>=bl;final_out=closes[-1]<bl
            any_touch=bool(touch.any());any_re=bool(reentry.any())
            if not any_touch:path='P0_NoTouch'
            elif not any_re:path='P1_WickHold'
            elif final_out:path='P2_Reclaim'
            else:path='P3_FailedAcceptance'
            if path not in ('P1_WickHold','P2_Reclaim'):
                stats[path]+=1;break
            first_touch=int(np.where(touch)[0][0])+1
            t3_idx=gi+3;t3_close=float(df.iloc[t3_idx].close_coord)
            retest_start=gi+first_touch
            known_window=df.iloc[gi:t3_idx+1]
            retest_seg=df.iloc[retest_start:t3_idx+1]
            if direction==1:
                close_anchor=float(known_window.close_coord.max());price_anchor=float(known_window.high_coord.max())
                retest_anchor=float(retest_seg.high_coord.max());progress_anchor=t3_close+0.5*sc
            else:
                close_anchor=float(known_window.close_coord.min());price_anchor=float(known_window.low_coord.min())
                retest_anchor=float(retest_seg.low_coord.min());progress_anchor=t3_close-0.5*sc
            candidates.append({'ticker':ticker,'stage':'Markup' if st==2 else 'Markdown','era':era_name(ep[0]['event_time']),
                               'episode_id':eid,'path':path,'entry_time':ep[0]['event_time'],'break_time':int(cur.event_time),
                               'direction':direction,'scale':sc,'box_high':bh,'box_low':bl,'break_global_idx':gi,'t3_global_idx':t3_idx,
                               'episode_start_idx':start,'episode_len':len(ep),'t3_local_idx':lt+3,'t3_close':t3_close,
                               'close_anchor':close_anchor,'price_anchor':price_anchor,'retest_anchor':retest_anchor,
                               'progress_anchor':progress_anchor,'first_touch_bar':first_touch})
            stats[path]+=1;break
        if not found:stats['no_breakout']+=1
    return pd.DataFrame(candidates),dict(stats)

def rule_trigger(rule,row,df,ep_end_idx):
    direction=int(row.direction);start=int(row.t3_global_idx)+1
    for idx in range(start,ep_end_idx+1):
        r=df.iloc[idx];c=float(r.close_coord);h=float(r.high_coord);l=float(r.low_coord)
        hit=False
        if rule=='R1_CloseExtreme':hit=c>row.close_anchor if direction==1 else c<row.close_anchor
        elif rule=='R2_PriceExtreme':hit=h>row.price_anchor if direction==1 else l<row.price_anchor
        elif rule=='R3_RetestStructure':hit=c>row.retest_anchor if direction==1 else c<row.retest_anchor
        elif rule=='R4_Progress05':hit=c>=row.progress_anchor if direction==1 else c<=row.progress_anchor
        if hit:return idx
    return None

def evaluate(frames,candidates):
    rows=[]
    for _,r in candidates.iterrows():
        df=frames[r.ticker];ep_start=int(r.episode_start_idx);ep_end=ep_start+int(r.episode_len)-1
        direction=int(r.direction);scale=float(r.scale);t3=int(r.t3_global_idx);t3_close=float(r.t3_close)
        ep_future=df.iloc[t3:ep_end+1]
        if direction==1:
            best_future_close=float(ep_future.close_coord.max());available=max(0.0,best_future_close-t3_close)
        else:
            best_future_close=float(ep_future.close_coord.min());available=max(0.0,t3_close-best_future_close)
        for rule in RULES:
            trig=rule_trigger(rule,r,df,ep_end)
            base={'ticker':r.ticker,'stage':r.stage,'era':r.era,'episode_id':int(r.episode_id),'path':r.path,'rule':rule,
                  'triggered':int(trig is not None)}
            if trig is None:
                rows.append({**base,'delay':math.nan,'trigger_close_progress_atr':math.nan,'trigger_intrabar_progress_atr':math.nan,
                             'tax_fraction':math.nan,'remaining_life':math.nan,'remaining10':math.nan,'remaining20':math.nan,
                             'reexpand5':math.nan,'reexpand10':math.nan,'oldbox_fail3':math.nan})
                continue
            tr=df.iloc[trig];tc=float(tr.close_coord);th=float(tr.high_coord);tl=float(tr.low_coord)
            delay=trig-t3;remaining=ep_end-trig
            close_prog=max(0.0,direction*(tc-t3_close))/scale
            intrabar_prog=max(0.0,(th-t3_close) if direction==1 else (t3_close-tl))/scale
            tax=(max(0.0,direction*(tc-t3_close))/available) if available>1e-15 else math.nan
            f3=df.iloc[trig+1:min(trig+4,ep_end+1)]
            f5=df.iloc[trig+1:min(trig+6,ep_end+1)]
            f10=df.iloc[trig+1:min(trig+11,ep_end+1)]
            known=df.iloc[int(r.break_global_idx):trig+1]
            if direction==1:
                known_best=float(known.high_coord.max())
                rex5=int(len(f5)==5 and float(f5.high_coord.max())>known_best+1e-12) if len(f5)==5 else math.nan
                rex10=int(len(f10)==10 and float(f10.high_coord.max())>known_best+1e-12) if len(f10)==10 else math.nan
                fail3=int(len(f3)>0 and np.any(f3.close_coord.to_numpy(float)<=float(r.box_high))) if len(f3)>0 else math.nan
            else:
                known_best=float(known.low_coord.min())
                rex5=int(len(f5)==5 and float(f5.low_coord.min())<known_best-1e-12) if len(f5)==5 else math.nan
                rex10=int(len(f10)==10 and float(f10.low_coord.min())<known_best-1e-12) if len(f10)==10 else math.nan
                fail3=int(len(f3)>0 and np.any(f3.close_coord.to_numpy(float)>=float(r.box_low))) if len(f3)>0 else math.nan
            rows.append({**base,'delay':delay,'trigger_close_progress_atr':close_prog,'trigger_intrabar_progress_atr':intrabar_prog,
                         'tax_fraction':tax,'remaining_life':remaining,'remaining10':int(remaining>=10),'remaining20':int(remaining>=20),
                         'reexpand5':rex5,'reexpand10':rex10,'oldbox_fail3':fail3})
    return pd.DataFrame(rows)

def summary(events,group_cols):
    rows=[]
    for keys,g in events.groupby(group_cols):
        if not isinstance(keys,tuple):keys=(keys,)
        row=dict(zip(group_cols,keys));row['n']=g.episode_id.nunique();row['trigger_rate']=g.triggered.mean();row['no_trigger_rate']=1-row['trigger_rate']
        t=g[g.triggered==1]
        row['triggered_n']=len(t)
        row['delay_median']=t.delay.median();row['delay_mean']=t.delay.mean()
        for n in (3,5,10):row[f'trigger_le_{n}_rate_all']=((g.triggered==1)&(g.delay<=n)).mean()
        row['close_progress_atr_mean']=t.trigger_close_progress_atr.mean();row['intrabar_progress_atr_mean']=t.trigger_intrabar_progress_atr.mean()
        row['tax_fraction_median']=t.tax_fraction.median();row['tax_fraction_mean']=t.tax_fraction.mean()
        row['remaining_life_mean']=t.remaining_life.mean();row['remaining10_rate']=t.remaining10.mean();row['remaining20_rate']=t.remaining20.mean()
        row['reexpand5_rate']=t.reexpand5.mean();row['reexpand10_rate']=t.reexpand10.mean();row['oldbox_fail3_rate']=t.oldbox_fail3.mean()
        rows.append(row)
    return pd.DataFrame(rows)

def equal_market(events,extra_cols=()):
    market=summary(events,[*extra_cols,'ticker','rule'])
    rows=[]
    grp=[*extra_cols,'rule']
    for keys,g in market.groupby(grp):
        if not isinstance(keys,tuple):keys=(keys,)
        row=dict(zip(grp,keys));row['markets']=g.ticker.nunique();row['pooled_n']=int(g.n.sum())
        for col in ['trigger_rate','no_trigger_rate','delay_median','delay_mean','trigger_le_3_rate_all','trigger_le_5_rate_all','trigger_le_10_rate_all',
                    'close_progress_atr_mean','intrabar_progress_atr_mean','tax_fraction_median','tax_fraction_mean','remaining_life_mean','remaining10_rate','remaining20_rate','reexpand5_rate','reexpand10_rate','oldbox_fail3_rate']:
            row[col+'_eq_market']=g[col].mean()
        rows.append(row)
    return market,pd.DataFrame(rows)

def paired(events,a,b):
    rows=[]
    for (ticker,eid,path),g in events[events.rule.isin([a,b])].groupby(['ticker','episode_id','path']):
        ga=g[g.rule==a];gb=g[g.rule==b]
        if len(ga)!=1 or len(gb)!=1 or ga.iloc[0].triggered!=1 or gb.iloc[0].triggered!=1:continue
        ra,rb=ga.iloc[0],gb.iloc[0]
        rows.append({'ticker':ticker,'episode_id':eid,'path':path,'a':a,'b':b,
                     'delay_delta':ra.delay-rb.delay,'tax_delta':ra.tax_fraction-rb.tax_fraction,
                     'remaining_life_delta':ra.remaining_life-rb.remaining_life,
                     'reexpand5_delta':ra.reexpand5-rb.reexpand5 if pd.notna(ra.reexpand5) and pd.notna(rb.reexpand5) else math.nan,
                     'reexpand10_delta':ra.reexpand10-rb.reexpand10 if pd.notna(ra.reexpand10) and pd.notna(rb.reexpand10) else math.nan,
                     'oldbox_fail3_delta':ra.oldbox_fail3-rb.oldbox_fail3 if pd.notna(ra.oldbox_fail3) and pd.notna(rb.oldbox_fail3) else math.nan})
    d=pd.DataFrame(rows)
    if d.empty:return d,pd.DataFrame()
    mr=[]
    for ticker,g in d.groupby('ticker'):
        mr.append({'ticker':ticker,'n':len(g),**{c:g[c].mean() for c in ['delay_delta','tax_delta','remaining_life_delta','reexpand5_delta','reexpand10_delta','oldbox_fail3_delta']}})
    m=pd.DataFrame(mr)
    u={'a':a,'b':b,'markets':m.ticker.nunique(),'paired_n':len(d)}
    for c in ['delay_delta','tax_delta','remaining_life_delta','reexpand5_delta','reexpand10_delta','oldbox_fail3_delta']:
        u[c+'_eq_market']=m[c].mean()
    return d,pd.DataFrame([u])

def main():
    paths=sorted(glob.glob('/mnt/data/pine-logs-#76 Forward Logger*.csv'))
    ev=read_events(paths);assert len(ev)==EXPECTED_EVENTS,len(ev)
    frames,err=reconstruct(ev);eps=build_episodes(frames);assert len(eps)==EXPECTED_EPISODES,len(eps)
    cand,stats=build_candidates(frames,eps);assert len(cand)==236
    events=evaluate(frames,cand)
    out=Path('/mnt/data/issue78-resume-trigger-stage1');out.mkdir(exist_ok=True)
    events.to_csv(out/'issue78-resume-trigger-stage1-events.csv',index=False)
    cand.to_csv(out/'issue78-resume-trigger-stage1-candidates.csv',index=False)
    m,u=equal_market(events);m.to_csv(out/'issue78-resume-trigger-stage1-per-market.csv',index=False);u.to_csv(out/'issue78-resume-trigger-stage1-universal.csv',index=False)
    for extra,label in [(('path',),'by-path'),(('era',),'temporal'),(('stage',),'direction')]:
        mm,uu=equal_market(events,extra);mm.to_csv(out/f'issue78-resume-trigger-stage1-{label}-per-market.csv',index=False);uu.to_csv(out/f'issue78-resume-trigger-stage1-{label}.csv',index=False)
    paired_us=[]
    for a,b in [('R3_RetestStructure','R1_CloseExtreme'),('R2_PriceExtreme','R1_CloseExtreme'),('R4_Progress05','R3_RetestStructure')]:
        d,uu=paired(events,a,b);d.to_csv(out/f'issue78-resume-trigger-stage1-paired-{a}-vs-{b}.csv',index=False);paired_us.append(uu)
    pd.concat(paired_us,ignore_index=True).to_csv(out/'issue78-resume-trigger-stage1-paired-universal.csv',index=False)
    print('events',len(ev),'episodes',len(eps),'candidates',len(cand),'reconstruction_error',err,'stats',stats)

if __name__=='__main__':main()
