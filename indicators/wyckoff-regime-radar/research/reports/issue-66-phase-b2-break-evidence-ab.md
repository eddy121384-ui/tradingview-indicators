# Issue #66 Phase B-2 — Direction-Neutral Break Evidence A/B

Status: **reused frozen data / no PnL**

Primary break-evidence gate: **PASS**

Only break evidence and its directly-derived gate differ from B-1.

| Primary metric | B-1 | B-2 | Gain (lower) |
|---|---:|---:|---:|
| Break score U→inverse D MAE | 25.414096 | 0.136128 | 25.277968 |
| Break score D→inverse U MAE | 25.491818 | 0.096506 | 25.395312 |
| Break gate U→inverse D MAE | 0.249587 | 0.001361 | 0.248226 |
| Break gate D→inverse U MAE | 0.249458 | 0.000965 | 0.248493 |

## Frozen invariants

Range U→D: 100.00%; Range D→U: 100.00%  
MA U→D: 100.00%; MA D→U: 100.00%

## Downstream observations (not tuning targets)

| Metric | B-1 | B-2 | Symmetry gain |
|---|---:|---:|---:|
| Raw stage-vector MAE | 3.936016 | 2.678344 | 1.257671 lower |
| Gate-vector MAE | 0.066895 | 0.070447 | -0.003551 lower |
| Effective-vector MAE | 5.170996 | 5.471294 | -0.300298 lower |
| Probability-vector MAE | 9.036012 | 8.345951 | 0.690062 lower |
| Candidate mirror | 74.67% | 76.38% | 1.72% |
| Formal mirror | 76.57% | 78.86% | 2.29% |
| Formal transition mirror | 73.89% | 76.22% | 2.33% |

Stage metrics above may not be used to retune B-2.
