#!/usr/bin/env python3
"""Generate Issue #68 B3.16 stale-range release counterfactual TradingView audit."""
from __future__ import annotations
import argparse
from pathlib import Path
import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE=Path(__file__).resolve().parent
DECL='indicator("Chase Risk Radar｜Issue #68 B3.16 Stale-Range Release", shorttitle="ChaseRisk #68 B316", overlay=false, precision=2)'
BODY=r'''
// Issue #68 B3.16 diagnostic shadow only: remove old-direction range-memory source during stale overlap.
groupIssue68B316="Issue #68｜B3.16 Stale-Range Release"
issue68B316Direction=input.string("Bull","審計方向",options=["Bull","Bear"],group=groupIssue68B316)
showIssue68B316Legend=input.bool(true,"顯示右上角狀態表",group=groupIssue68B316)
int issue68B316Dir=issue68B316Direction=="Bull"?1:-1
bool issue68B316Ready=bar_index>=rankLen-1

float issue68B316ObsBreak=issue68B316Dir*0.17*(breakoutScore-explicitBreakdownScore)
float issue68B316Heat=issue68B316Dir*0.17*(heatUp-panicHeatDn)
float issue68B316Structure=issue68B316Dir*0.17*(structureStrong-structureWeak)
float issue68B316Extension=issue68B316Dir*0.2125*(markupExtensionScore-markdownExtensionScore)
float issue68B316Continuation=issue68B316Dir*0.1275*(markupContinuationScore-markdownContinuationScore)
float issue68B316Trace=issue68B316Dir*0.15*(accTraceForMarkup-distTraceForMarkdown)
float issue68B316ObsRaw=issue68B316ObsBreak+issue68B316Heat+issue68B316Structure+issue68B316Extension+issue68B316Continuation+issue68B316Trace

bool issue68B316MaTarget=issue68B316Direction=="Bull"?logPrice>maLog:logPrice<maLog
bool issue68B316OldMem=issue68B316Direction=="Bull"?nz(recentRangeBreakDnStrength,0.0)>0.0:nz(recentRangeBreakUpStrength,0.0)>0.0
bool issue68B316Overlap=issue68B316MaTarget and issue68B316OldMem
float issue68B316TargetRange=issue68B316Direction=="Bull"?breakoutRangeEvidence:breakdownRangeEvidence
float issue68B316TargetMa=issue68B316Direction=="Bull"?breakoutMaEvidence:breakdownMaEvidence
bool issue68B316TargetMode=issue68B316Direction=="Bull"?breakoutModeUp:breakdownModeDn
float issue68B316OldRange=issue68B316Direction=="Bull"?breakdownRangeEvidence:breakoutRangeEvidence
float issue68B316OldMa=issue68B316Direction=="Bull"?breakdownMaEvidence:breakoutMaEvidence
bool issue68B316OldMode=issue68B316Direction=="Bull"?breakdownModeDn:breakoutModeUp
bool issue68B316NewRange=issue68B316TargetRange>0.0
float issue68B316TargetScore=issue68B316TargetMode?100.0:math.max(nz(issue68B316TargetRange,0.0),nz(issue68B316TargetMa,0.0))
float issue68B316ShadowOldRange=issue68B316Overlap?0.0:nz(issue68B316OldRange,0.0)
float issue68B316ShadowOldScore=issue68B316OldMode?100.0:math.max(issue68B316ShadowOldRange,nz(issue68B316OldMa,0.0))
float issue68B316ShadowBreak=0.17*(issue68B316TargetScore-issue68B316ShadowOldScore)
float issue68B316ShadowRaw=issue68B316ObsRaw-issue68B316ObsBreak+issue68B316ShadowBreak
bool issue68B316ReleasedBreak=issue68B316Overlap and issue68B316ObsBreak<0.0 and issue68B316ShadowBreak>0.0
bool issue68B316AdvancedRaw=issue68B316Overlap and issue68B316ObsRaw<=0.0 and issue68B316ShadowRaw>0.0
bool issue68B316Handoff=issue68B316Ready and issue68B316ObsRaw>0 and issue68B316ObsRaw[1]<=0
bool issue68B316Blocker=issue68B316Handoff and issue68B316ObsBreak[1]<=issue68B316Heat[1] and issue68B316ObsBreak[1]<=issue68B316Structure[1] and issue68B316ObsBreak[1]<=issue68B316Extension[1] and issue68B316ObsBreak[1]<=issue68B316Continuation[1] and issue68B316ObsBreak[1]<=issue68B316Trace[1]

f_issue68B316Sign(float x)=>x>0?color.new(colGreen,15):x<0?color.new(colRed,15):color.new(colNeutral,65)
f_issue68B316YN(bool x)=>x?"YES":"NO"
float half=0.34
float c1=8.0,c2=7.0,c3=6.0,c4=5.0,c5=4.0,c6=3.0,c7=2.0,c8=1.0,c9=0.0
p1h=plot(issue68B316Ready?c1+half:na,"B316 OBS BREAK top",color=color.new(colNeutral,100)); p1l=plot(issue68B316Ready?c1-half:na,"B316 OBS BREAK bottom",color=color.new(colNeutral,100))
p2h=plot(issue68B316Ready?c2+half:na,"B316 SHADOW BREAK top",color=color.new(colNeutral,100)); p2l=plot(issue68B316Ready?c2-half:na,"B316 SHADOW BREAK bottom",color=color.new(colNeutral,100))
p3h=plot(issue68B316Ready?c3+half:na,"B316 OBS RAW top",color=color.new(colNeutral,100)); p3l=plot(issue68B316Ready?c3-half:na,"B316 OBS RAW bottom",color=color.new(colNeutral,100))
p4h=plot(issue68B316Ready?c4+half:na,"B316 SHADOW RAW top",color=color.new(colNeutral,100)); p4l=plot(issue68B316Ready?c4-half:na,"B316 SHADOW RAW bottom",color=color.new(colNeutral,100))
p5h=plot(issue68B316Ready?c5+half:na,"B316 STALE OVERLAP top",color=color.new(colNeutral,100)); p5l=plot(issue68B316Ready?c5-half:na,"B316 STALE OVERLAP bottom",color=color.new(colNeutral,100))
p6h=plot(issue68B316Ready?c6+half:na,"B316 NEW RANGE top",color=color.new(colNeutral,100)); p6l=plot(issue68B316Ready?c6-half:na,"B316 NEW RANGE bottom",color=color.new(colNeutral,100))
p7h=plot(issue68B316Ready?c7+half:na,"B316 BREAK RELEASE top",color=color.new(colNeutral,100)); p7l=plot(issue68B316Ready?c7-half:na,"B316 BREAK RELEASE bottom",color=color.new(colNeutral,100))
p8h=plot(issue68B316Ready?c8+half:na,"B316 RAW ADVANCE top",color=color.new(colNeutral,100)); p8l=plot(issue68B316Ready?c8-half:na,"B316 RAW ADVANCE bottom",color=color.new(colNeutral,100))
p9h=plot(issue68B316Ready?c9+half:na,"B316 BREAK BLOCKER top",color=color.new(colNeutral,100)); p9l=plot(issue68B316Ready?c9-half:na,"B316 BREAK BLOCKER bottom",color=color.new(colNeutral,100))
fill(p1h,p1l,color=f_issue68B316Sign(issue68B316ObsBreak),title="B316 OBS BREAK band")
fill(p2h,p2l,color=f_issue68B316Sign(issue68B316ShadowBreak),title="B316 SHADOW BREAK band")
fill(p3h,p3l,color=f_issue68B316Sign(issue68B316ObsRaw),title="B316 OBS RAW band")
fill(p4h,p4l,color=f_issue68B316Sign(issue68B316ShadowRaw),title="B316 SHADOW RAW band")
fill(p5h,p5l,color=issue68B316Overlap?color.new(color.yellow,8):color.new(colNeutral,82),title="B316 STALE OVERLAP band")
fill(p6h,p6l,color=issue68B316NewRange?color.new(colGreen,15):color.new(colRed,15),title="B316 NEW RANGE band")
fill(p7h,p7l,color=issue68B316ReleasedBreak?color.new(color.aqua,0):color.new(colNeutral,82),title="B316 BREAK RELEASE band")
fill(p8h,p8l,color=issue68B316AdvancedRaw?color.new(color.lime,0):color.new(colNeutral,82),title="B316 RAW ADVANCE band")
fill(p9h,p9l,color=issue68B316Blocker?color.new(color.orange,0):color.new(colNeutral,82),title="B316 BREAK FINAL BLOCKER band")

var table issue68B316Legend=table.new(position.top_right,2,10,border_width=1)
if barstate.islast
    if showIssue68B316Legend
        table.cell(issue68B316Legend,0,0,"LAYER",text_color=color.white,bgcolor=color.new(colNeutral,15)); table.cell(issue68B316Legend,1,0,"NOW",text_color=color.white,bgcolor=color.new(colNeutral,15))
        table.cell(issue68B316Legend,0,1,"TARGET",text_color=color.white,bgcolor=color.new(colNeutral,45)); table.cell(issue68B316Legend,1,1,issue68B316Direction,text_color=color.white)
        table.cell(issue68B316Legend,0,2,"STALE OVERLAP",text_color=color.white,bgcolor=color.new(colNeutral,45)); table.cell(issue68B316Legend,1,2,f_issue68B316YN(issue68B316Overlap),text_color=color.white,bgcolor=issue68B316Overlap?color.new(color.yellow,8):color.new(colNeutral,55))
        table.cell(issue68B316Legend,0,3,"OBS BREAK",text_color=color.white,bgcolor=color.new(colNeutral,45)); table.cell(issue68B316Legend,1,3,issue68B316ObsBreak>0?"TARGET":issue68B316ObsBreak<0?"OLD":"ZERO",text_color=color.white,bgcolor=f_issue68B316Sign(issue68B316ObsBreak))
        table.cell(issue68B316Legend,0,4,"SHADOW BREAK",text_color=color.white,bgcolor=color.new(colNeutral,45)); table.cell(issue68B316Legend,1,4,issue68B316ShadowBreak>0?"TARGET":issue68B316ShadowBreak<0?"OLD":"ZERO",text_color=color.white,bgcolor=f_issue68B316Sign(issue68B316ShadowBreak))
        table.cell(issue68B316Legend,0,5,"OBS RAW",text_color=color.white,bgcolor=color.new(colNeutral,45)); table.cell(issue68B316Legend,1,5,issue68B316ObsRaw>0?"TARGET":issue68B316ObsRaw<0?"OLD":"ZERO",text_color=color.white,bgcolor=f_issue68B316Sign(issue68B316ObsRaw))
        table.cell(issue68B316Legend,0,6,"SHADOW RAW",text_color=color.white,bgcolor=color.new(colNeutral,45)); table.cell(issue68B316Legend,1,6,issue68B316ShadowRaw>0?"TARGET":issue68B316ShadowRaw<0?"OLD":"ZERO",text_color=color.white,bgcolor=f_issue68B316Sign(issue68B316ShadowRaw))
        table.cell(issue68B316Legend,0,7,"NEW RANGE",text_color=color.white,bgcolor=color.new(colNeutral,45)); table.cell(issue68B316Legend,1,7,f_issue68B316YN(issue68B316NewRange),text_color=color.white)
        table.cell(issue68B316Legend,0,8,"BREAK RELEASE",text_color=color.white,bgcolor=color.new(colNeutral,45)); table.cell(issue68B316Legend,1,8,f_issue68B316YN(issue68B316ReleasedBreak),text_color=color.white)
        table.cell(issue68B316Legend,0,9,"RAW ADVANCE",text_color=color.white,bgcolor=color.new(colNeutral,45)); table.cell(issue68B316Legend,1,9,f_issue68B316YN(issue68B316AdvancedRaw),text_color=color.white)
    else
        table.clear(issue68B316Legend,0,0,1,9)
plot(issue68B316ObsBreak,"B316 observed weighted Break",display=display.data_window)
plot(issue68B316ShadowBreak,"B316 shadow weighted Break",display=display.data_window)
plot(issue68B316ObsRaw,"B316 observed oriented raw",display=display.data_window)
plot(issue68B316ShadowRaw,"B316 shadow oriented raw",display=display.data_window)
'''.strip()

def generate(source:Path)->str:
    d1=phase_b.d1.generate(source)
    if d1.count(phase_b.D1_EXPORT_MARKER)!=1: raise RuntimeError("expected one D1 export marker")
    core=d1.split(phase_b.D1_EXPORT_MARKER,1)[0].rstrip(); core=replace_once(core,phase_b.D1_INDICATOR_DECL,DECL)
    out=core+"\n\n"+BODY+"\n"
    for token in ("B316 SHADOW BREAK band","B316 SHADOW RAW band","B316 STALE OVERLAP band","B316 BREAK RELEASE band","B316 RAW ADVANCE band"):
        if token not in out: raise RuntimeError(f"missing {token}")
    for token in ("strategy.","D1B|"):
        if token in out: raise RuntimeError(f"forbidden token {token}")
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--source",type=Path,default=HERE/SOURCE_RELATIVE); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    text=generate(a.source); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(text,encoding="utf-8"); print(a.output)
if __name__=="__main__": main()
