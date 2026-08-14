# Issue #57 — Transition formation and regime decay behavior map

**Burned-data behavior study only. Existing v0.6 is not modified. No independent OOS claim.**

## Formation — does a sudden consensus build matter?

Total actionable episode onsets: **263**
Median of pair-level median episode duration: **2.0 bars**

Continuous pair-median relationships:

| Formation measurement | Spearman rho |
|---|---:|
| 3-bar Top2 strength change vs episode duration | 0.006 |
| 3-bar entropy drop vs episode duration | 0.020 |
| 3-bar Top2 strength change vs 10-bar aligned return | -0.004 |
| 3-bar entropy drop vs 10-bar aligned return | -0.118 |

Sign-only descriptive split (not a production threshold):

| Group | Events | Median duration | Survive 5 | Survive 10 | Survive 20 | 10-bar aligned return | 20-bar aligned return |
|---|---:|---:|---:|---:|---:|---:|---:|
| Strength up + entropy down | 144 | 2.5 | 35.00% | 20.00% | 4.76% | -0.25% | 0.24% |
| Other formations | 119 | 2.0 | 29.17% | 13.04% | 0.00% | -0.15% | -0.01% |

## Regime health — do deterioration warnings appear before the episode ends?

Each established-regime bar gets 0–3 warnings: Top2 weakening, entropy rising, opposite structural pressure rising.

| Warning count | Observations | End <=5 bars | End <=10 bars | Median remaining bars | 5-bar aligned return | 5-bar adverse excursion |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 593 | 51.55% | 78.12% | 5.0 | -0.22% | 1.02% |
| 1 | 16 | 100.00% | 100.00% | 3.0 | -0.05% | 0.41% |
| 2 | 22 | 80.00% | 100.00% | 3.5 | -0.15% | 0.74% |
| 3 | 114 | 84.62% | 100.00% | 1.0 | 0.04% | 0.72% |

Episode-level first occurrence of **2+ simultaneous warnings**:

- Events: 58
- End within 5 bars (pair-median): 83.33%
- End within 10 bars (pair-median): 100.00%
- Median remaining bars (pair-median): 2.0
- 5-bar aligned return (pair-median): -0.10%
- 5-bar adverse excursion (pair-median): 0.71%

## Interpretation boundary

This report maps behavior. It does not pick an optimal lookback, warning threshold, or trading rule. Any later production change must be a separate decision after the behavior is understood.
