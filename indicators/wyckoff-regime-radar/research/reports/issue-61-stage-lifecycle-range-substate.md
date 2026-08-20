# Issue #61 — Existing rangeScore as Trend Consolidation substate

**Pre-PnL structural audit only.**

The existing v0.6 range gate starts at `rangeScore = 35` and is fully active at `70`. Both are reported as inherited model semantics; neither is selected from returns.

## Aggregate

| Side | Existing level | Held bars | Active bars | Share held | Inside matching Formal trend | Runs | Pairs | Break same/end bar | by +3 | by +5 | by +20 | No break +20 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Long | range_gate_start (≥35) | 1409 | 959 | 68.06% | 954 | 80 | 4/4 | 7 | 21 | 21 | 25 | 55 |
| Long | range_gate_full (≥70) | 1409 | 146 | 10.36% | 146 | 28 | 4/4 | 2 | 4 | 4 | 7 | 21 |
| Short | range_gate_start (≥35) | 1378 | 1066 | 77.36% | 1066 | 84 | 4/4 | 6 | 13 | 14 | 16 | 68 |
| Short | range_gate_full (≥70) | 1378 | 168 | 12.19% | 168 | 42 | 4/4 | 5 | 10 | 10 | 11 | 31 |

## Per pair — range gate start (≥35)

| Pair | Long active share | Long runs | Long break +20 | Short active share | Short runs | Short break +20 |
|---|---:|---:|---:|---:|---:|---:|
| EURUSD | 58.59% | 18 | 10 | 76.14% | 22 | 5 |
| USDJPY | 77.15% | 21 | 3 | 80.60% | 17 | 2 |
| GBPUSD | 75.51% | 24 | 5 | 74.69% | 19 | 4 |
| AUDUSD | 59.59% | 17 | 7 | 78.13% | 26 | 5 |

## Boundary

Existing rangeScore boundaries only; counts/durations/fresh-break timing only. No PnL or threshold selection from returns.
