# Issue #68 Phase B3.10 — S5 vs S2 Local Formula Duel

Status: **diagnostic only / frozen C-2 / no performance use**

Primary engineering gate: **PASS**
- target-losing direction observations: **5388**
- exact raw handoff events: **373**
- max six-component reconstruction error: **2.842e-14**
- minimum reciprocal handoff-event agreement: **99.818%**
- pooled reciprocal final-blocker agreement: **99.730%** (369/370)
- pooled reciprocal handoff-driver agreement: **99.730%** (369/370)
- minimum per-slice final-blocker agreement (diagnostic): **97.561%**
- minimum per-slice handoff-driver agreement (diagnostic): **98.148%**

## Component drag while target fresh trend loses

| Component | Negative-edge share | Cumulative negative edge | Largest-negative count |
|---|---:|---:|---:|
| break | 74.0% | -45643.54 | 2274 |
| heat | 82.3% | -32175.43 | 763 |
| structure | 72.5% | -66419.00 | 2254 |
| extension | 93.3% | -44323.71 | 40 |
| continuation | 88.7% | -26404.35 | 42 |
| trace | 46.2% | -3320.35 | 15 |

## Exact handoff attribution

| Component | Final blocker | Handoff driver |
|---|---:|---:|
| break | 106 | 36 |
| heat | 93 | 38 |
| structure | 140 | 279 |
| extension | 14 | 0 |
| continuation | 14 | 19 |
| trace | 6 | 1 |

## Per-pair Bull handoffs

| Pair | S5-leading bars | S5->S2 handoffs | Top final blocker | Top driver |
|---|---:|---:|---|---|
| EURUSD | 717 | 54 | structure | structure |
| USDJPY | 617 | 49 | heat | structure |
| GBPUSD | 608 | 41 | break | structure |
| AUDUSD | 742 | 43 | structure | structure |

## Boundary

Exact frozen S2-vs-S5 raw duel attribution only; no model or performance rule is changed.
