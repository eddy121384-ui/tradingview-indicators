# Issue #68 Phase B3.15 — Event-Window / Stale-Memory Audit

Status: **diagnostic only / frozen C-2 / no performance use**

Primary engineering gate: **PASS**
- Break final-blocker events: **106**
- mechanically expected from B3.14/B3.10: **106**
- reproduction delta: **0**
- minimum reciprocal population-label agreement: **100.000%**
- reciprocal uncensored timing agreement: **100.000%** (122/122)

## Blocker clock split

- MA already target-side at blocker (`t-1`): **20 / 106 (18.9%)**
- PRE_MA_FLIP_AT_BLOCKER: **86**
- event-related MA flip found: **103**; censored: **3**

## Timing after event-related MA flip

- old range-memory survival: **median=5.0, p75=11.0, max=16, uncensored=36, censored=67**
- target range-evidence delay: **median=1.0, p75=1.0, max=10, uncensored=54, censored=49**
- Break release delay: **median=5.0, p75=9.0, max=16, uncensored=33, censored=70**

## Stale overlap behavior

- stale-overlap bars (`MA target + old range memory`): **452**
- Break still old-negative on stale-overlap bars: **255 (56.4%)**
- Break target-positive on stale-overlap bars: **40**
- Break zero on stale-overlap bars: **157**
- primary stale-population events with at least one old-negative Break overlap: **20 / 20 (100.0%)**
- target range appears before old memory clears: **24 / 30 (80.0%)**

## Per-pair event-window summary

| Pair | Events | MA target @ blocker | Share | Stale overlap bars | Break-old overlap share |
|---|---:|---:|---:|---:|---:|
| EURUSD | 30 | 4 | 13.3% | 103 | 55.3% |
| USDJPY | 21 | 6 | 28.6% | 98 | 65.3% |
| GBPUSD | 29 | 4 | 13.8% | 114 | 50.0% |
| AUDUSD | 26 | 6 | 23.1% | 137 | 56.2% |

## Boundary

Event-window timing attribution only; frozen C-2 and all classifier parameters remain unchanged.

## Preregistered population split

### Primary causal population — MA already target-side at blocker

- events: **20**
- event-related MA flip found / censored: **20 / 0**
- old range-memory survival: **median=11.0, p75=15.0, max=16, uncensored=7, censored=13**
- target range-evidence delay: **median=1.0, p75=2.0, max=5, uncensored=14, censored=6**
- Break release delay: **median=11.0, p75=15.0, max=16, uncensored=7, censored=13**
- stale-overlap bars: **166**
- Break old-negative during overlap: **105 / 166 (63.3%)**
- Break target-positive during overlap: **4**; zero: **57**
- target range before old memory clears: **7 / 7 (100.0%)**
- interpretation boundary: eligible evidence for stale memory after the market has already moved to the new MA side.

### Context population — blocker occurs before MA flip

- events: **86**
- event-related MA flip found / censored: **83 / 3**
- old range-memory survival: **median=3.0, p75=9.0, max=15, uncensored=29, censored=54**
- target range-evidence delay: **median=0.0, p75=1.0, max=10, uncensored=40, censored=43**
- Break release delay: **median=4.5, p75=7.0, max=15, uncensored=26, censored=57**
- stale-overlap bars: **286**
- Break old-negative during overlap: **150 / 286 (52.4%)**
- Break target-positive during overlap: **36**; zero: **100**
- target range before old memory clears: **17 / 23 (73.9%)**
- interpretation boundary: timing context only; these events cannot by themselves prove stale memory after an MA turn.
