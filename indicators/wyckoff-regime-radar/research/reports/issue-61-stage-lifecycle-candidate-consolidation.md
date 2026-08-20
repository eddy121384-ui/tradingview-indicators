# Issue #61 — Candidate Stage 3 / 6 consolidation audit

**Counts/durations only. No price outcomes.**

Formal Stage 3/6 were nearly absent in the base lifecycle. This audit checks whether the existing `candidate_display_id` layer surfaces those consolidation semantics while Formal remains in the matching trend stage.

## Aggregate

| State | Held bars | Candidate bars | Share held | Bars inside matching Formal trend | Runs | Onsets | Onsets while Formal trend | Pairs with any | Median pair run |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Long / Candidate Stage 3 | 1409 | 6 | 0.43% | 4 | 4 | 4 | 3 | 2/4 | 1.0 |
| Short / Candidate Stage 6 | 1378 | 0 | 0.00% | 0 | 0 | 0 | 0 | 0/4 | — |

## Per pair

| Pair | Long held | Cand3 bars | Cand3 share | Cand3 runs | Short held | Cand6 bars | Cand6 share | Cand6 runs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 326 | 0 | 0.00% | 0 | 352 | 0 | 0.00% | 0 |
| USDJPY | 302 | 0 | 0.00% | 0 | 299 | 0 | 0.00% | 0 |
| GBPUSD | 437 | 5 | 1.14% | 3 | 320 | 0 | 0.00% | 0 |
| AUDUSD | 344 | 1 | 0.29% | 1 | 407 | 0 | 0.00% | 0 |

## Boundary

Counts/durations only. No PnL. Candidate layer is existing v0.6 semantics; no new threshold is introduced.
