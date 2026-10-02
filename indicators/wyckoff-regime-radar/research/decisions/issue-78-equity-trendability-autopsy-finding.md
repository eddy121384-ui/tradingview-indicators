# Issue #78 — Equity Trendability / Broad-Oscillation Autopsy finding

Date: 2026-10-02

## Scope

This finding executes the frozen post-outcome diagnostic in
`issue-78-equity-trendability-autopsy-preregistration.md`.

It asks whether OOS3 weakness is concentrated in a slow **broad oscillation / large-box** environment, represented by:

- Low Trendability (ER63 / ER126 / ER252 composite percentile <33.33), and
- Wide 252-bar range-width percentile (>66.67).

This is descriptive mechanism work on an already-inspected cohort. It does not validate a production filter.

## Integrity

- exact OOS3 FIGI-set SHA:
  `017e9360402afa002dc0970088649e7c411c4f02333dec550f2432be3c0dd701`
- 300 stocks;
- 19,572 completed eligible episodes;
- 19,567 context-eligible episodes;
- context coverage: **99.974%**;
- frozen classifier blob:
  `1eec08e791403453853b589373bb2270c508c3bb`.

Only 5 completed episodes lack sufficient slow-context history.

## Primary result — broad-oscillation hypothesis is not supported

The preregistered composite support gate fails.

R0_NoDerisk by Trendability:

| Bucket | Equal-stock mean | Median stock | Positive stocks | MFE<4 | MFE>=8 | Bad structure |
|---|---:|---:|---:|---:|---:|---:|
| Low | -0.0057 | -0.1323 | 39.9% | 72.8% | 11.2% | 61.8% |
| Neutral | -0.1207 | -0.1549 | 35.9% | 74.0% | 11.0% | 62.0% |
| High | +0.0053 | -0.1945 | 41.4% | 74.4% | 11.2% | 60.4% |

There is no Low < Neutral < High expectancy monotonicity.

Low Trendability has slightly more bad-structure episodes than High, but it does **not** have more MFE<4 episodes and it is not the worst expectancy bucket.

The middle / Neutral bucket is the weakest on equal-stock mean.

## Direct large-box test — Low + Wide is not the sink

Within Low Trendability:

| Width | Equal-stock mean | Median stock | Positive stocks | MFE<4 | MFE>=8 | Bad structure |
|---|---:|---:|---:|---:|---:|---:|
| Narrow | -0.0086 | -0.1698 | 38.1% | 73.0% | 10.6% | 61.9% |
| Medium | -0.0290 | -0.2906 | 38.3% | 72.9% | 10.2% | 61.5% |
| Wide | **+0.1996** | -0.3378 | 35.7% | **70.1%** | **14.5%** | **60.3%** |

The preregistered prediction that Low + Wide would be worse than Low + Narrow / Medium fails in the opposite direction on equal-stock mean.

Low + Wide also has:

- lower MFE<4 share;
- higher MFE>=8 share;
- slightly lower bad-structure share.

Therefore **large slow ranges are not the main source of R0 damage**.

## Important tail nuance

Low + Wide is highly right-skewed.

Per-stock R0 mean harvest:

- mean: **+0.1996 ATR**
- median: **-0.3378 ATR**
- positive-stock fraction: **35.7%**
- after removing the top 1% positive stocks: **+0.0691 ATR**
- after removing the top 5% positive stocks: **-0.2009 ATR**

So a typical stock in Low + Wide is still negative, but the cell produces enough very large winners to make its equal-stock mean positive.

This is consistent with wide slow ranges sometimes containing major directional legs after long travel, rather than being uniformly hostile.

## Temporal robustness fails

For the preregistered robust eras, Low has better R0 expectancy than High in only **1 of 3** eras under the frozen comparison rule.

Examples:

- 2010–2014: Low -0.011 vs High +0.022;
- 2015–2019: Low +0.124 vs High -0.257;
- 2020–2026: Low -0.004 vs High -0.033.

There is no stable temporal Low-vs-High ordering.

## Direction and sleeve diagnostics

The previously observed direction asymmetry remains much larger than the Trendability effect.

R0_NoDerisk:

### Markdown

- Low: -0.189
- Neutral: -0.258
- High: -0.078

### Markup

- Low: +0.120
- Neutral: -0.014
- High: -0.025

Low Trendability is therefore not universally bad; for Markup it is the strongest of the three frozen buckets.

Across large / mid / small sleeves, the same lack of clean monotonicity remains.

## Research decision

### Reject the simple “large box is the main culprit” mechanism

The frozen Low-Trendability + Wide-Range proxy does not explain the OOS3 failure.

Do **not** create a production filter that simply suppresses:

- Low Trendability;
- Wide 252-bar ranges;
- Low + Wide cells.

### Narrow compression also remains unsupported

This is consistent with the earlier Compression Structure Stage 1B finding: pre-breakout narrowness is not a universal healthy-breakout dimension.

### What remains unresolved

The failure mechanism appears more local and path-dependent than a simple slow-context range regime.

The strongest replicated evidence remains:

- NoUsableB3 / P3 dominate failed-trend damage;
- P0 / P1 / P2 carry much better economics;
- early proof contains trend-size information but over-promotes failed structures;
- WarningFirst is portable risk control.

The next mechanism study should therefore focus on **durability between initial proof and structural acceptance**, rather than another static range-width filter.

Guardrail: no post-hoc filter or threshold may be promoted from this already-inspected cohort.

Refs #78, #138, #135, #132, #131, #80.
