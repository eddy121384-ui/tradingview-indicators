# Issue #68 Phase B3.11 — Trace Persistence / Decay Audit

Status: **diagnostic only / frozen C-2 / no performance use**

Primary engineering gate: **PASS**
- stale-opposition bars: **1479** / other-five-consensus **2475**
- stale Trace that actually keeps total raw on old side: **0** (0.00% of stale-opposition bars)
- all full-vs-no-Trace sign flips: **122** (blocks target 61, rescues target 61)
- unexplained sign flips: **0**
- stale run length: median **9.0**, p90 **29.10000000000001**, max **87.0** bars
- opposing Trace source age on stale bars: median **28.0**, p90 **47.0**, max **49.0** bars
- exact raw handoffs: **373**; Trace opposed at t-1 **185** (49.6%), at t **184** (49.3%)
- opposing Trace source age at handoff t-1: median **11.0**, p90 **47.599999999999994**, max **49.0** bars
- max six-component reconstruction error: **2.842e-14**
- pooled stale-opposition reciprocal agreement: **99.909%**
- pooled full-vs-no-Trace sign-flip reciprocal agreement: **99.954%**
- minimum reciprocal exact-handoff agreement: **99.818%**

## Per-pair Bull diagnostic

| Pair | Stale bars | Stale blocks raw | Full/no-Trace flips | Handoffs | Trace opposes t-1 |
|---|---:|---:|---:|---:|---:|
| EURUSD | 188 | 0 | 22 | 54 | 19 |
| USDJPY | 129 | 0 | 13 | 49 | 31 |
| GBPUSD | 243 | 0 | 8 | 41 | 23 |
| AUDUSD | 204 | 0 | 18 | 43 | 16 |

## Boundary

Frozen 50-bar rolling-max Trace attribution only; no Trace length/weight/decay/reset or model rule is changed.
