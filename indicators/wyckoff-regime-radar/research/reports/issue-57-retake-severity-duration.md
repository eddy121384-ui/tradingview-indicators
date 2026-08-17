# Issue #57 — Retake severity × duration map

**Reused-data structural study only. Existing v0.6 is unchanged.**

- Retake events: **89** across **7** FX pairs.

## Continuous pair-aware associations

| Predictor | Median pair rho vs same-direction completion | Median pair rho vs opposite failure |
|---|---:|---:|
| normalized_first_retake_margin | -0.093 | 0.216 |
| first_control_spell_bars | -0.067 | -0.129 |
| max_normalized_retake_margin | -0.034 | 0.179 |
| dominance_area | -0.242 | -0.006 |

## First-control duration (fixed bins)

| Duration | Events | Pair-median success | Pair-median opposite failure | Pair-median timeout |
|---|---:|---:|---:|---:|
| 1_bar | 12 | 0.00% | 0.00% | 100.00% |
| 2_3_bars | 17 | 0.00% | 16.67% | 66.67% |
| 4_plus_bars | 60 | 11.11% | 22.22% | 77.78% |

## First-retake severity (within-pair predictor-only terciles)

| Severity | Events | Pair-median success | Pair-median opposite failure | Pair-median timeout |
|---|---:|---:|---:|---:|
| low | 27 | 20.00% | 0.00% | 75.00% |
| mid | 29 | 0.00% | 0.00% | 100.00% |
| high | 33 | 0.00% | 25.00% | 60.00% |

## Severity × duration matrix

| Severity | 1 bar | 2–3 bars | 4+ bars |
|---|---:|---:|---:|
| low | 0.00% (n=6) | 0.00% (n=4) | 0.00% (n=17) |
| mid | 0.00% (n=2) | 0.00% (n=5) | 0.00% (n=22) |
| high | 0.00% (n=4) | 0.00% (n=8) | 0.00% (n=21) |

## Boundary

Reused-data structural research only; bins were frozen before outcomes and are not production thresholds.
