#!/usr/bin/env python3
import numpy as np
import pandas as pd
import diagnose_issue68_phase_b312_structure_step_ma_cross as b312

def fixture():
    n=4;z=np.zeros(n);w=.17
    d={"close":np.ones(n),"issue66_b1_ma_log":np.array([1.,1.,-1.,-1.]),"issue66_b1_maturity_ma_log":np.ones(n)}
    d.update({"b38_breakout":np.full(n,3/w),"b38_breakdown":z,"b38_heat_up":z,"b38_panic_dn":z,"b38_structure_up":np.array([0.,0.,50.,50.]),"b38_structure_dn":np.array([100.,100.,50.,50.]),"b38_extension_up":z,"b38_extension_dn":z,"b38_continuation_up":z,"b38_continuation_dn":z,"b38_acc_trace":z,"b38_dist_trace":z})
    direct=np.array([-14.,-14.,3.,3.]);d["b38_markup_raw0"]=50+direct/2;d["b38_markdown_raw0"]=50-direct/2
    return pd.DataFrame(d)

def main():
    assert b312.run_before(np.array([-1.,2.,3.,-1.]),3)==2
    x=b312.audit(fixture(),1,0)
    assert x["handoffs"]==1
    assert x["structure_improves"]==1
    assert x["cross"]["ma50_only"]==1
    assert x["break_pos_prev"]==1
    assert x["break_pos_structure_not_prev"]==1
    assert x["unexplained_improvements"]==0
    print("B3.12 synthetic contracts PASS")
if __name__=="__main__":main()
