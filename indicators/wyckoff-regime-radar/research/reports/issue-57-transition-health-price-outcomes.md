# Issue #57 — Transition health → subsequent price outcomes

**Reused-data price-relevance study only. Existing v0.6 is unchanged.**

- Observable checkpoint: **+3 bars after handoff onset**.
- Eligible unresolved events: **114**.
- Healthy / damaged events: **63 / 51**.
- All price outcomes start from the +3 close; pre-checkpoint price movement is excluded.

## Cross-pair price outcomes

| Horizon | Group | Aligned return | Hit rate | MFE | MAE | MFE-MAE |
|---|---|---:|---:|---:|---:|---:|
| +5 | healthy_hold | 0.06% | 66.67% | 0.81% | 0.68% | 0.12% |
| +5 | damaged_retake | 0.05% | 40.00% | 0.78% | 0.77% | 0.17% |
| +10 | healthy_hold | 0.20% | 62.50% | 1.05% | 0.76% | 0.20% |
| +10 | damaged_retake | 0.01% | 42.86% | 1.15% | 0.98% | -0.11% |
| +20 | healthy_hold | 0.23% | 62.50% | 1.22% | 1.31% | 0.21% |
| +20 | damaged_retake | -0.17% | 55.56% | 1.50% | 1.42% | -0.09% |

## Pair consistency

| Horizon | Comparable FX | Healthy wins aligned return | Healthy wins hit rate | Healthy wins MFE-MAE |
|---|---:|---:|---:|---:|
| +5 | 7 | 5 | 5 | 4 |
| +10 | 7 | 6 | 6 | 6 |
| +20 | 7 | 5 | 4 | 5 |

## Per pair — 10-bar aligned return / hit rate

| Pair | Healthy n | Healthy return | Healthy hit | Damaged n | Damaged return | Damaged hit |
|---|---:|---:|---:|---:|---:|---:|
| EURUSD | 8 | 0.39% | 62.50% | 5 | 0.29% | 40.00% |
| USDJPY | 7 | -0.09% | 42.86% | 11 | -1.14% | 9.09% |
| GBPUSD | 6 | 0.61% | 66.67% | 9 | 0.01% | 55.56% |
| AUDUSD | 12 | 0.90% | 75.00% | 6 | 0.72% | 66.67% |
| EURCHF | 8 | 0.20% | 75.00% | 6 | -0.39% | 50.00% |
| USDCAD | 14 | -0.29% | 50.00% | 7 | -0.55% | 28.57% |
| USDCHF | 8 | -0.26% | 37.50% | 7 | 0.18% | 42.86% |

## Boundary

Reused-data price-relevance diagnostic only; no production trading rule or independent OOS claim.
