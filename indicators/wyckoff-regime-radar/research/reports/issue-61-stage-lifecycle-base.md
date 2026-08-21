# Issue #61 — Phase B base stage-lifecycle proxy

**Reused-data development evidence only. Rules frozen before this PnL comparison.**

- `binary_color`: stages 1/2/3 long; 4/5/6 short.
- `stage_lifecycle_base`: Stage 1/4 observe; fresh break arms up to confirmBars=3; Stage 2/5 confirms entry; hold only in 2/3 or 5/6; no stops, targets, partial sizing or add leverage.
- Signals are applied with one-bar execution lag.
- 2 bp cost is reported only as fixed sensitivity.

## Median-pair metrics

| Variant | Gross ann return | Gross Sharpe | Gross max DD | Net 2bp ann return | Net 2bp Sharpe | Net 2bp max DD | Exposure | Turnover/yr | Median hold bars | Entries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| binary_color | -3.06% | -0.427 | -21.48% | -3.35% | -0.465 | -22.41% | 77.16% | 14.562 | 21.500 | 185 |
| stage_lifecycle_base | -1.72% | -0.271 | -16.41% | -1.88% | -0.298 | -17.07% | 43.43% | 8.277 | 22.500 | 108 |

## Pair consistency: lifecycle vs binary color

- Gross return better: **3/4**.
- Gross Sharpe better: **2/4**.
- Gross max drawdown better: **4/4**.
- Net 2bp return better: **3/4**.
- Net 2bp Sharpe better: **2/4**.
- Net 2bp max drawdown better: **4/4**.

## Lifecycle event counts

- `bull_setups_armed`: 55
- `bear_setups_armed`: 31
- `bull_setup_confirmed_entries`: 13
- `bear_setup_confirmed_entries`: 9
- `bull_direct_stage2_break_entries`: 35
- `bear_direct_stage5_break_entries`: 51
- `bull_setup_expired_or_cancelled`: 41
- `bear_setup_expired_or_cancelled`: 22
- `long_family_exits`: 47
- `short_family_exits`: 58
- `bull_continuation_break_candidates`: 85
- `bear_continuation_break_candidates`: 67

## Per pair

| Pair | Binary gross return | Lifecycle gross return | Binary Sharpe | Lifecycle Sharpe | Binary DD | Lifecycle DD | Lifecycle exposure | Lifecycle entries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | -1.05% | 0.40% | -0.152 | 0.112 | -18.93% | -13.63% | 41.18% | 23 |
| USDJPY | -3.51% | -3.10% | -0.551 | -0.641 | -21.92% | -18.76% | 36.50% | 30 |
| GBPUSD | -2.61% | -2.90% | -0.316 | -0.492 | -21.04% | -19.76% | 45.99% | 30 |
| AUDUSD | -4.46% | -0.54% | -0.538 | -0.050 | -30.20% | -14.07% | 45.68% | 25 |

## Boundary

All samples are reused evidence. No stop/target/sizing optimization and no independent validation claim.
