# Issue #66 Phase B-3 — Direction-Neutral Trend-Entry Gate A/B

Status: **reused frozen data / no PnL**

Primary trend-entry gate: **PASS**

Only the Stage-2 / Stage-5 fresh trend-entry gate differs from B-2.

| Primary metric | B-2 | B-3 | Gain (lower) |
|---|---:|---:|---:|
| Markup entry → inverse Markdown entry MAE | 0.193957 | 0.000277 | 0.193680 |
| Markdown entry → inverse Markup entry MAE | 0.198902 | 0.000303 | 0.198599 |

## Frozen invariants

Range U→D 100.00%; Range D→U 100.00%  
MA U→D 100.00%; MA D→U 100.00%  
B-2 break metrics preserved exactly: **YES**

## Downstream observations (not tuning targets)

| Metric | B-2 | B-3 | Symmetry gain |
|---|---:|---:|---:|
| Raw stage-vector MAE | 2.678586 | 2.678586 | 0.000000 lower |
| Gate-vector MAE | 0.070393 | 0.020117 | 0.050276 lower |
| Effective-vector MAE | 5.469371 | 1.781195 | 3.688177 lower |
| Probability-vector MAE | 8.349753 | 3.644949 | 4.704804 lower |
| Candidate mirror | 76.43% | 89.97% | 13.54% |
| Formal mirror | 78.74% | 87.08% | 8.34% |
| Formal transition mirror | 76.11% | 85.32% | 9.21% |

Downstream metrics may not be used to retune B-3.
