# Issue #78 — Add-Risk Evidence Incrementality Preregistration

## Purpose

Phase 1 of the updated Issue #78 is already answered by the preregistered Participation Ramp study: beginning with controlled exposure materially reduces false-start damage, at the cost of delayed participation in genuine large trends.

Phase 2 asks a narrower question before any new sizing threshold is invented:

> **Once we know how much directional progress a live trend has already made, does directional path efficiency add stable incremental information about how much trend remains?**

This study is diagnostic. It does not select a production sizing rule and does not optimize numeric add-risk thresholds.

## Why this study comes before a new ramp

The completed Big Trend vs Failed Trend feature study identified two strong post-entry feature families:

1. cumulative direction-aligned progress;
2. directional path efficiency.

Those two features are related by construction: directional efficiency uses cumulative aligned progress as its numerator and total traveled path as its denominator.

Therefore a high standalone AUC for both features does **not** prove that both belong in an exposure rule.

The practical decision is binary:

- if efficiency adds little after controlling for progress, prefer a simpler progress-based ramp;
- if efficiency adds stable incremental information, preregister a later two-dimensional add-risk rule.

## Frozen sample

Reuse the accepted Issue #76 nine-market daily sample and completed known-start Markup / Markdown episodes used by the prior Issue #78 studies.

Markets:

- OANDA:EURUSD
- OANDA:GBPUSD
- OANDA:USDJPY
- TVC:US10Y
- TVC:DE10Y
- TVC:FR10Y
- TVC:GB10Y
- TVC:AU10Y
- TVC:JP10Y

This remains in-sample discovery evidence.

## Frozen checkpoints

Evaluate only two checkpoints already used in the completed feature study:

- after 5 completed daily moves following entry;
- after 10 completed daily moves following entry.

An episode is eligible at a checkpoint only if the formal Markup / Markdown regime is still alive through that checkpoint.

This conditioning is explicit. The 5- and 10-move studies answer:

> conditional on the trend having survived this long, what does the evidence observed so far say about the remaining path?

Do not compare checkpoint results as if all initial entries survive to both checkpoints.

## Frozen causal features

For checkpoint `k` in {5, 10}, using only the first `k` completed directional steps after entry:

### 1. Cumulative aligned progress

`cum_atr_k = sum(direction_aligned_move_i / entry_ATR)`

Higher is hypothesized to be better.

### 2. Directional path efficiency

`dir_eff_k = cum_atr_k / sum(abs(direction_aligned_move_i / entry_ATR))`

Equivalent to aligned net path / gross traveled path.

Range is approximately -1 to +1.

Higher means the path has traveled more cleanly in the intended direction.

No other feature family enters this study.

## Frozen forward outcomes

All primary outcomes begin **after** the checkpoint. Already-realized progress before the checkpoint is excluded from the outcome.

For each eligible episode and checkpoint measure:

1. **Remaining directional net move** in entry-ATR units from the checkpoint close to formal regime end.
2. **Remaining favorable excursion**: maximum additional favorable move reachable after the checkpoint, measured from the checkpoint close.
3. **Remaining adverse excursion**: maximum adverse move after the checkpoint, measured from the checkpoint close.
4. **Additional +2 ATR continuation flag**: whether remaining favorable excursion reaches at least +2 ATR.
5. **Additional +4 ATR continuation flag**: whether remaining favorable excursion reaches at least +4 ATR.
6. **Remaining regime life** in completed daily moves.

The +2 / +4 ATR landmarks are reused from existing Issue #76 / #78 discovery buckets. They are not searched in this study.

## Normalization and ranking

Primary comparisons use within-market percentile ranks so that no market with a naturally different feature scale dominates the result.

At each checkpoint separately:

- compute within-market percentile rank for cumulative progress;
- compute within-market percentile rank for directional efficiency;
- form progress quintiles Q1–Q5;
- form efficiency quintiles Q1–Q5.

Direction is not separately optimized. Markup / Markdown splits are diagnostics only.

## Primary analyses

### A. Progress-only gradient

Across progress quintiles Q1–Q5 report equal-market means / medians for all frozen forward outcomes.

Question:

> Does more realized directional progress imply better remaining continuation, or has much of the opportunity already been consumed?

### B. Efficiency-only gradient

Across efficiency quintiles Q1–Q5 report the same outcomes.

This reproduces the standalone relationship using strictly forward-from-checkpoint outcomes rather than final episode labels.

### C. Incrementality of efficiency conditional on progress — primary test

Within each progress quintile, compare lower vs higher efficiency ranks.

Report a 5 × 5 progress-quintile × efficiency-quintile grid where sample size permits.

Primary interpretation focuses on whether, **at similar already-realized progress**, higher efficiency is associated with:

- larger remaining directional net move;
- larger remaining favorable excursion;
- higher +2 / +4 ATR continuation rates;
- lower remaining adverse excursion;
- longer remaining regime life.

Do not collapse this grid into one optimized cutoff.

### D. Incrementality of progress conditional on efficiency

Mirror analysis C by inspecting progress gradients within efficiency quintiles.

This identifies which feature carries the stronger independent ordering information.

## Cross-market robustness

For each checkpoint and primary contrast report:

- equal-market mean effect;
- equal-market median effect;
- count of markets with the expected sign;
- Markup and Markdown diagnostic splits.

A feature is not considered universal merely because pooled observations look strong.

## Temporal robustness

Repeat the key progress, efficiency, and conditional-incrementality summaries for:

- 2010–2014;
- 2015–2019;
- 2020–2026.

The 2015–2019 slice must remain visible as a separate stress era. Do not tune it away.

Sparse cells must be labeled as such rather than silently pooled into a favorable result.

## Decision rules

### Efficiency earns promotion to a later add-risk rule only if all are broadly true

1. At both the 5- and 10-move checkpoints, higher efficiency shows the expected forward orientation after controlling for progress.
2. The effect is present in a clear majority of eligible markets rather than being driven by one market.
3. The conditional gradient is reasonably monotonic or at least shows consistent endpoint separation.
4. The effect is not dependent on only Markup or only Markdown.
5. The relationship remains visible across the temporal slices where sample size is adequate, including 2015–2019.

### If efficiency fails this incremental test

Prefer the simpler architecture:

> trend progress earns exposure; path efficiency remains descriptive / diagnostic only.

Do not rescue efficiency by changing horizons, adding market-specific thresholds, splitting long / short rules, or searching alternative efficiency formulas in the same pass.

## Guardrails

- no classifier changes;
- no new entry-quality gate;
- no optimization of exposure percentages;
- no threshold search over efficiency values;
- no threshold search over cumulative progress values;
- no new lookback horizons beyond the frozen 5 / 10 checkpoints;
- no market-specific rules;
- no separate Markup / Markdown policies;
- no final-MFE label as a live feature;
- no pre-checkpoint price movement counted as a post-checkpoint outcome;
- no production claim from this discovery sample.

## Relationship to existing Issue #78 work

Phase 1 result is already established by the Participation Ramp study:

- controlled initial exposure reduces short-lived false-trend damage broadly across markets;
- delayed participation necessarily gives up some genuine large-trend harvest;
- Excursion-Proof preserved more large-trend participation than age-only Persistence;
- Persistence + Health added complexity without a clear frontier improvement.

The completed Big Trend vs Failed Trend feature study then showed that post-entry cumulative progress and directional path efficiency are the strongest stable feature families at 5 / 10 completed moves.

This preregistration is the bridge between those two findings and the next actual sizing rule.

Refs #78, #80 and #76.
