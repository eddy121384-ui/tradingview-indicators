# Issue #61 — Phase E early breakout invalidation

**Reused-data development evidence only. Rule frozen before PnL.**

- Same structural anchor as Phase D.
- Stop is active only at entry ages 1–3 (`confirmBars=3`).
- Surviving age 3 retires the anchor and returns control to the base lifecycle.
- New fresh break is required after an early stop.

## Median-pair metrics

| Variant | Gross ann return | Gross Sharpe | Gross max DD | Net 2bp ann return | Net 2bp Sharpe | Net 2bp max DD | Exposure | Turnover/yr | Median hold bars | Entries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| stage_lifecycle_base | -1.72% | -0.271 | -16.41% | -1.88% | -0.298 | -17.07% | 43.43% | 8.277 | 22.500 | 27.500 |
| stage_lifecycle_breakout_invalidation | -1.51% | -0.360 | -13.81% | -1.75% | -0.416 | -14.48% | 24.60% | 12.263 | 3.000 | 40.000 |
| stage_lifecycle_early_breakout_invalidation | -1.16% | -0.191 | -14.32% | -1.36% | -0.228 | -14.74% | 34.12% | 10.423 | 4.750 | 34.500 |

## Early-only consistency vs base

- Gross return better: **4/4**.
- Gross Sharpe better: **3/4**.
- Gross max drawdown better: **3/4**.
- Net 2bp return better: **3/4**.
- Net 2bp Sharpe better: **3/4**.
- Net 2bp max drawdown better: **3/4**.

## Early-stop events

- `long_early_invalidation_exits`: 24
- `short_early_invalidation_exits`: 44
- `long_reentries_after_early_invalidation`: 10
- `short_reentries_after_early_invalidation`: 19
- `windows_survived`: 64
- `entry_anchor_missing`: 0

## Per pair

| Pair | Base return | Always-stop return | Early-stop return | Base DD | Always DD | Early DD | Base hold | Always hold | Early hold |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 0.40% | 0.75% | 0.50% | -13.63% | -5.88% | -10.05% | 27.000 | 3.000 | 6.500 |
| USDJPY | -3.10% | -2.28% | -3.08% | -18.76% | -14.55% | -18.89% | 16.500 | 2.000 | 2.000 |
| GBPUSD | -2.90% | -2.89% | -2.26% | -19.76% | -17.74% | -16.04% | 21.000 | 3.000 | 12.000 |
| AUDUSD | -0.54% | -0.73% | -0.06% | -14.07% | -13.06% | -12.59% | 24.000 | 3.000 | 3.000 |

## Boundary

Existing confirmBars=3 only; reused development evidence; no buffer/ATR/target/sizing optimization.
