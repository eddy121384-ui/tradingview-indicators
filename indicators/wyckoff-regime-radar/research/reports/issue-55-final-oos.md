# Issue #55 — ONE-SHOT Final-OOS result

Final OOS has been **OPENED AND EVALUATED**. This sample may not be reused as an independent test after any rule change.

Window: **2020-04-30 through 2022-03-04**, 480 daily bars per pair.

## Final directional / state-separation summary

- Formal Markup mean return exceeds Formal Markdown in **13 / 16** pair × horizon comparisons.
- Median formal-state forward-return eta-squared: **0.034**.
- Median count of stages occupying at least 1% of Final-OOS bars: **4.0 / 6**.

## Frozen-response trading utility — equal-weight four-pair aggregate

| Strategy | Net ann. return | Vol | Sharpe | Max DD | Exposure | Turnover |
|---|---:|---:|---:|---:|---:|---:|
| wyckoff_frozen_response | 0.35% | 4.16% | 0.11 | -4.73% | 77.6% | 20.5 |
| sma200 | 4.92% | 5.01% | 0.98 | -2.92% | 100.0% | 13.0 |
| momentum60 | 0.38% | 4.65% | 0.11 | -4.74% | 100.0% | 58.5 |
| donchian55 | 3.45% | 5.04% | 0.70 | -3.99% | 100.0% | 6.0 |
| always_flat | 0.00% | 0.00% | — | 0.00% | 0.0% | 0.0 |

### Wyckoff per pair

| Pair | Net ann. return | Sharpe | Max DD | Exposure |
|---|---:|---:|---:|---:|
| EURUSD | 3.46% | 0.66 | -4.94% | 77.2% |
| USDJPY | 0.82% | 0.18 | -4.48% | 86.4% |
| GBPUSD | -4.70% | -0.71 | -11.22% | 70.4% |
| AUDUSD | 1.52% | 0.22 | -12.03% | 76.2% |

## Final confidence calibration

- `evidence_strength`: high beats low **13/32** (40.6%); strict monotonic **3/28** (10.7%).
- `top_gap`: high beats low **6/28** (21.4%); strict monotonic **2/28** (7.1%).

## All-six-state bar-level path snapshot

### 5-bar horizon

| Pair | Stage | n | Mean return | MFE | MAE | Vol | New20H | New20L |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 1 Accumulation | 45 | -0.35% | 0.54% | -1.03% | 5.69% | 26.67% | 33.33% |
| EURUSD | 2 Markup | 179 | 0.16% | 0.84% | -0.61% | 6.13% | 54.75% | 15.08% |
| EURUSD | 3 Re-accumulation | 0 | — | — | — | — | — | — |
| EURUSD | 4 Distribution | 63 | -0.04% | 0.67% | -0.74% | 5.60% | 30.16% | 26.98% |
| EURUSD | 5 Markdown | 188 | 0.00% | 0.61% | -0.58% | 5.33% | 17.55% | 44.15% |
| EURUSD | 6 Re-distribution | 0 | — | — | — | — | — | — |
| USDJPY | 1 Accumulation | 37 | 0.02% | 0.63% | -0.59% | 4.76% | 45.95% | 5.41% |
| USDJPY | 2 Markup | 234 | 0.12% | 0.66% | -0.57% | 5.08% | 39.74% | 13.25% |
| USDJPY | 3 Re-accumulation | 0 | — | — | — | — | — | — |
| USDJPY | 4 Distribution | 28 | 0.38% | 0.82% | -0.35% | 5.27% | 42.86% | 14.29% |
| USDJPY | 5 Markdown | 176 | 0.01% | 0.61% | -0.65% | 5.16% | 11.36% | 33.52% |
| USDJPY | 6 Re-distribution | 0 | — | — | — | — | — | — |
| GBPUSD | 1 Accumulation | 58 | -0.24% | 0.67% | -1.00% | 6.05% | 25.86% | 29.31% |
| GBPUSD | 2 Markup | 197 | 0.01% | 0.90% | -0.95% | 7.65% | 56.35% | 13.71% |
| GBPUSD | 3 Re-accumulation | 0 | — | — | — | — | — | — |
| GBPUSD | 4 Distribution | 80 | 0.07% | 0.72% | -0.69% | 6.38% | 18.75% | 30.00% |
| GBPUSD | 5 Markdown | 139 | 0.32% | 0.97% | -0.61% | 6.36% | 24.46% | 28.78% |
| GBPUSD | 6 Re-distribution | 0 | — | — | — | — | — | — |
| AUDUSD | 1 Accumulation | 53 | -0.09% | 0.90% | -1.12% | 7.97% | 37.74% | 30.19% |
| AUDUSD | 2 Markup | 246 | 0.21% | 1.22% | -1.01% | 9.44% | 46.75% | 13.01% |
| AUDUSD | 3 Re-accumulation | 0 | — | — | — | — | — | — |
| AUDUSD | 4 Distribution | 46 | 0.41% | 1.22% | -0.92% | 8.70% | 17.39% | 28.26% |
| AUDUSD | 5 Markdown | 119 | 0.03% | 0.96% | -0.96% | 7.85% | 14.29% | 41.18% |
| AUDUSD | 6 Re-distribution | 0 | — | — | — | — | — | — |

