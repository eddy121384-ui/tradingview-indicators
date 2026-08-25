# Issue #66 Phase B-6 — Stage 1/4 Raw Symmetry Repair A/B

Status: **reused frozen data / no PnL**

Primary Stage 1/4 raw gate: **PASS**

Only the Accumulation / Distribution raw final 10% context differs from B-5.

| Primary metric | B-5 | B-6 | Gain (lower) |
|---|---:|---:|---:|
| Acc raw → inverse Dist raw MAE | 3.566984 | 0.073840 | 3.493144 |
| Dist raw → inverse Acc raw MAE | 3.103473 | 0.071486 | 3.031987 |

## Frozen invariants

Range U→D 100.00%; Range D→U 100.00%  
MA U→D 100.00%; MA D→U 100.00%  
B-2 break + B-3 entry + B-5 Stage3/6 raw metrics preserved exactly: **YES**

## Downstream observations (not tuning targets)

| Metric | B-5 | B-6 | Symmetry gain |
|---|---:|---:|---:|
| Raw stage-vector MAE | 1.250358 | 0.058428 | 1.191930 lower |
| Gate-vector MAE | 0.020136 | 0.020136 | 0.000000 lower |
| Effective-vector MAE | 1.775579 | 1.658936 | 0.116643 lower |
| Probability-vector MAE | 3.639760 | 3.468723 | 0.171037 lower |
| Candidate mirror | 89.97% | 90.78% | 0.81% |
| Formal mirror | 87.16% | 86.99% | -0.17% |
| Formal transition mirror | 85.41% | 85.26% | -0.15% |

Downstream metrics may not be used to retune B-6.
