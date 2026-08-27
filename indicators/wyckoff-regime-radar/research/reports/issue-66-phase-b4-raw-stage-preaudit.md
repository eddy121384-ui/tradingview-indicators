# Issue #66 Phase B-4 — Raw-Stage Residual Pre-Audit

Status: **reused frozen data / no PnL / no formula change**

B-3 raw-stage vector MAE: **2.678344**  
Reconstructed from three mirrored families: **2.678344**  
Reconstruction check: **PASS**

## Raw-stage localization

| Rank | Mirrored family | Weighted raw MAE | Share of raw absolute error |
|---:|---|---:|---:|
| 1 | Stage 3 Re-accumulation ↔ Stage 6 Re-distribution | 4.207516 | 54.20% |
| 2 | Stage 1 Accumulation ↔ Stage 4 Distribution | 3.335228 | 41.51% |
| 3 | Stage 2 Markup ↔ Stage 5 Markdown | 0.357240 | 4.29% |

Dominant residual family by preregistered rule: **Stage 3 Re-accumulation ↔ Stage 6 Re-distribution**.

## Secondary layer context

These values localize propagation only; they do not choose the next formula.

| Mirrored family | Gate MAE | Effective MAE | Probability MAE |
|---|---:|---:|---:|
| Stage 3 Re-accumulation ↔ Stage 6 Re-distribution | 0.001763 | 0.150492 | 0.290179 |
| Stage 1 Accumulation ↔ Stage 4 Distribution | 0.058272 | 5.098812 | 7.930602 |
| Stage 2 Markup ↔ Stage 5 Markdown | 0.000372 | 0.093567 | 2.709089 |

## Next-step boundary

No classifier change is authorized by this report. Inspect the dominant raw family's source formula for explicit non-isomorphic primitives, then preregister one B-5 repair family before changing code. Candidate/Formal/PnL results are not selection criteria.
