# Issue #61 — Phase A fresh-break / Formal-stage timing audit

**Reused-data semantic/timing audit only. No PnL.**

- Engine: Issue #57 frozen v0.6 Phase-B six-stage core
- Fresh break: existing 20-bar rangeBreakUp/rangeBreakDn pulse
- Frozen descriptive horizon: +20 bars.
- Warm-up: model `rank_len - 1` (755 bars under frozen defaults).

## Aggregate

| Side | Fresh breaks | Already in target before break | Need later target confirmation | Target by same bar | by +1 | by +3 | by +5 | by +20 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Bull → Stage 2 | 282 | 104 | 178 | 20 (11.2%) | 28 (15.7%) | 47 (26.4%) | 54 (30.3%) | 82 (46.1%) |
| Bear → Stage 5 | 277 | 94 | 183 | 25 (13.7%) | 45 (24.6%) | 67 (36.6%) | 80 (43.7%) | 95 (51.9%) |

## Stage-onset alignment

| Side | Target onsets | Fresh break same bar | Initial 1→2 / 4→5 | Initial same-bar break | Renewal 3→2 / 6→5 | Renewal same-bar break |
|---|---:|---:|---:|---:|---:|---:|
| Bull | 63 | 20 | 22 | 6 | 2 | 0 |
| Bear | 81 | 25 | 12 | 2 | 0 | 0 |

## Per pair

### EURUSD

| Side | Fresh breaks | Already target | Need confirm | Same bar | +3 | +5 | +20 | Renewal events | Renewal same-bar break |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Bull | 66 | 29 | 37 | 5 | 8 | 8 | 10 | 0 | 0 |
| Bear | 68 | 25 | 43 | 5 | 16 | 18 | 22 | 0 | 0 |

### USDJPY

| Side | Fresh breaks | Already target | Need confirm | Same bar | +3 | +5 | +20 | Renewal events | Renewal same-bar break |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Bull | 75 | 22 | 53 | 5 | 14 | 17 | 30 | 0 | 0 |
| Bear | 57 | 14 | 43 | 9 | 17 | 20 | 23 | 0 | 0 |

### GBPUSD

| Side | Fresh breaks | Already target | Need confirm | Same bar | +3 | +5 | +20 | Renewal events | Renewal same-bar break |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Bull | 71 | 26 | 45 | 7 | 16 | 18 | 26 | 1 | 0 |
| Bear | 76 | 25 | 51 | 3 | 13 | 16 | 19 | 0 | 0 |

### AUDUSD

| Side | Fresh breaks | Already target | Need confirm | Same bar | +3 | +5 | +20 | Renewal events | Renewal same-bar break |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Bull | 70 | 27 | 43 | 3 | 9 | 11 | 16 | 1 | 0 |
| Bear | 76 | 30 | 46 | 8 | 21 | 26 | 31 | 0 | 0 |

## Boundary

Timing/state counts only. All fixtures are reused evidence. No PnL or independent validation claim.