### 10-bar horizon

| Pair | Stage | n | Mean return | MFE | MAE | Vol | New20H | New20L |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 1 Accumulation | 40 | -0.29% | 1.04% | -1.55% | 6.20% | 40.00% | 55.00% |
| EURUSD | 2 Markup | 179 | 0.23% | 1.15% | -0.81% | 6.17% | 63.69% | 24.02% |
| EURUSD | 3 Re-accumulation | 0 | — | — | — | — | — | — |
| EURUSD | 4 Distribution | 63 | 0.05% | 0.97% | -1.00% | 6.08% | 55.56% | 42.86% |
| EURUSD | 5 Markdown | 188 | 0.00% | 0.85% | -0.80% | 5.39% | 29.26% | 53.19% |
| EURUSD | 6 Re-distribution | 0 | — | — | — | — | — | — |
| USDJPY | 1 Accumulation | 37 | 0.15% | 0.95% | -0.89% | 5.30% | 48.65% | 18.92% |
| USDJPY | 2 Markup | 229 | 0.23% | 0.96% | -0.74% | 5.30% | 49.78% | 22.27% |
| USDJPY | 3 Re-accumulation | 0 | — | — | — | — | — | — |
| USDJPY | 4 Distribution | 28 | 0.71% | 1.20% | -0.39% | 5.05% | 64.29% | 14.29% |
| USDJPY | 5 Markdown | 176 | -0.01% | 0.82% | -0.88% | 5.44% | 17.05% | 41.48% |
| USDJPY | 6 Re-distribution | 0 | — | — | — | — | — | — |
| GBPUSD | 1 Accumulation | 53 | -0.29% | 1.10% | -1.53% | 6.51% | 33.96% | 35.85% |
| GBPUSD | 2 Markup | 197 | 0.06% | 1.22% | -1.26% | 7.81% | 68.02% | 21.83% |
| GBPUSD | 3 Re-accumulation | 0 | — | — | — | — | — | — |
| GBPUSD | 4 Distribution | 80 | 0.22% | 1.03% | -0.94% | 6.61% | 31.25% | 46.25% |
| GBPUSD | 5 Markdown | 139 | 0.53% | 1.41% | -0.78% | 6.46% | 31.65% | 33.81% |
| GBPUSD | 6 Re-distribution | 0 | — | — | — | — | — | — |
| AUDUSD | 1 Accumulation | 48 | -0.18% | 1.17% | -1.64% | 8.25% | 33.33% | 41.67% |
| AUDUSD | 2 Markup | 246 | 0.40% | 1.73% | -1.30% | 9.60% | 55.28% | 19.51% |
| AUDUSD | 3 Re-accumulation | 0 | — | — | — | — | — | — |
| AUDUSD | 4 Distribution | 46 | 0.68% | 1.75% | -1.15% | 8.99% | 28.26% | 43.48% |
| AUDUSD | 5 Markdown | 119 | 0.07% | 1.34% | -1.41% | 8.08% | 22.69% | 47.90% |
| AUDUSD | 6 Re-distribution | 0 | — | — | — | — | — | — |

### 20-bar horizon

