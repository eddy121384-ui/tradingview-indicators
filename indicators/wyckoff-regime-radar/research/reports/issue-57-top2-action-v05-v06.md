# Issue #57 — Action-compatible Top-2 consensus, v0.5 vs v0.6

**Burned-data / price-only diagnostic only.**

Frozen Pine semantic correction: bullish consensus is the pair **Markup (2) + Re-accumulation (3)**; bearish consensus is **Markdown (5) + Redistribution (6)**. Top1+Top2 must sum to at least **90%**.

| Engine | H | Median aligned return | Median hit rate | Median coverage | Positive pairs | Positive halves | Signal origins |
|---|---:|---:|---:|---:|---:|---:|---:|
| v05 | 5 | -0.13% | 47.02% | 6.47% | 1/7 | 5/14 | 1157 |
| v05 | 10 | -0.18% | 46.32% | 6.49% | 2/7 | 4/14 | 1157 |
| v05 | 20 | -0.43% | 41.94% | 6.51% | 1/7 | 3/14 | 1145 |
| v05 | 60 | -1.04% | 46.89% | 6.62% | 1/7 | 2/14 | 1113 |
| v06 | 5 | -0.14% | 46.15% | 7.52% | 1/7 | 5/14 | 1258 |
| v06 | 10 | -0.18% | 47.30% | 7.53% | 1/7 | 5/14 | 1258 |
| v06 | 20 | -0.39% | 42.71% | 7.52% | 1/7 | 3/14 | 1246 |
| v06 | 60 | -0.81% | 47.85% | 7.26% | 1/7 | 2/14 | 1211 |

## Trading diagnostic — median across seven pairs

| Engine | Net ann. return | Sharpe | Exposure |
|---|---:|---:|---:|
| v05 | -0.41% | -0.15 | 6.50% |
| v06 | -0.60% | -0.17 | 7.54% |

Boundary: this fixes stage-direction semantics but still does not reproduce v0.5.2.1 default Volume Auto. A failure here does not yet falsify the user's live-dashboard observation.
