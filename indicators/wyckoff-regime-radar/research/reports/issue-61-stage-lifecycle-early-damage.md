# Issue #61 — Phase B Early-Damaged lifecycle overlay

**Reused-data development evidence only. Overlay mechanics frozen before PnL.**

- Base lifecycle is unchanged.
- Exact archived Issue #57 Transition Health engine is used.
- Matching Early Damaged exits and blocks that direction until the same TH watch resolves.
- Resolution does not auto re-enter; a new base lifecycle entry is required.
- Healthy +3 has no entry/re-entry role.

## Median-pair metrics

| Variant | Gross ann return | Gross Sharpe | Gross max DD | Net 2bp ann return | Net 2bp Sharpe | Net 2bp max DD | Exposure | Turnover/yr | Entries |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| binary_color | -3.06% | -0.427 | -21.48% | -3.35% | -0.465 | -22.41% | 77.16% | 14.562 | 185 |
| stage_lifecycle_base | -1.72% | -0.271 | -16.41% | -1.88% | -0.298 | -17.07% | 43.43% | 8.277 | 108 |
| stage_lifecycle_plus_early_damage | -1.57% | -0.287 | -14.95% | -1.74% | -0.318 | -15.25% | 40.45% | 8.124 | 106 |

## Incremental consistency: Early Damaged vs base lifecycle

- Gross return better: **3/4**.
- Gross Sharpe better: **2/4**.
- Gross max drawdown better: **2/4**.
- Net 2bp return better: **3/4**.
- Net 2bp Sharpe better: **2/4**.
- Net 2bp max drawdown better: **2/4**.

## Managed overlay event counts

- `bull_setups_armed`: 53
- `bear_setups_armed`: 30
- `bull_setup_confirmed_entries`: 11
- `bear_setup_confirmed_entries`: 9
- `bull_direct_stage2_break_entries`: 35
- `bear_direct_stage5_break_entries`: 51
- `bull_setup_expired_or_cancelled`: 41
- `bear_setup_expired_or_cancelled`: 21
- `long_family_exits`: 38
- `short_family_exits`: 49
- `bull_continuation_break_candidates`: 81
- `bear_continuation_break_candidates`: 65
- `early_damage_pulses`: 31
- `early_damage_long_exits`: 7
- `early_damage_short_exits`: 9
- `early_damage_bull_setup_cancels`: 0
- `early_damage_bear_setup_cancels`: 0
- `damage_blocks_started_bull`: 17
- `damage_blocks_started_bear`: 14
- `damage_block_resolutions`: 31
- `blocked_bull_entry_attempts`: 6
- `blocked_bear_entry_attempts`: 3

## Per pair

| Pair | Base return | Managed return | Base Sharpe | Managed Sharpe | Base DD | Managed DD | Base exposure | Managed exposure | Early-damage exits |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 0.40% | 0.42% | 0.112 | 0.118 | -13.63% | -14.77% | 41.18% | 39.66% | 3 |
| USDJPY | -3.10% | -2.10% | -0.641 | -0.439 | -18.76% | -13.24% | 36.50% | 34.31% | 4 |
| GBPUSD | -2.90% | -2.79% | -0.492 | -0.505 | -19.76% | -19.11% | 45.99% | 41.24% | 5 |
| AUDUSD | -0.54% | -1.04% | -0.050 | -0.135 | -14.07% | -15.13% | 45.68% | 41.79% | 4 |

## Boundary

All samples are reused evidence. Frozen Early-Damaged overlay only; no stop/target/sizing optimization or validation claim.
