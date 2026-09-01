#!/usr/bin/env python3
"""Generate Issue #68 B3.12 Structure / MA-cross visual audit Pine."""
from __future__ import annotations
import argparse
from pathlib import Path
import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE=Path(__file__).resolve().parent
DECL='indicator("Chase Risk Radar｜Issue #68 B3.12 Structure Step", shorttitle="ChaseRisk #68 B312", overlay=false, precision=2)'
BODY=r'''

// Issue #68 B3.12 diagnostic only: existing S2-vs-S5 raw, Break, discrete
// Structure and MA50/MA200 relation timing. No model or strategy change.
groupIssue68B312="Issue #68｜B3.12 Structure Step"
issue68B312Direction=input.string("Bull","審計方向",options=["Bull","Bear"],group=groupIssue68B312)
showIssue68B312Legend=input.bool(true,"顯示右上角狀態表",group=groupIssue68B312)
int issue68B312Dir=issue68B312Direction=="Bull"?1:-1
bool issue68B312Ready=bar_index>=rankLen-1
float issue68B312Break=0.17*(breakoutScore-explicitBreakdownScore)
float issue68B312Heat=0.17*(heatUp-panicHeatDn)
float issue68B312Structure=0.17*(structureStrong-structureWeak)
float issue68B312Extension=0.2125*(markupExtensionScore-markdownExtensionScore)
float issue68B312Continuation=0.1275*(markupContinuationScore-markdownContinuationScore)
float issue68B312Trace=0.15*(accTraceForMarkup-distTraceForMarkdown)
float issue68B312Direct=issue68B312Break+issue68B312Heat+issue68B312Structure+issue68B312Extension+issue68B312Continuation+issue68B312Trace
float issue68B312RawOriented=issue68B312Dir*issue68B312Direct
float issue68B312BreakOriented=issue68B312Dir*issue68B312Break
float issue68B312StructureOriented=issue68B312Dir*issue68B312Structure
bool issue68B312MA50=issue68B312Dir==1?logPrice>maLog:logPrice<maLog
bool issue68B312MA200=issue68B312Dir==1?logPrice>maturityMaLog:logPrice<maturityMaLog
bool issue68B312Handoff=issue68B312Ready and issue68B312RawOriented>0 and issue68B312RawOriented[1]<=0
f_issue68B312Sign(float x)=>not issue68B312Ready?0:x>0?1:x<0?-1:0
f_issue68B312Color(int x)=>x==1?colGreen:x==-1?colRed:colNeutral
f_issue68B312Band(int x)=>color.new(f_issue68B312Color(x),x==0?68:18)
f_issue68B312Text(int x)=>x==1?"TARGET":x==-1?"OLD":"NEUTRAL"
int issue68B312Raw=f_issue68B312Sign(issue68B312RawOriented)
int issue68B312BreakState=f_issue68B312Sign(issue68B312BreakOriented)
int issue68B312StructureState=f_issue68B312Sign(issue68B312StructureOriented)
int issue68B312MA50State=not issue68B312Ready?0:issue68B312MA50?1:-1
int issue68B312MA200State=not issue68B312Ready?0:issue68B312MA200?1:-1
float h=.34
float yRaw=5.,yBreak=4.,yStruct=3.,y50=2.,y200=1.,yHand=0.
p1h=plot(issue68B312Ready?yRaw+h:na,"B312 RAW top",color=color.new(colNeutral,100));p1l=plot(issue68B312Ready?yRaw-h:na,"B312 RAW bottom",color=color.new(colNeutral,100))
p2h=plot(issue68B312Ready?yBreak+h:na,"B312 BREAK top",color=color.new(colNeutral,100));p2l=plot(issue68B312Ready?yBreak-h:na,"B312 BREAK bottom",color=color.new(colNeutral,100))
p3h=plot(issue68B312Ready?yStruct+h:na,"B312 STRUCTURE top",color=color.new(colNeutral,100));p3l=plot(issue68B312Ready?yStruct-h:na,"B312 STRUCTURE bottom",color=color.new(colNeutral,100))
p4h=plot(issue68B312Ready?y50+h:na,"B312 MA50 top",color=color.new(colNeutral,100));p4l=plot(issue68B312Ready?y50-h:na,"B312 MA50 bottom",color=color.new(colNeutral,100))
p5h=plot(issue68B312Ready?y200+h:na,"B312 MA200 top",color=color.new(colNeutral,100));p5l=plot(issue68B312Ready?y200-h:na,"B312 MA200 bottom",color=color.new(colNeutral,100))
p6h=plot(issue68B312Ready?yHand+h:na,"B312 HANDOFF top",color=color.new(colNeutral,100));p6l=plot(issue68B312Ready?yHand-h:na,"B312 HANDOFF bottom",color=color.new(colNeutral,100))
fill(p1h,p1l,color=f_issue68B312Band(issue68B312Raw),title="B312 RAW band")
fill(p2h,p2l,color=f_issue68B312Band(issue68B312BreakState),title="B312 BREAK band")
fill(p3h,p3l,color=f_issue68B312Band(issue68B312StructureState),title="B312 STRUCTURE band")
fill(p4h,p4l,color=f_issue68B312Band(issue68B312MA50State),title="B312 MA50 band")
fill(p5h,p5l,color=f_issue68B312Band(issue68B312MA200State),title="B312 MA200 band")
fill(p6h,p6l,color=issue68B312Handoff?color.new(color.yellow,10):color.new(colNeutral,75),title="B312 HANDOFF band")
var table issue68B312Legend=table.new(position.top_right,2,8,border_width=1)
if barstate.islast
    if showIssue68B312Legend
        table.cell(issue68B312Legend,0,0,"LAYER",text_color=color.white,bgcolor=color.new(colNeutral,15));table.cell(issue68B312Legend,1,0,"NOW",text_color=color.white,bgcolor=color.new(colNeutral,15))
        table.cell(issue68B312Legend,0,1,"TARGET",text_color=color.white,bgcolor=color.new(colNeutral,45));table.cell(issue68B312Legend,1,1,issue68B312Direction,text_color=color.white,bgcolor=color.new(colNeutral,15))
        table.cell(issue68B312Legend,0,2,"RAW",text_color=color.white,bgcolor=color.new(colNeutral,45));table.cell(issue68B312Legend,1,2,f_issue68B312Text(issue68B312Raw),text_color=color.white,bgcolor=f_issue68B312Color(issue68B312Raw))
        table.cell(issue68B312Legend,0,3,"BREAK",text_color=color.white,bgcolor=color.new(colNeutral,45));table.cell(issue68B312Legend,1,3,f_issue68B312Text(issue68B312BreakState),text_color=color.white,bgcolor=f_issue68B312Color(issue68B312BreakState))
        table.cell(issue68B312Legend,0,4,"STRUCTURE",text_color=color.white,bgcolor=color.new(colNeutral,45));table.cell(issue68B312Legend,1,4,f_issue68B312Text(issue68B312StructureState),text_color=color.white,bgcolor=f_issue68B312Color(issue68B312StructureState))
        table.cell(issue68B312Legend,0,5,"MA50",text_color=color.white,bgcolor=color.new(colNeutral,45));table.cell(issue68B312Legend,1,5,issue68B312MA50?"TARGET SIDE":"OLD SIDE",text_color=color.white,bgcolor=f_issue68B312Color(issue68B312MA50State))
        table.cell(issue68B312Legend,0,6,"MA200",text_color=color.white,bgcolor=color.new(colNeutral,45));table.cell(issue68B312Legend,1,6,issue68B312MA200?"TARGET SIDE":"OLD SIDE",text_color=color.white,bgcolor=f_issue68B312Color(issue68B312MA200State))
        table.cell(issue68B312Legend,0,7,"HANDOFF",text_color=color.white,bgcolor=color.new(colNeutral,45));table.cell(issue68B312Legend,1,7,issue68B312Handoff?"NOW":"-",text_color=color.white,bgcolor=issue68B312Handoff?color.new(color.yellow,10):color.new(colNeutral,15))
    else
        table.clear(issue68B312Legend,0,0,1,7)
plot(issue68B312Direct,"B312 S2-S5 raw delta",display=display.data_window)
plot(issue68B312Break,"B312 break edge",display=display.data_window)
plot(issue68B312Structure,"B312 structure edge",display=display.data_window)
'''.strip()

def generate(source:Path)->str:
    text=phase_b.d1.generate(source)
    core=text.split(phase_b.D1_EXPORT_MARKER,1)[0].rstrip()
    core=replace_once(core,phase_b.D1_INDICATOR_DECL,DECL)
    out=core+"\n\n"+BODY+"\n"
    for token in ("B312 RAW band","B312 BREAK band","B312 STRUCTURE band","B312 MA50 band","B312 MA200 band","B312 HANDOFF band"):
        if token not in out:raise RuntimeError(token)
    for token in ("strategy.","issue68B34A","issue68B34B","issue68B34C","D1B|"):
        if token in out:raise RuntimeError(f"forbidden {token}")
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,default=HERE/SOURCE_RELATIVE);p.add_argument("--output",type=Path,required=True);a=p.parse_args();t=generate(a.source);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(t,encoding="utf-8");print(a.output)
if __name__=="__main__":main()
