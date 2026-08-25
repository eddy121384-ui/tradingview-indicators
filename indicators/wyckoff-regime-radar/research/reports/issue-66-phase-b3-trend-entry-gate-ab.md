# Issue #66 Phase B-3 — Direction-Neutral Trend-Entry Gate A/B

Status: **reused frozen data / no PnL**

Primary trend-entry gate: **PASS**

Only the Stage-2 / Stage-5 fresh trend-entry gate differs from B-2.

| Primary metric | B-2 | B-3 | Gain (lower) |
|---|---:|---:|---:|
| Markup entry → inverse Markdown entry MAE | 0.193968 | 0.000277 | 0.193691 |
| Markdown entry → inverse Markup entry MAE | 0.199215 | 0.000303 | 0.198912 |

## Frozen invariants

Range U→D 100.00%; Range D→U 100.00%  
MA U→D 100.00%; MA D→U 100.00%  
B-2 break metrics preserved exactly: **YES**

## Downstream observations (not tuning targets)

| Metric | B-2 | B-3 | Symmetry gain |
|---|---:|---:|---:|
| Raw stage-vector MAE | 2.678344 | 2.678344 | 0.000000 lower |
| Gate-vector MAE | 0.070447 | 0.020136 | 0.050311 lower |
| Effective-vector MAE | 5.471294 | 1.781622 | 3.689671 lower |
| Probability-vector MAE | 8.345951 | 3.643290 | 4.702661 lower |
| Candidate mirror | 76.38% | 89.95% | 13.57% |
| Formal mirror | 78.86% | 87.16% | 8.30% |
| Formal transition mirror | 76.22% | 85.41% | 9.19% |

Downstream metrics may not be used to retune B-3.
