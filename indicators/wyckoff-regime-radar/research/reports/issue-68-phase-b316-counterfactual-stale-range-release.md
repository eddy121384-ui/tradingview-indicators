# Issue #68 Phase B3.16 — Counterfactual Stale-Range Release

Status: **diagnostic shadow only / frozen C-2 / no performance use**

Primary engineering gate: **PASS**
- Break final-blocker reproduction: **106 / 106** (delta 0)
- strict B3.15 primary reproduction: **20 / 20** (delta 0)
- max Break reconstruction error: **0.000e+00**
- max observed/shadow six-component reconstruction error: **2.842e-14 / 2.842e-14**
- minimum reciprocal shadow-sign agreement: **100.000%**

## Strict primary blocker-bar counterfactual

- shadow Break target-positive: **6 / 20 (30.0%)**
- shadow Break signs: target **6**, neutral **14**, old **0**
- shadow total raw target-positive at `t-1`: **16 / 20 (80.0%)**
- shadow total signs: target **16**, neutral **0**, old **4**

## Lead before observed handoff

- events with any shadow-total target-positive bar from MA flip through `t-1`: **16 / 20**
- lead bars: median **1.0**, p75 **2.0**, max **7**
- reciprocal lead agreement: **100.000%** (16/16)

## Primary event-window overlap accounting

- stale-overlap observations: **55**
- observed Break old-negative observations: **46**
- shadow Break during overlap: target **16**, neutral **39**, old **0**
- NEW RANGE present + observed Break old + shadow Break target: **2**

## Per-pair strict primary summary

| Pair | Primary | Shadow Break + | Shadow raw + @ blocker | Overlap obs | New-range release obs |
|---|---:|---:|---:|---:|---:|
| EURUSD | 4 | 1 | 3 | 8 | 1 |
| USDJPY | 6 | 1 | 4 | 18 | 1 |
| GBPUSD | 4 | 2 | 4 | 19 | 0 |
| AUDUSD | 6 | 2 | 5 | 10 | 0 |

## Boundary

One fixed shadow removes only old-direction range-memory evidence during MA-target stale overlap; production C-2 and parameters unchanged.
