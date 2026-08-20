# Issue #57 — Color-first regime + Transition Health risk overlay

**Reused-data strategy-proxy diagnostic only. No production rule change.**

- Formal color: stages 1/2/3 = bull, 4/5/6 = bear, 0 = flat.
- Color is acted on immediately in signal time; position applies one bar later.
- Early Damaged blocks the matching color direction; later matching Healthy re-risks.
- Healthy does not delay an unblocked color entry.
- Fixed cost sensitivity: 2 bp per unit absolute position change.

## development_7fx

Pairs: **7** | Color entries: **305** | Early-Damaged blocks: **41** | Healthy re-risks: **4**

| Variant | Gross ann ret | Gross Sharpe | Gross max DD | Net 2bp ann ret | Net 2bp Sharpe | Net 2bp max DD | Ann turnover | Exposure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| color_only | -1.80% | -0.262 | -21.04% | -2.00% | -0.295 | -21.61% | 9.559 | 52.90% |
| color_plus_th_gate | -1.51% | -0.223 | -18.66% | -1.71% | -0.256 | -19.24% | 9.769 | 47.69% |

Managed wins (gross) — return **5/7**, Sharpe **3/7**, drawdown **4/7**.
Managed wins (2bp) — return **5/7**, Sharpe **3/7**, drawdown **4/7**.

## later_reused_5fx_2022_2026

Pairs: **5** | Color entries: **171** | Early-Damaged blocks: **29** | Healthy re-risks: **6**

| Variant | Gross ann ret | Gross Sharpe | Gross max DD | Net 2bp ann ret | Net 2bp Sharpe | Net 2bp max DD | Ann turnover | Exposure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| color_only | -2.96% | -0.254 | -24.97% | -3.21% | -0.281 | -25.34% | 13.241 | 94.41% |
| color_plus_th_gate | -1.38% | -0.108 | -20.31% | -1.66% | -0.139 | -21.01% | 13.872 | 89.41% |

Managed wins (gross) — return **5/5**, Sharpe **5/5**, drawdown **2/5**.
Managed wins (2bp) — return **5/5**, Sharpe **5/5**, drawdown **3/5**.

## combined_12fx

Pairs: **12** | Color entries: **476** | Early-Damaged blocks: **70** | Healthy re-risks: **10**

| Variant | Gross ann ret | Gross Sharpe | Gross max DD | Net 2bp ann ret | Net 2bp Sharpe | Net 2bp max DD | Ann turnover | Exposure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| color_only | -2.11% | -0.258 | -21.09% | -2.30% | -0.288 | -22.08% | 10.189 | 53.36% |
| color_plus_th_gate | -1.45% | -0.179 | -19.44% | -1.68% | -0.213 | -19.97% | 10.189 | 51.10% |

Managed wins (gross) — return **10/12**, Sharpe **8/12**, drawdown **6/12**.
Managed wins (2bp) — return **10/12**, Sharpe **8/12**, drawdown **7/12**.

## Per-pair gross comparison

| Cohort | Pair | Color ret | Managed ret | Color Sharpe | Managed Sharpe | Color DD | Managed DD | Blocks | Re-risks |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| development_7fx | EURUSD | -0.72% | -0.75% | -0.125 | -0.135 | -18.93% | -20.23% | 4 | 0 |
| development_7fx | USDJPY | -2.42% | -1.82% | -0.456 | -0.359 | -21.92% | -17.04% | 6 | 0 |
| development_7fx | GBPUSD | -1.80% | -1.51% | -0.262 | -0.223 | -21.04% | -18.66% | 7 | 0 |
| development_7fx | AUDUSD | -3.08% | -3.06% | -0.445 | -0.465 | -30.20% | -31.47% | 6 | 0 |
| development_7fx | EURCHF | 0.77% | 1.16% | 0.248 | 0.378 | -7.00% | -6.72% | 5 | 0 |
| development_7fx | USDCAD | 0.35% | -0.07% | 0.095 | 0.009 | -9.79% | -12.22% | 6 | 3 |
| development_7fx | USDCHF | -2.43% | -2.35% | -0.495 | -0.500 | -21.13% | -20.51% | 7 | 1 |
| later_reused_5fx_2022_2026 | NZDUSD | -2.96% | -1.38% | -0.254 | -0.108 | -26.40% | -27.05% | 10 | 1 |
| later_reused_5fx_2022_2026 | EURGBP | -5.09% | -4.60% | -0.545 | -0.494 | -26.14% | -25.51% | 5 | 0 |
| later_reused_5fx_2022_2026 | GBPJPY | -4.24% | -2.36% | -0.413 | -0.222 | -24.97% | -17.42% | 7 | 3 |
| later_reused_5fx_2022_2026 | AUDJPY | 1.36% | 1.55% | 0.182 | 0.205 | -20.12% | -20.31% | 5 | 2 |
| later_reused_5fx_2022_2026 | CADJPY | 4.65% | 4.89% | 0.525 | 0.550 | -12.32% | -12.32% | 2 | 0 |

## Boundary

All observations are reused for this new overlay hypothesis. This is not independent OOS validation and does not justify production trading rules.
