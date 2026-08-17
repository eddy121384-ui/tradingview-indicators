# Issue #57 — Transition Health independent OOS validation

**Frozen rule, frozen new FX sample, no post-outcome tuning. Existing v0.6 is unchanged.**

- Score era: **2022-01-01 through 2026-08-14**.
- Pairs: **NZDUSD, EURGBP, GBPJPY, AUDJPY, CADJPY**.
- Observable rule: carried stage takes the handoff lead and keeps a strict lead through **+3 bars**.
- Eligible +3 events: **81**.
- Healthy / damaged events: **45 / 36**.
- Price outcomes start from the +3 close.

## Cross-pair OOS price outcomes

| Horizon | Group | Aligned return | Hit rate | MFE | MAE | MFE-MAE |
|---|---|---:|---:|---:|---:|---:|
| +5 | healthy_hold | 0.11% | 46.67% | 0.81% | 0.99% | 0.23% |
| +5 | damaged_retake | -0.04% | 45.45% | 0.88% | 1.24% | -0.08% |
| +10 | healthy_hold | 0.09% | 53.33% | 1.13% | 1.61% | -0.25% |
| +10 | damaged_retake | -0.42% | 37.50% | 1.00% | 1.59% | -0.05% |
| +20 | healthy_hold | 0.92% | 62.50% | 1.82% | 1.65% | 0.17% |
| +20 | damaged_retake | -0.61% | 37.50% | 1.83% | 1.78% | -0.46% |

## Pair consistency

| Horizon | Comparable FX | Healthy wins return | Healthy wins hit rate | Healthy wins MFE-MAE |
|---|---:|---:|---:|---:|
| +5 | 5 | 3 | 2 | 3 |
| +10 | 5 | 5 | 4 | 3 |
| +20 | 5 | 4 | 4 | 3 |

## Per pair — 10-bar OOS aligned return / hit rate

| Pair | Healthy n | Healthy return | Healthy hit | Damaged n | Damaged return | Damaged hit |
|---|---:|---:|---:|---:|---:|---:|
| NZDUSD | 8 | -0.59% | 37.50% | 11 | -0.61% | 36.36% |
| EURGBP | 3 | -0.35% | 33.33% | 4 | -0.42% | 25.00% |
| GBPJPY | 15 | 0.09% | 53.33% | 8 | -0.93% | 37.50% |
| AUDJPY | 8 | 0.75% | 62.50% | 8 | -0.19% | 75.00% |
| CADJPY | 11 | 0.80% | 63.64% | 5 | 0.66% | 60.00% |

## Boundary

Independent OOS evaluation of the rule frozen before this sample was read. No threshold or checkpoint tuning is permitted on this sample.
