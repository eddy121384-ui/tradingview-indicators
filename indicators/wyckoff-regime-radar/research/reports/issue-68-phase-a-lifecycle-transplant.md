# Issue #68 Phase A — Human-review-v2 Lifecycle Transplant Audit

Status: **reused burned development data / semantic engineering only / no PnL**

Primary gate: **PASS**
- Old Issue #61 desired-position mirror: **86.44%**
- Preregistered Issue #68 gate: **>= 95.00%**
- Current C-2 lifecycle desired-position mirror: **99.92%**
- Gain vs old lifecycle mirror: **13.48 pp**
- Current C-2 Formal mirror on same scored bars: **99.64%**

## Per pair

| Pair | Formal mirror | Lifecycle position mirror | Position mismatch bars | Flat / Long / Short | Median hold |
|---|---:|---:|---:|---:|---:|
| EURUSD | 100.00% | 100.00% | 0 | 91.91% / 1.64% / 6.44% | 25.0 |
| USDJPY | 99.09% | 99.76% | 4 | 75.26% / 11.06% / 13.68% | 48.0 |
| GBPUSD | 100.00% | 100.00% | 0 | 80.55% / 8.45% / 11.00% | 33.0 |
| AUDUSD | 99.45% | 99.94% | 1 | 99.70% / 0.00% / 0.30% | 1.0 |

## Aggregate mirrored event families

| Event mirror | Bar agreement | Jaccard | Mismatch bars | Either event |
|---|---:|---:|---:|---:|
| `arm_long__to_inverse__arm_short` | 100.00% | 100.00% | 0 | 47 |
| `arm_short__to_inverse__arm_long` | 100.00% | 100.00% | 0 | 42 |
| `entry_long__to_inverse__entry_short` | 100.00% | 100.00% | 0 | 10 |
| `entry_short__to_inverse__entry_long` | 99.97% | 88.89% | 2 | 18 |
| `early_fail_long__to_inverse__early_fail_short` | 100.00% | 100.00% | 0 | 2 |
| `early_fail_short__to_inverse__early_fail_long` | 100.00% | 100.00% | 0 | 7 |
| `opposite_exit_long__to_inverse__opposite_exit_short` | 100.00% | 100.00% | 0 | 8 |
| `opposite_exit_short__to_inverse__opposite_exit_long` | 99.97% | 81.82% | 2 | 11 |
| `add_long_candidate__to_inverse__add_short_candidate` | 100.00% | 100.00% | 0 | 11 |
| `add_short_candidate__to_inverse__add_long_candidate` | 100.00% | 100.00% | 0 | 25 |
| `cancel_long_arm__to_inverse__cancel_short_arm` | 100.00% | 100.00% | 0 | 38 |
| `cancel_short_arm__to_inverse__cancel_long_arm` | 100.00% | 100.00% | 0 | 29 |
| `direct_transition_long__to_inverse__direct_transition_short` | 100.00% | 100.00% | 0 | 2 |
| `direct_transition_short__to_inverse__direct_transition_long` | 100.00% | 100.00% | 0 | 4 |

## Event counts and setup lag

### EURUSD

- Original events: `{'arm_long': 12, 'arm_short': 8, 'entry_long': 2, 'entry_short': 3, 'early_fail_long': 1, 'early_fail_short': 0, 'opposite_exit_long': 1, 'opposite_exit_short': 3, 'add_long_candidate': 2, 'add_short_candidate': 6, 'cancel_long_arm': 11, 'cancel_short_arm': 6, 'direct_transition_long': 1, 'direct_transition_short': 1}`
- Original entry lag histogram: `{'0': 2, '1': 2, '2': 0, '3': 1, 'other': 0}`
- Holding summary: `{'episodes': 5, 'median_bars': 25.0, 'mean_bars': 26.6, 'max_bars': 65}`

### USDJPY

- Original events: `{'arm_long': 12, 'arm_short': 11, 'entry_long': 4, 'entry_short': 5, 'early_fail_long': 1, 'early_fail_short': 2, 'opposite_exit_long': 3, 'opposite_exit_short': 3, 'add_long_candidate': 5, 'add_short_candidate': 8, 'cancel_long_arm': 8, 'cancel_short_arm': 7, 'direct_transition_long': 0, 'direct_transition_short': 1}`
- Original entry lag histogram: `{'0': 1, '1': 3, '2': 4, '3': 1, 'other': 0}`
- Holding summary: `{'episodes': 9, 'median_bars': 48.0, 'mean_bars': 45.22222222222222, 'max_bars': 132}`

### GBPUSD

- Original events: `{'arm_long': 12, 'arm_short': 16, 'entry_long': 4, 'entry_short': 6, 'early_fail_long': 0, 'early_fail_short': 2, 'opposite_exit_long': 4, 'opposite_exit_short': 4, 'add_long_candidate': 4, 'add_short_candidate': 11, 'cancel_long_arm': 9, 'cancel_short_arm': 11, 'direct_transition_long': 1, 'direct_transition_short': 1}`
- Original entry lag histogram: `{'0': 2, '1': 2, '2': 6, '3': 0, 'other': 0}`
- Holding summary: `{'episodes': 10, 'median_bars': 33.0, 'mean_bars': 32.0, 'max_bars': 94}`

### AUDUSD

- Original events: `{'arm_long': 11, 'arm_short': 7, 'entry_long': 0, 'entry_short': 3, 'early_fail_long': 0, 'early_fail_short': 3, 'opposite_exit_long': 0, 'opposite_exit_short': 0, 'add_long_candidate': 0, 'add_short_candidate': 0, 'cancel_long_arm': 10, 'cancel_short_arm': 5, 'direct_transition_long': 0, 'direct_transition_short': 1}`
- Original entry lag histogram: `{'0': 1, '1': 1, '2': 0, '3': 1, 'other': 0}`
- Holding summary: `{'episodes': 3, 'median_bars': 1.0, 'mean_bars': 1.6666666666666667, 'max_bars': 3}`

## Boundary

No PnL/return/Sharpe/drawdown/sizing/stop/target metrics are computed. Burned four-FX evidence is semantic engineering data only.
