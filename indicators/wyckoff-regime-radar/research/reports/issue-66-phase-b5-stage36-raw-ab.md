# Issue #66 Phase B-5 — Stage 3/6 Raw Symmetry Repair A/B

Status: **reused frozen data / no PnL**

Primary Stage 3/6 raw gate: **PASS**

Only the Re-accumulation / Re-distribution raw fourth component differs from B-3.

| Primary metric | B-3 | B-5 | Gain (lower) |
|---|---:|---:|---:|
| Reacc raw → inverse Redist raw MAE | 4.206546 | 0.070917 | 4.135628 |
| Redist raw → inverse Reacc raw MAE | 4.208487 | 0.066533 | 4.141954 |

## Frozen invariants

Range U→D 100.00%; Range D→U 100.00%  
MA U→D 100.00%; MA D→U 100.00%  
B-2 break + B-3 entry metrics preserved exactly: **YES**

## Downstream observations (not tuning targets)

| Metric | B-3 | B-5 | Symmetry gain |
|---|---:|---:|---:|
| Raw stage-vector MAE | 2.678344 | 1.250358 | 1.427987 lower |
| Gate-vector MAE | 0.020136 | 0.020136 | 0.000000 lower |
| Effective-vector MAE | 1.781622 | 1.775579 | 0.006044 lower |
| Probability-vector MAE | 3.643290 | 3.639760 | 0.003530 lower |
| Candidate mirror | 89.95% | 89.97% | 0.02% |
| Formal mirror | 87.16% | 87.16% | 0.00% |
| Formal transition mirror | 85.41% | 85.41% | 0.00% |

Downstream metrics may not be used to retune B-5.
