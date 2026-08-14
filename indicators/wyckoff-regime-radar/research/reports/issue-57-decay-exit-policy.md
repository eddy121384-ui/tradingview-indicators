# Issue #57 — Decay warning exit vs regime-change exit

**Burned-data position-management comparison only. Existing v0.6 is unchanged.**

## Question

If an established actionable Top-2 regime develops the first 2+ decay warning, is it better to exit on the next open or wait until the regime visibly changes and then exit on the following open?

## Execution convention

- Same entry for both policies: next open after episode onset.
- Warning policy: next open after first 2+ warning.
- Regime-change policy: wait for the first post-episode bar to close, then exit next open.
- This therefore avoids same-close look-ahead execution.

## Aggregate

- Comparable warned episodes: **58** across **7** FX pairs.
- Warning exit beats later regime-change exit (pooled): **53.45%**.
- Median pair warning-exit win rate: **50.00%**.
- Pairs where warning exit wins a majority of events: **3 / 7**.
- Median pair mean incremental return from continuing to hold after the warning: **-0.02%**.
- Median pair mean warning-exit advantage: **0.02%**.
- Median pair mean MAE reduction from leaving at warning: **0.15%**.
- Median pair mean MFE sacrificed by leaving at warning: **0.22%**.
- Median pair bars exited earlier: **3.0** bars.

## Per pair

| Pair | Events | Warning exit wins | Hold-after-warning return | Early advantage | MAE reduction | MFE sacrificed | Bars earlier |
|---|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 4 | 50.00% | -0.05% | 0.05% | 0.37% | 0.36% | 4.0 |
| USDJPY | 6 | 50.00% | -0.15% | 0.15% | 0.14% | 0.17% | 3.0 |
| GBPUSD | 14 | 64.29% | 0.03% | -0.03% | 0.15% | 0.23% | 2.0 |
| AUDUSD | 11 | 45.45% | -0.03% | 0.03% | 0.22% | 0.72% | 3.0 |
| EURCHF | 11 | 54.55% | 0.17% | -0.17% | 0.07% | 0.22% | 3.0 |
| USDCAD | 7 | 57.14% | -0.02% | 0.02% | 0.19% | 0.22% | 4.0 |
| USDCHF | 5 | 40.00% | 0.02% | -0.02% | 0.11% | 0.19% | 5.0 |

## Interpretation boundary

This comparison is conditional on an episode surviving long enough to develop a warning, and the warning definition itself came from earlier burned-data behavior mapping. It can tell us how the existing indicator behaved historically; it cannot independently validate a production exit rule.
