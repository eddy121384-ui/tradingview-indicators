# Issue #57 — Transition Health online-state parity

**PASS_EXACT_ONLINE_TO_FROZEN_RESEARCH_PARITY**

- Frozen checkpoint: **+3 bars**.
- Pairs checked: **12**.
- Research-eligible +3 labels checked: **195**.
- Live-tail labels intentionally outside retrospective parity window: **4**.
- Online implementation is compared bar-for-bar with the previously frozen retrospective extractor wherever the original research had a complete 20-bar future window.

## used_research_fx

| Pair | Handoff | Healthy | Damaged | +3 labels | Tail live | Exact |
|---|---:|---:|---:|---:|---:|---|
| EURUSD | 15 | 8 | 5 | 13 | 0 | PASS |
| USDJPY | 18 | 7 | 11 | 18 | 0 | PASS |
| GBPUSD | 19 | 6 | 9 | 15 | 0 | PASS |
| AUDUSD | 20 | 12 | 6 | 18 | 0 | PASS |
| EURCHF | 15 | 9 | 6 | 14 | 1 | PASS |
| USDCAD | 21 | 14 | 7 | 21 | 0 | PASS |
| USDCHF | 21 | 9 | 7 | 15 | 1 | PASS |

## independent_oos_fx

| Pair | Handoff | Healthy | Damaged | +3 labels | Tail live | Exact |
|---|---:|---:|---:|---:|---:|---|
| NZDUSD | 21 | 8 | 12 | 19 | 1 | PASS |
| EURGBP | 10 | 3 | 4 | 7 | 0 | PASS |
| GBPJPY | 27 | 15 | 8 | 23 | 0 | PASS |
| AUDJPY | 20 | 9 | 8 | 16 | 1 | PASS |
| CADJPY | 18 | 11 | 5 | 16 | 0 | PASS |

## Boundary

Engineering parity on the historical research-eligible window only. Live-tail labels are valid real-time outputs but were not part of retrospective research because their 20-bar outcome window was incomplete. No tuning is permitted.