| Pair | Stage | n | Mean return | MFE | MAE | Vol | New20H | New20L |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 1 Accumulation | 30 | -0.23% | 1.49% | -1.72% | 6.13% | 60.00% | 76.67% |
| EURUSD | 2 Markup | 179 | 0.35% | 1.62% | -1.11% | 6.06% | 69.27% | 35.20% |
| EURUSD | 3 Re-accumulation | 0 | — | — | — | — | — | — |
| EURUSD | 4 Distribution | 63 | 0.13% | 1.48% | -1.48% | 6.18% | 68.25% | 74.60% |
| EURUSD | 5 Markdown | 188 | 0.08% | 1.28% | -1.20% | 5.63% | 42.55% | 67.55% |
| EURUSD | 6 Re-distribution | 0 | — | — | — | — | — | — |
| USDJPY | 1 Accumulation | 37 | 0.88% | 1.73% | -1.37% | 5.55% | 48.65% | 35.14% |
| USDJPY | 2 Markup | 219 | 0.53% | 1.45% | -0.91% | 5.45% | 63.93% | 28.31% |
| USDJPY | 3 Re-accumulation | 0 | — | — | — | — | — | — |
| USDJPY | 4 Distribution | 28 | 0.58% | 1.55% | -0.47% | 4.81% | 67.86% | 14.29% |
| USDJPY | 5 Markdown | 176 | -0.09% | 1.08% | -1.19% | 5.54% | 23.86% | 59.09% |
| USDJPY | 6 Re-distribution | 0 | — | — | — | — | — | — |
| GBPUSD | 1 Accumulation | 43 | -0.20% | 1.56% | -2.02% | 6.55% | 41.86% | 48.84% |
| GBPUSD | 2 Markup | 197 | 0.33% | 1.82% | -1.63% | 7.72% | 70.05% | 28.93% |
| GBPUSD | 3 Re-accumulation | 0 | — | — | — | — | — | — |
| GBPUSD | 4 Distribution | 80 | 0.52% | 1.43% | -1.24% | 6.56% | 38.75% | 47.50% |
| GBPUSD | 5 Markdown | 139 | 0.70% | 2.14% | -1.18% | 6.93% | 47.48% | 46.04% |
| GBPUSD | 6 Re-distribution | 0 | — | — | — | — | — | — |
| AUDUSD | 1 Accumulation | 47 | -0.09% | 1.78% | -2.38% | 8.04% | 44.68% | 44.68% |
| AUDUSD | 2 Markup | 246 | 0.70% | 2.65% | -1.73% | 9.60% | 64.23% | 29.67% |
| AUDUSD | 3 Re-accumulation | 0 | — | — | — | — | — | — |
| AUDUSD | 4 Distribution | 46 | 1.80% | 2.74% | -1.31% | 8.96% | 50.00% | 63.04% |
| AUDUSD | 5 Markdown | 110 | -0.12% | 1.71% | -2.06% | 8.37% | 32.73% | 60.91% |
| AUDUSD | 6 Re-distribution | 0 | — | — | — | — | — | — |

### 60-bar horizon

| Pair | Stage | n | Mean return | MFE | MAE | Vol | New20H | New20L |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 1 Accumulation | 20 | 0.06% | 3.22% | -3.51% | 6.16% | 40.00% | 65.00% |
| EURUSD | 2 Markup | 179 | 0.00% | 2.49% | -2.17% | 5.90% | 75.98% | 46.37% |
| EURUSD | 3 Re-accumulation | 0 | — | — | — | — | — | — |
| EURUSD | 4 Distribution | 63 | 2.24% | 3.49% | -1.78% | 6.02% | 98.41% | 80.95% |
| EURUSD | 5 Markdown | 158 | -0.26% | 2.16% | -2.26% | 5.70% | 48.10% | 84.18% |
| EURUSD | 6 Re-distribution | 0 | — | — | — | — | — | — |
| USDJPY | 1 Accumulation | 37 | 1.15% | 2.90% | -1.59% | 5.25% | 64.86% | 51.35% |
| USDJPY | 2 Markup | 187 | 1.60% | 2.73% | -1.01% | 5.59% | 98.40% | 32.09% |
| USDJPY | 3 Re-accumulation | 0 | — | — | — | — | — | — |
| USDJPY | 4 Distribution | 20 | 1.67% | 2.94% | -0.78% | 5.13% | 100.00% | 20.00% |
| USDJPY | 5 Markdown | 176 | 0.24% | 2.22% | -2.03% | 5.64% | 43.75% | 89.77% |
| USDJPY | 6 Re-distribution | 0 | — | — | — | — | — | — |
| GBPUSD | 1 Accumulation | 27 | 1.26% | 3.61% | -2.63% | 7.45% | 55.56% | 48.15% |
| GBPUSD | 2 Markup | 197 | 1.72% | 3.74% | -2.14% | 7.55% | 85.79% | 34.01% |
| GBPUSD | 3 Re-accumulation | 0 | — | — | — | — | — | — |
| GBPUSD | 4 Distribution | 80 | -0.72% | 1.84% | -2.12% | 6.60% | 48.75% | 87.50% |
| GBPUSD | 5 Markdown | 115 | 1.53% | 3.97% | -1.90% | 7.11% | 58.26% | 65.22% |
| GBPUSD | 6 Re-distribution | 0 | — | — | — | — | — | — |
| AUDUSD | 1 Accumulation | 38 | -2.19% | 2.87% | -4.31% | 8.46% | 84.21% | 84.21% |
| AUDUSD | 2 Markup | 246 | 1.22% | 4.39% | -2.84% | 9.36% | 77.64% | 49.19% |
| AUDUSD | 3 Re-accumulation | 0 | — | — | — | — | — | — |
| AUDUSD | 4 Distribution | 46 | 4.07% | 6.68% | -1.93% | 8.89% | 91.30% | 86.96% |
| AUDUSD | 5 Markdown | 90 | -0.16% | 2.44% | -3.48% | 8.36% | 40.00% | 88.89% |
| AUDUSD | 6 Re-distribution | 0 | — | — | — | — | — | — |

Full JSON contains q05/q95 tail returns, medians, positive-return rates, episode durations, and next-state transition matrices.

Boundary: this is the one-shot Final-OOS result. Any redesign now requires a new independent sample.
