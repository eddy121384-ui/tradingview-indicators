# Issue #61 — Buy & Hold benchmark

Spot-only apples-to-apples benchmark. FX carry / swap points are excluded from both benchmark and lifecycle variants.

| Pair | Score period | B&H ann ret | B&H Sharpe | B&H max DD | Early ann ret | Early Sharpe | Early max DD | Early exposure |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 2015-11-03 → 2022-03-04 | -0.12% | 0.018 | -14.78% | 0.50% | 0.144 | -10.05% | 33.15% |
| USDJPY | 2015-11-03 → 2022-03-04 | -0.76% | -0.054 | -19.21% | -3.08% | -0.725 | -18.89% | 25.36% |
| GBPUSD | 2015-11-03 → 2022-03-04 | -2.31% | -0.198 | -25.65% | -2.26% | -0.403 | -16.04% | 38.08% |
| AUDUSD | 2015-11-03 → 2022-03-04 | 0.48% | 0.098 | -29.35% | -0.06% | 0.021 | -12.59% | 35.10% |

## Median pair

| Variant | Gross ann ret | Gross Sharpe | Gross max DD | Net 2bp ann ret | Net 2bp Sharpe | Net 2bp max DD | Exposure |
|---|---:|---:|---:|---:|---:|---:|---:|
| buy_and_hold_spot | -0.44% | -0.018 | -22.43% | -0.44% | -0.018 | -22.43% | 100.00% |
| stage_lifecycle_base | -1.72% | -0.271 | -16.41% | -1.88% | -0.298 | -17.07% | 43.43% |
| stage_lifecycle_early_invalidation | -1.16% | -0.191 | -14.32% | -1.36% | -0.228 | -14.74% | 34.12% |

## Early invalidation vs Buy & Hold

- Gross return better: **2/4**
- Gross Sharpe better: **1/4**
- Gross max DD better: **4/4**
- Net 2bp return better: **1/4**
- Net 2bp Sharpe better: **1/4**
- Net 2bp max DD better: **3/4**
