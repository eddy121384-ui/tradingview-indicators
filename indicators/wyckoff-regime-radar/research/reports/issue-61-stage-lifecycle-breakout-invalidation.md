# Issue #61 — Phase D breakout-invalidation stop

**Reused-data development evidence only. Rule frozen before PnL.**

- Base lifecycle unchanged except for structural failed-breakout exit.
- Long exits when close <= the upside break level that caused entry.
- Short exits when close >= the downside break level that caused entry.
- Re-entry after a stop requires a new matching fresh break.
- No ATR / percent stop, buffer, target, trailing stop, or partial sizing.

## Median-pair metrics

| Variant | Gross ann return | Gross Sharpe | Gross max DD | Net 2bp ann return | Net 2bp Sharpe | Net 2bp max DD | Exposure | Turnover/yr | Median hold bars | Entries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| stage_lifecycle_base | -1.72% | -0.271 | -16.41% | -1.88% | -0.298 | -17.07% | 43.43% | 8.277 | 22.500 | 27.500 |
| stage_lifecycle_breakout_invalidation | -1.51% | -0.360 | -13.81% | -1.75% | -0.416 | -14.48% | 24.60% | 12.263 | 3.000 | 40.000 |

## Incremental consistency: invalidation stop vs base

- Gross return better: **3/4**.
- Gross Sharpe better: **2/4**.
- Gross max drawdown better: **4/4**.
- Net 2bp return better: **2/4**.
- Net 2bp Sharpe better: **2/4**.
- Net 2bp max drawdown better: **4/4**.

## Stop events

- `long_invalidation_exits`: 59
- `short_invalidation_exits`: 73
- `long_reentries_after_invalidation`: 26
- `short_reentries_after_invalidation`: 27
- `entry_anchor_missing`: 0

## Per pair

| Pair | Base return | Stop return | Base Sharpe | Stop Sharpe | Base DD | Stop DD | Base exposure | Stop exposure | Invalidation exits |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 0.40% | 0.75% | 0.112 | 0.230 | -13.63% | -5.88% | 41.18% | 27.19% | 25 |
| USDJPY | -3.10% | -2.28% | -0.641 | -0.610 | -18.76% | -14.55% | 36.50% | 19.65% | 33 |
| GBPUSD | -2.90% | -2.89% | -0.492 | -0.638 | -19.76% | -17.74% | 45.99% | 23.91% | 41 |
| AUDUSD | -0.54% | -0.73% | -0.050 | -0.110 | -14.07% | -13.06% | 45.68% | 25.30% | 33 |

## Boundary

Frozen structural invalidation only. No ATR/percent buffer, target, trailing stop, sizing, or validation claim.
