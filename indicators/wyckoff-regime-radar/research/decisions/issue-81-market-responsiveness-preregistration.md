# Issue #81 — Market Responsiveness preregistration

Date: 2026-09-15

## Purpose

Issue #78 established that static entry-time context is only modestly informative, while the first 5–10 completed daily moves after a fresh formal Markup / Markdown entry carry much stronger Large-vs-Failed separation.

This study asks a narrower question inspired by discretionary trader language such as `this market is responding correctly`:

> After a probe is already live, which observable properties of the early path distinguish trends that later become Large from trends that fail to expand, and which properties add information beyond cumulative directional progress alone?

This is a diagnostic study. It is not a classifier rewrite, entry filter, production score, or position-sizing policy selection.

## Frozen sample and labels

Use the same accepted Issue #76 nine-market daily universe and event contract used by Issue #78:

- OANDA:EURUSD
- OANDA:GBPUSD
- OANDA:USDJPY
- TVC:US10Y
- TVC:DE10Y
- TVC:FR10Y
- TVC:GB10Y
- TVC:AU10Y
- TVC:JP10Y

Use completed known-start formal trend episodes reconstructed exactly as in the Issue #78 Big Trend vs Failed Trend study.

Labels remain frozen:

- Failed / small: final episode directional MFE `< 4 entry ATR`.
- Large: final episode directional MFE `>= 8 entry ATR`.
- `4 <= MFE < 8` is excluded from the primary binary contrast.

No relabeling or threshold optimization is allowed.

## Information timing

Only post-entry causal information is studied here.

- **E5**: first 5 completed daily moves after entry.
- **E10**: first 10 completed daily moves after entry.

An episode is eligible at E5 / E10 only if the formal trend is still alive long enough for that decision point to exist in real time.

E5 and E10 are sizing / confidence information, never entry-time predictors.

## Frozen responsiveness features

All price-path moves are direction-aligned and normalized consistently with the Issue #78 entry-ATR convention.

### 1. Cumulative directional progress — baseline

`cum_atr`

Sum of the first `k` aligned daily moves.

Expected orientation: higher is better.

This is the already-established baseline and is included so every other feature can be judged against it.

### 2. Directional path efficiency — baseline

`dir_eff`

`cumulative aligned move / total absolute early path`.

Expected orientation: higher is better.

### 3. Favorable-day consistency

`favorable_day_share`

Fraction of the first `k` aligned daily moves that are strictly positive.

Expected orientation: higher is better.

Question: does a healthy trend win more days, rather than relying on one large jump surrounded by noise?

### 4. New favorable extreme rate

`new_high_rate`

Fraction of the first `k` completed moves that end at a new favorable cumulative close-path extreme relative to all prior completed moves since entry.

Expected orientation: higher is better.

Question: does the market repeatedly extend the favorable frontier?

### 5. Maximum adverse excursion from entry

`mae_atr`

Magnitude of the worst cumulative move below entry during the first `k` completed moves, in entry ATR. Zero if the path never goes below entry.

Expected orientation: lower is better.

Question: how much pain does the market inflict before proving itself?

### 6. Maximum intra-window pullback

`max_pullback_atr`

Largest decline from any prior favorable cumulative close-path extreme to a later cumulative point within the first `k` completed moves.

Expected orientation: lower is better.

This differs from end-of-window giveback: a trend can recover by E5 / E10 after suffering an ugly interim pullback.

### 7. Early activity expansion

`activity_ratio20`

Mean absolute aligned move per bar during the first `k` moves divided by the mean absolute move per bar over the 20 completed pre-entry moves, using the same entry-ATR normalization.

Expected orientation: higher is better.

Question: does a real trend arrive with expanding realized movement rather than remaining in the same low-energy texture?

This is a volatility / activity diagnostic only; it is not assumed to be directional by itself.

### 8. Time to first +0.5 ATR proof

`bars_to_half_atr`

Number of completed daily moves required for cumulative aligned progress to first reach `+0.5 entry ATR` within the E5 / E10 window. If not reached, encode `k + 1`.

Expected orientation: lower is better.

The `0.5 ATR` proof level is frozen because it already exists in the earlier Issue #78 Excursion-Proof architecture; it is not selected from this study's outcomes.

## Primary evaluation

For each feature separately at E5 and E10:

1. per-market Large-vs-Failed ROC AUC using the frozen expected orientation;
2. equal-market mean and median AUC;
3. number of markets with AUC > 0.50;
4. within-market quintiles over eligible episodes, checking whether Large-share rises and Failed-share falls with feature quality;
5. Markup / Markdown diagnostic slices;
6. common-era diagnostics for 2010–2014, 2015–2019, 2020–2026.

No best cutoff is selected.

## Critical incremental test: beyond cumulative progress

Many responsiveness features may simply re-express `cum_atr`. Therefore each non-baseline feature must also face a conditional test.

Within each market and information set:

1. take eligible Large / Failed episodes;
2. rank them by `cum_atr`;
3. split cumulative proof into **three coarse within-market bands** using within-market percentile rank: lower third, middle third, upper third;
4. compute the candidate feature's Large-vs-Failed AUC separately inside each band when both classes have at least 3 observations;
5. average valid band AUCs within market, then aggregate those market-level conditional AUCs equally across markets.

This is deliberately coarse and preregistered. Do not alter the number of bands after seeing results.

Interpretation:

- strong unconditional AUC but conditional AUC near 0.50 => mostly a restatement of cumulative move;
- conditional AUC meaningfully above 0.50 across markets => candidate contains incremental path-quality information beyond how far price already traveled.

No multivariate optimizer, regression search, decision tree, or feature-selection algorithm is allowed.

## Temporal falsification

Repeat the primary separation diagnostics in the frozen common eras:

- 2010–2014
- 2015–2019
- 2020–2026

The key stress slice remains 2015–2019. A feature does not pass merely because its level differs between good and bad calendar eras; it should distinguish Large from Failed inside the era where sample size permits.

Conditional cumulative-band diagnostics are primary on the all-years sample and descriptive by era only when sample support is adequate. Sparse era cells must remain sparse rather than be rescued by relaxing minimum counts.

## Survivor interpretation

### Strong survivor

Most of:

- useful equal-market unconditional separation;
- expected orientation in a clear majority of markets;
- reasonably ordered quintiles;
- survives both Markup and Markdown diagnostics;
- retains within-2015–2019 separation where eligible;
- and shows incremental conditional AUC above cumulative-proof bands.

### Weak survivor

Useful unconditional separation but mostly redundant with cumulative progress, temporally sparse, or inconsistent after conditioning.

May remain descriptive but should not earn a separate component in a later responsiveness composite without new evidence.

### Reject

Near-chance / reversed AUC, poor cross-market consistency, badly non-monotonic quintiles, or no credible incremental information.

Do not rescue rejected features by changing windows, thresholds, or direction-specific rules after outcomes are visible.

## Explicit guardrails

- frozen Issue #68 classifier semantics remain unchanged;
- no asset-class-specific rules;
- no separate Markup / Markdown parameter sets;
- no 2015–2019-specific logic;
- no E0 feature expansion in this study;
- no future information beyond the stated E5 / E10 decision point;
- no search over proof thresholds;
- no production Market Responsiveness / Trend Quality composite yet;
- any later sizing frontier or composite requires a separate preregistration.

## Intended outputs

- reproducible analyzer;
- compact all-years / era separation table;
- within-market quintile table;
- direction diagnostic table;
- cumulative-proof-conditioned incremental table;
- concise survivor / reject finding.

This preregistration is frozen before Issue #81 responsiveness outcomes are inspected.

Refs #81 #78 #76 #68.
