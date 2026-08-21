# Issue #61 — Phase C range-managed lifecycle

**Reused-data development evidence only. Rule frozen before PnL.**

- Base lifecycle unchanged.
- Strong Trend Consolidation = existing `rangeScore >= 70` full range gate.
- Exposure reduces 1.0 → 0.5; no automatic restore when rangeScore falls.
- Fresh matching break in Formal Stage 2/5 restores 0.5 → 1.0.
- No stop, target, trailing stop, leverage, or optimized fraction.

## Median-pair metrics

| Variant | Gross ann return | Gross Sharpe | Gross max DD | Net 2bp ann return | Net 2bp Sharpe | Net 2bp max DD | Avg abs exposure | Nonzero exposure | Turnover/yr | Half exposure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| stage_lifecycle_base | -1.72% | -0.271 | -16.41% | -1.88% | -0.298 | -17.07% | 43.43% | 43.43% | 8.277 | 0.00% |
| stage_lifecycle_range_managed | -1.67% | -0.284 | -18.12% | -1.85% | -0.315 | -18.76% | 40.45% | 43.43% | 8.852 | 6.36% |

## Incremental consistency: range-managed vs base

- Gross return better: **1/4**.
- Gross Sharpe better: **1/4**.
- Gross max drawdown better: **1/4**.
- Net 2bp return better: **1/4**.
- Net 2bp Sharpe better: **1/4**.
- Net 2bp max drawdown better: **1/4**.

## Management events

- `long_reductions`: 25
- `short_reductions`: 36
- `long_readds`: 8
- `short_readds`: 9
- `new_long_episodes`: 48
- `new_short_episodes`: 60

## Per pair

| Pair | Base return | Managed return | Base Sharpe | Managed Sharpe | Base DD | Managed DD | Managed avg exposure | Reductions | Re-adds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 0.40% | 0.18% | 0.112 | 0.064 | -13.63% | -15.24% | 38.69% | 10 | 4 |
| USDJPY | -3.10% | -3.50% | -0.641 | -0.763 | -18.76% | -20.99% | 33.24% | 17 | 5 |
| GBPUSD | -2.90% | -3.33% | -0.492 | -0.597 | -19.76% | -21.61% | 42.21% | 19 | 7 |
| AUDUSD | -0.54% | -0.02% | -0.050 | 0.028 | -14.07% | -13.76% | 42.58% | 15 | 1 |

## Boundary

Frozen inherited rangeScore=70 and semantic 50/50 split. Reused development data only; no tuning or validation claim.
