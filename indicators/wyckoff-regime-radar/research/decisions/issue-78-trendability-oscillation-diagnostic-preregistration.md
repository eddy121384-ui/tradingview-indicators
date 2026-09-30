# Issue #78 — Trendability / Oscillation Diagnostic Preregistration

## Purpose

Diagnose the 2015–2019 failure regime without changing the classifier or exposure rules.

The working question is:

> When the formal classifier identifies Markup / Markdown, can a slower, causal market-context layer distinguish an **expansion / trendable environment** from a **broad oscillation environment** in which local directional legs repeatedly fail to extend?

This is a diagnostic layer only. It is not authorized to suppress signals, change position size, or alter Issue #68 classifier semantics in this pass.

## Motivation already observed before this preregistration

The Issue #78 economic-value audit found that all frozen policies lose equal-market gross edge in the preregistered 2015–2019 era, while the same policies are positive in the surrounding eras. Visual inspection of US10Y shows a plausible broad-range environment containing many local directional legs.

Do not use this observation to tune a threshold. The purpose of this pass is to measure whether a pre-existing, universal path-efficiency concept captures that environment across markets.

## Frozen sample

Use the same accepted Issue #76 nine-market 1D universe and representation convention:

- OANDA:EURUSD
- OANDA:GBPUSD
- OANDA:USDJPY
- TVC:US10Y
- TVC:DE10Y
- TVC:FR10Y
- TVC:GB10Y
- TVC:AU10Y
- TVC:JP10Y

Primary era slices remain unchanged:

- 2010–2014
- 2015–2019
- 2020–2026

## Frozen trendability metric family

Use **path efficiency**, equivalent in spirit to an efficiency ratio:

`ER(L) = abs(modelPrice[t] - modelPrice[t-L]) / sum(abs(modelPrice[i] - modelPrice[i-1]), i=t-L+1..t)`

Interpretation:

- ER near 1: most travelled distance became net displacement — expansion / trendable path.
- ER near 0: substantial travelled distance produced little net displacement — oscillatory / mean-reverting path.

Use the same `modelPrice` representation already frozen by Issue #68:

- Yield Level for yield series under Auto;
- Price Log for price series under Auto.

No ATR normalization is required for ER because numerator and denominator use the same units.

## Frozen horizons

Measure three standard slow-context horizons before viewing results:

- `63` bars — approximately one quarter;
- `126` bars — approximately half a year;
- `252` bars — approximately one trading year.

Do not search alternative lengths in this pass.

## Cross-market normalization

For each horizon, convert raw ER to its rolling within-market percentile rank using the existing classifier's frozen `rankLen = 756` bar context where history is available.

Define:

`TrendabilityScore = mean(ER63_percentile, ER126_percentile, ER252_percentile)`

The equal-weight average is frozen before results. No horizon receives an optimized weight.

For descriptive buckets only:

- Low Trendability: score < 33.33
- Neutral: 33.33–66.67
- High Trendability: > 66.67

These are fixed terciles for interpretation, not production thresholds.

## Primary diagnostics

### A. Era diagnosis

For each market and equal-market aggregate, report by era:

- median raw ER63 / ER126 / ER252;
- median TrendabilityScore;
- share of formal Markup / Markdown bars in Low / Neutral / High Trendability;
- share of fresh formal trend entries occurring in each bucket.

Primary question: is 2015–2019 systematically lower-trendability than 2010–2014 and 2020–2026?

### B. Outcome monotonicity

Without changing any strategy rule, condition completed known-start Markup / Markdown episodes on the TrendabilityScore observable at episode entry.

Report by Low / Neutral / High bucket:

- episode count;
- median episode duration;
- median favorable excursion;
- share reaching >=4 ATR favorable excursion;
- share reaching >=8 ATR favorable excursion;
- Formal Hold normalized mean episode return;
- Persistence + Gentle normalized mean episode return.

Primary question: does higher entry-time trendability correspond to better subsequent trend extension and economic value?

### C. Within-era discrimination

Within 2015–2019 only, compare the same outcome metrics across Low / Neutral / High trendability buckets.

This is crucial: a useful diagnostic should distinguish better and worse opportunities **inside** the bad era, not merely label the era after the fact.

## Visual audit

Create a research-only TradingView visualizer that shows:

- ER63, ER126 and ER252 percentile lines optionally;
- the composite TrendabilityScore prominently;
- fixed 33.33 / 66.67 reference lines;
- simple labels: `Oscillation / Neutral / Expansion`;
- formal regime background for context if practical, without changing classifier semantics.

The visualizer is not a trading signal and must not automatically modify Issue #78 exposure.

## Data requirement

Existing Issue #76 forward logs do not contain the full continuous pre-entry path needed to reconstruct 63/126/252-bar ER reliably across unclassified gaps. Therefore quantitative cross-market validation requires a new logger/export or equivalent continuous source.

Do not approximate missing path segments from formal-stage-only rows and present them as valid ER evidence.

The first implementation step is therefore:

1. build the visualizer and a compact logger using the frozen classifier representation;
2. perform manual visual smoke on US10Y;
3. only then collect the nine-market evidence if the metric behaves as intended visually.

## Guardrails

- no classifier tuning;
- no exposure-policy tuning;
- no market-specific thresholds;
- no separate FX / rates rules;
- no search over lookback lengths or percentile boundaries;
- no using future episode outcomes to define the score;
- no claiming 2015–2019 is solved merely because the score is visually low;
- if trendability has no monotonic relationship with future extension, reject or downgrade the hypothesis rather than tune it to fit.

Refs #78, #80, #76.
