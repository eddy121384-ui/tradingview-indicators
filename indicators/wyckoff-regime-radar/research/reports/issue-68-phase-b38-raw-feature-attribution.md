# Issue #68 Phase B3.8 — Raw Feature Attribution

Status: **diagnostic only / frozen C-2 / no performance use**

Primary engineering gate: **PASS**
- raw-loss observations, bull+bear four-FX: **7620**
- raw winner = precursor range: **2232 (29.3%)**
- raw winner = opposite range: **2232 (29.3%)**
- raw winner = opposite trend: **3156 (41.4%)**
- unexplained raw winner: **0**
- Stage2-vs5 exact raw0 reconstruction max error: **2.842e-14**
- minimum reciprocal boolean mirror agreement: **99.818%**
- max reciprocal component-delta MAE (diagnostic only): **5.939e-02**

## Stage2-vs5 largest negative weighted component when Markup raw0 < Markdown raw0

- break: **1103**
- heat: **325**
- structure: **1223**
- extension: **7**
- continuation: **17**
- trace: **9**

## Per pair raw winner groups

| Pair | Side | Raw loss | Precursor range | Opp range | Opp trend |
|---|---|---:|---:|---:|---:|
| EURUSD | bull | 992 | 328 | 226 | 438 |
| EURUSD | bear | 909 | 226 | 328 | 355 |
| USDJPY | bull | 1010 | 335 | 300 | 375 |
| USDJPY | bear | 972 | 300 | 335 | 337 |
| GBPUSD | bull | 899 | 230 | 297 | 372 |
| GBPUSD | bear | 975 | 297 | 230 | 448 |
| AUDUSD | bull | 987 | 302 | 214 | 471 |
| AUDUSD | bear | 876 | 214 | 302 | 360 |

## Boundary

Raw-stage attribution only. No classifier weight, threshold, gate, persistence, exposure rule, or strategy-performance metric is changed or optimized.
