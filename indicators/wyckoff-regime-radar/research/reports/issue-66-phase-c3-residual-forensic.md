# Issue #66 Phase C-3 — Residual Strong/Formal Mismatch Forensic

Status: **reused frozen data / no PnL / no formula change**

C-2 persistence exact replay: **YES**

Strong-stage mirror: **99.33%** (44 mismatch bars)  
Formal mirror: **99.64%** (24 mismatch bars)  
Candidate-display mirror: **99.64%**

## Residual strong-stage attribution

| Rank | Cause | Mismatch overlap | Share of strong-stage mismatch |
|---:|---|---:|---:|
| 1 | Candidate conflict | 32 | 72.73% |
| 2 | Top-gap threshold | 14 | 31.82% |
| 3 | Top-stage / argmax | 6 | 13.64% |
| 4 | Probability validity | 0 | 0.00% |
| 5 | Dominant threshold | 0 | 0.00% |
| 6 | Evidence threshold | 0 | 0.00% |

Unexplained strong-stage mismatch bars: **0**.

## Stage 1/4 residual conflict predicate forensic

Residual Stage 1/4 conflict mismatch bars with top stage already mirrored: **28**

| Predicate | Mismatch bars |
|---|---:|
| Holding threshold predicate | 27 |
| Exhaustion threshold predicate | 1 |
| Both holding + exhaustion | 0 |
| Inferred continuation-override only | 0 |

Threshold distance on predicate-mismatch bars (existing absorb threshold; descriptive only):

| Margin | Median | P90 | Max |
|---|---:|---:|---:|
| Holding left | 3.802161 | 9.274676 | 10.751699 |
| Holding inverse | 2.892262 | 9.306258 | 12.795640 |
| Exhaustion left | 0.011643 | 0.011643 | 0.011643 |
| Exhaustion inverse | 0.036816 | 0.036816 | 0.036816 |

## Formal residual by pair

| Pair | Mismatch bars | Episodes | Max episode | State-carry share |
|---|---:|---:|---:|---:|
| EURUSD | 0 | 0 | 0 | 0.00% |
| USDJPY | 15 | 4 | 6 | 73.33% |
| GBPUSD | 0 | 0 | 0 | 0.00% |
| AUDUSD | 9 | 6 | 3 | 55.56% |

Aggregate Formal state-carry share: **66.67%**  
Stale-pressure reason mirror: **99.50%**  
Stale-pressure bars mirror: **99.44%**

## Decision boundary

This forensic does not authorize threshold movement. If no explicit non-isomorphic source remains, stop classifier-formula repair and hand off the C-2 core to Phase D Pine↔Python parity.
