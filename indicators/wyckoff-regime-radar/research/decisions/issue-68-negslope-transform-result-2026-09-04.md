# Issue #68 — NegSlope Transform Audit Result (2026-09-04)

Status: DISCOVERY ONLY / NO PNL / NO TUNING / FROZEN C-2.

## Shared window

2022-01-03 through 2023-12-29, 1D.

Primary contrast:
- FR10Y — adverse case.
- DE10Y — control that reaches materially more S2 effective flips.

## TradingView observations

### FR10Y
- valid population: 502; RAW S1 -> EFF S2 flips: 100.
- 20D bp slope avg: 9.71 bp; full-support bp rank: 54.27.
- positive/log-supported bp rank: 20.32.
- log-slope rank: 18.61; speedRank: 21.25; NegSlopeDull: 23.3.
- rolling 756-bar positive-close share: 58.72%; valid-speedZ share: 44.95%.
- average rank shift full-bp -> positive/log-supported bp: -33.95 points.

### DE10Y
- valid population: 449; RAW S1 -> EFF S2 flips: 156.
- 20D bp slope avg: 7.49 bp; full-support bp rank: 51.72.
- positive/log-supported bp rank: 11.46.
- log-slope rank: 10.60; speedRank: 12.32; NegSlopeDull: 8.16.
- rolling 756-bar positive-close share: 35.11%; valid-speedZ share: 29.77%.
- average rank shift full-bp -> positive/log-supported bp: -40.25 points.

## Interpretation

The raw 20D yield path does not explain the FR/DE split: bp slopes and full-support bp percentile ranks are similar.

The large divergence appears when the production log-price chain loses historical support on non-positive yield bars. The masked/valid support entering percentile ranking is much thinner for DE10Y than FR10Y. DE's positive-close and valid-speedZ shares are materially lower, and its bp percentile collapses farther once restricted to log-valid support.

Because production uses:

`negSlopeDullScore = f_gate(speedRank, 15, 55) * 100`

this sparse-support percentile distortion pushes DE speedRank below/near the lower gate threshold much more often, producing a much lower NegSlopeDull score. That suppresses the S1 downside-exhaustion gate and accidentally allows more S2 effective flips. FR retains more valid support, receives a higher speedRank / NegSlopeDull score, and therefore preserves S1 more often.

Thus DE's comparatively better Bull recognition is not evidence that the current transform is semantically sound. It is consistent with an accidental rescue caused by market-specific missing-history support in the log/percentile transform.

## Current root-cause hypothesis

Primary architecture issue:

**A percentile-ranked feature is being computed on a log-yield series whose historical validity depends on whether the yield was above zero. This makes the reference distribution market-specific in a way that is unrelated to current regime geometry.**

The FR/DE discrepancy is therefore best attributed to support-domain / normalization distortion rather than to simple bp move magnitude.

## Next falsification step

No production change yet. Build fixed-contract shadows that preserve the same current 20D direction concept but remove the market-specific missing-support effect, for example:

1. bp-slope percentile over a fully valid yield-level history;
2. a fixed-support comparison restricted to a common valid window across FR and DE;
3. production speedRank side-by-side with these shadows.

Test whether the FR/DE NegSlopeDull and S1-vs-S2 effective-gap discrepancy materially collapses without tuning any threshold or weight.

If the discrepancy collapses under a support-invariant shadow, classify this as a transform/domain architecture defect and only then design a repair candidate. If it does not, continue attribution downstream.
