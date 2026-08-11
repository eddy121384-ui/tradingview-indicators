# Issue #57 — Top-2 consensus: v0.5 vs v0.6 on burned data

**Development diagnostic only; all seven FX fixtures are already burned.**

Rule held fixed across engines: Top1 and Top2 six-stage weights must share a directional family and sum to at least **90%**.

| Engine | H | Median aligned return | Median hit rate | Median coverage | Positive pairs | Positive halves |
|---|---:|---:|---:|---:|---:|---:|
| v05 | 5 | -0.07% | 48.13% | 25.80% | 1/7 | 2/14 |
| v05 | 10 | -0.12% | 46.60% | 25.77% | 2/7 | 3/14 |
| v05 | 20 | -0.12% | 44.28% | 25.80% | 1/7 | 4/14 |
| v05 | 60 | -0.40% | 45.89% | 25.73% | 2/7 | 4/14 |
| v06 | 5 | -0.06% | 48.23% | 26.14% | 1/7 | 2/14 |
| v06 | 10 | -0.13% | 47.74% | 26.03% | 2/7 | 3/14 |
| v06 | 20 | -0.14% | 44.16% | 25.88% | 1/7 | 4/14 |
| v06 | 60 | -0.38% | 46.32% | 25.77% | 2/7 | 5/14 |

## Trading diagnostic — median across seven pairs

| Engine | Net ann. return | Sharpe | Exposure |
|---|---:|---:|---:|
| v05 | -1.00% | -0.27 | 25.93% |
| v06 | -1.18% | -0.28 | 26.26% |

Interpretation boundary: if v0.5 materially outperforms v0.6 here, investigate whether the v0.6 redesign altered useful weight-agreement structure before abandoning the user's hypothesis. If both fail, the next question is whether the user's live observation depended on full-indicator witness layers rather than the price-only core.
