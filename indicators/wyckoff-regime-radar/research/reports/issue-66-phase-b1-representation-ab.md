# Issue #66 Phase B-1 — Reciprocal-Safe Representation A/B

Status: **reused frozen data / no PnL**

Primary representation gate: **PASS**

Only the preregistered representation family differs from the frozen v0.6 Phase-B baseline. Directional heuristics, stage formulas/gates, and persistence are unchanged.

## Primary layer

| Metric | Baseline | B-1 | Symmetry gain |
|---|---:|---:|---:|
| MA cross up → inverse down Jaccard | 92.43% | 100.00% | 7.57% |
| MA cross down → inverse up Jaccard | 93.64% | 100.00% | 6.36% |
| Representation numeric MAE | 0.135885 | 0.000000 | 0.135885 lower |

## Downstream observations (not tuning targets)

| Metric | Baseline | B-1 | Symmetry gain |
|---|---:|---:|---:|
| Breakout mode up → inverse down | 95.64% | 100.00% | 4.36% |
| Breakdown mode down → inverse up | 96.35% | 100.00% | 3.65% |
| Raw stage-vector MAE | 3.880591 | 3.936016 | -0.055425 lower |
| Gate-vector MAE | 0.068596 | 0.066895 | 0.001701 lower |
| Effective stage-vector MAE | 5.294190 | 5.170996 | 0.123193 lower |
| Probability-vector MAE | 9.239240 | 9.036012 | 0.203228 lower |
| Candidate-display mirror | 74.32% | 74.67% | 0.35% |
| Formal mirror | 76.11% | 76.57% | 0.46% |
| Candidate transition-pair mirror | 67.84% | 68.42% | 0.58% |
| Formal transition-pair mirror | 73.36% | 73.89% | 0.53% |

## Boundary

This report does not authorize threshold equalization or stage-formula changes. If B-1 passes its primary gate, the next experiment may change one additional non-isomorphic primitive family only.
