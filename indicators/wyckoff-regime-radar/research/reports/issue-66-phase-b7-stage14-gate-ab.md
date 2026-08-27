# Issue #66 Phase B-7 — Stage 1/4 Gate Symmetry Repair A/B

Status: **reused frozen data / no PnL**

Primary Stage 1/4 gate: **PASS**

Only the Stage-1 / Stage-4 background/maturity gate factor differs from B-6.

| Primary metric | B-6 | B-7 | Gain (lower) |
|---|---:|---:|---:|
| Acc gate → inverse Dist gate MAE | 0.048003 | 0.000447 | 0.047556 |
| Dist gate → inverse Acc gate MAE | 0.068540 | 0.000432 | 0.068109 |

## Frozen invariants

Range U→D 100.00%; Range D→U 100.00%  
MA U→D 100.00%; MA D→U 100.00%  
B-2/B-3/B-5/B-6 registered metrics preserved exactly: **YES**

## Downstream observations (not tuning targets)

| Metric | B-6 | B-7 | Symmetry gain |
|---|---:|---:|---:|
| Raw stage-vector MAE | 0.058428 | 0.058428 | 0.000000 lower |
| Gate-vector MAE | 0.020136 | 0.000858 | 0.019277 lower |
| Effective-vector MAE | 1.658936 | 0.071794 | 1.587141 lower |
| Probability-vector MAE | 3.468723 | 0.142710 | 3.326014 lower |
| Candidate mirror | 90.78% | 99.65% | 8.88% |
| Formal mirror | 86.99% | 92.33% | 5.33% |
| Formal transition mirror | 85.26% | 90.90% | 5.64% |

Downstream metrics may not be used to retune B-7.
