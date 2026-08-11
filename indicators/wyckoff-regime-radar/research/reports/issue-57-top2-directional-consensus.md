# Issue #57 — Top-2 directional consensus burned-data diagnostic

**Hypothesis-development only. All seven FX pairs in this report are already burned / observed.**

Primary rule: Top1 and Top2 six-stage weights must be in the same directional family and sum to at least **90%**.

## Aggregate comparison across seven burned FX pairs

| Signal | H | Median aligned return | Median hit rate | Median coverage | Positive pairs | Positive halves |
|---|---:|---:|---:|---:|---:|---:|
| Top2 same-dir >=90% | 5 | -0.06% | 48.23% | 26.14% | 1/7 | 2/14 |
| Top2 same-dir >=90% | 10 | -0.13% | 47.74% | 26.03% | 2/7 | 3/14 |
| Top2 same-dir >=90% | 20 | -0.14% | 44.16% | 25.88% | 1/7 | 4/14 |
| Top2 same-dir >=90% | 60 | -0.38% | 46.32% | 25.77% | 2/7 | 5/14 |
| Top1 family | 5 | -0.06% | 47.33% | 55.82% | 2/7 | 4/14 |
| Top1 family | 10 | -0.08% | 47.71% | 55.73% | 0/7 | 3/14 |
| Top1 family | 20 | -0.09% | 44.68% | 55.55% | 2/7 | 2/14 |
| Top1 family | 60 | -0.35% | 44.31% | 54.79% | 2/7 | 6/14 |
| Formal family | 5 | -0.03% | 48.17% | 52.82% | 1/7 | 3/14 |
| Formal family | 10 | -0.03% | 48.34% | 52.72% | 2/7 | 2/14 |
| Formal family | 20 | -0.08% | 46.97% | 52.52% | 2/7 | 4/14 |
| Formal family | 60 | -0.33% | 45.81% | 51.97% | 2/7 | 7/14 |
| Formal trend-only | 5 | -0.05% | 48.63% | 34.53% | 3/7 | 5/14 |
| Formal trend-only | 10 | -0.07% | 50.59% | 34.39% | 3/7 | 4/14 |
| Formal trend-only | 20 | -0.02% | 50.11% | 34.24% | 3/7 | 5/14 |
| Formal trend-only | 60 | -0.32% | 49.93% | 33.89% | 1/7 | 2/14 |

## Trading diagnostic — median across seven pairs

| Signal | Net ann. return | Sharpe | Exposure |
|---|---:|---:|---:|
| Top2 same-dir >=90% | -1.18% | -0.28 | 26.26% |
| Top1 family | -3.04% | -0.46 | 55.90% |
| Formal family | -1.87% | -0.27 | 52.90% |
| Formal trend-only | -1.06% | -0.16 | 34.60% |

## Top-2 threshold sensitivity (NOT parameter selection)

| Threshold | H | Median aligned return | Median hit rate | Median coverage |
|---:|---:|---:|---:|---:|
| 80% | 5 | -0.06% | 48.11% | 27.39% |
| 80% | 10 | -0.12% | 47.84% | 27.28% |
| 80% | 20 | -0.11% | 44.27% | 27.14% |
| 80% | 60 | -0.36% | 46.68% | 27.05% |
| 85% | 5 | -0.06% | 47.98% | 27.06% |
| 85% | 10 | -0.12% | 47.70% | 26.95% |
| 85% | 20 | -0.13% | 44.04% | 26.81% |
| 85% | 60 | -0.38% | 46.44% | 26.71% |
| 90% | 5 | -0.06% | 48.23% | 26.14% |
| 90% | 10 | -0.13% | 47.74% | 26.03% |
| 90% | 20 | -0.14% | 44.16% | 25.88% |
| 90% | 60 | -0.38% | 46.32% | 25.77% |
| 95% | 5 | -0.08% | 47.50% | 24.43% |
| 95% | 10 | -0.11% | 46.82% | 24.31% |
| 95% | 20 | -0.17% | 44.16% | 24.16% |
| 95% | 60 | -0.37% | 46.43% | 24.02% |

Interpretation boundary: 90% is the primary user-originated hypothesis. 80/85/95 are sensitivity diagnostics only and must not replace 90% because one happens to backtest better.

Any positive result here earns only a new untouched test; it is not independent validation.
