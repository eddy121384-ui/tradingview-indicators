# Issue #78 — Big Trend vs Failed Trend Feature Study preregistration

Date: 2026-09-15

## Purpose

The post-repair research has established that the frozen daily classifier can identify real local directional legs, but the economic value is not temporally stable. The common 2015–2019 slice is the clearest failure regime: trend episodes still form, yet volatility-normalized follow-through is much weaker and large trends are rarer.

This study asks a narrower and more causal question:

> At trend entry, or after only a small amount of early causal evidence, what observable characteristics distinguish episodes that later grow into large trends from episodes that fail to expand?

This is a feature-diagnostic study. It is **not** a classifier rewrite, exposure-policy selection, optimizer, or attempt to tune away 2015–2019.

## Frozen sample and labels

Use the already accepted Issue #76 daily nine-market universe and feed contract:

- OANDA:EURUSD
- OANDA:GBPUSD
- OANDA:USDJPY
- TVC:US10Y
- TVC:DE10Y
- TVC:FR10Y
- TVC:GB10Y
- TVC:AU10Y
- TVC:JP10Y

Use the existing completed known-start formal trend episodes reconstructed exactly as in the Issue #78 Participation Ramp / Economic Value analyses.

Primary labels are frozen before inspecting feature outcomes:

- **Failed / small trend:** final episode directional MFE `< 4 entry ATR`.
- **Large trend:** final episode directional MFE `>= 8 entry ATR`.
- Episodes with `4 <= MFE < 8` are excluded from the primary binary contrast and retained only for secondary ordinal / bucket diagnostics.

No threshold optimization over 4 / 8 ATR is permitted in this study.

## Causality / information sets

Two information sets must remain separate.

### E0 — entry-close information only

For a fresh formal trend entry at bar `t`, E0 features may use only rows / moves whose information is complete by the close of `t`.

The Issue #76 field `move1[t]` is a forward `t -> t+1` move and therefore **must not** be used in E0 features. E0 trailing path calculations may use `move1` only through row `t-1`.

### E5 / E10 — early proof information

Early-confirmation features may additionally use the first 5 or first 10 completed daily moves after entry.

These features are not entry predictors. They answer a different sizing question:

> once a probe is already on, does early price behavior identify which trends deserve larger participation?

E0, E5 and E10 results must never be pooled or described as if they were available at the same time.

## Frozen feature families

The first pass is intentionally small and mechanistic. No indicator zoo and no calendar labels.

### A. Pre-entry path efficiency

For trailing windows `20 / 63 / 126` daily bars:

1. absolute efficiency ratio:
   `abs(net displacement) / total absolute path`;
2. direction-aligned efficiency:
   `trend_direction * net displacement / total absolute path`.

Hypothesis: large trends should, on average, enter from a cleaner directional path than failed trends. A low absolute efficiency can also identify `走很多、沒走遠` behavior.

### B. Pre-entry directional displacement

For `20 / 63 / 126` bars:

`trend_direction * trailing net displacement / entry ATR`.

Hypothesis: large trends may have stronger directional lead-in. This is distinct from efficiency because a market can move efficiently but only a small distance.

### C. Structural range escape / location

Using reconstructed close-path values known at entry and the prior `63 / 126 / 252` closes:

1. direction-aligned distance beyond the prior rolling close range, in entry ATR;
2. direction-aligned close location within the prior rolling close range.

Positive escape means the entry close has moved beyond the previous range boundary in the trend direction. Range location is descriptive and does not require an actual breakout.

Hypothesis: large trends should show more genuine structural escape than failed trends, but a wide-range market can still host valuable internal trends; therefore this is a diagnostic, not a hard gate.

### D. Recent regime churn

Using only formal-stage history known by entry:

- formal stage-change count over prior `20 / 63` bars;
- fresh formal trend-entry count over prior `63 / 126` bars;
- fraction of prior `63 / 126` bars spent in directional trend states (Markup / Markdown).

Hypothesis: failed trends should be more common after repeated state flipping / churn. Directional occupancy is left unsigned; direction-specific policy is not allowed.

### E. Early proof after the probe is live

At E5 and E10, compute from the first completed moves after entry:

- cumulative direction-aligned move / entry ATR;
- early MFE / entry ATR;
- giveback from early favorable close-path extreme / entry ATR;
- directional path efficiency over the observed early moves.

Hypothesis: large trends should accumulate proof faster, with higher early efficiency and less immediate giveback.

## Primary evaluation

The primary question is **cross-market separation**, not the best threshold.

For each feature and information set:

1. compare Large vs Failed per-market medians / means;
2. compute per-market ROC AUC for the frozen expected orientation where applicable;
3. report equal-market mean / median AUC and count of markets with AUC above 0.50;
4. convert the feature to within-market quintiles over all eligible trend episodes and test whether Large-share rises and Failed-share falls monotonically across quintiles;
5. report equal-market Persistence + Gentle episode return by quintile as an economic diagnostic only.

No best cut-point, decision tree split, optimizer, Sharpe maximization, or market-specific threshold selection is allowed.

## Temporal falsification

Repeat the feature diagnostics in the previously frozen common eras:

- 2010–2014
- 2015–2019
- 2020–2026

The all-years / all-market result is primary.

2015–2019 is a **stress slice, not a training target**. A feature that merely labels 2015–2019 as different but does not separate Large from Failed **within that era** is not sufficient evidence of general trend quality.

Direction slices (Markup / Markdown) are diagnostic only and cannot create separate parameter sets.

## Success / failure interpretation

A feature family is a serious survivor only if it shows most of the following without retuning:

- useful Large-vs-Failed separation in equal-market aggregation;
- the expected sign in a clear majority of the nine markets;
- reasonably monotonic quintile behavior;
- some within-era separation, including 2015–2019 rather than only across eras;
- no dependence on a single market or a single direction.

Weak, non-monotonic or market-specific features should be rejected or downgraded rather than rescued by changing windows or thresholds after results are visible.

## Explicit guardrails

- frozen Issue #68 classifier semantics remain unchanged;
- no asset-class-specific rules;
- no separate long / short policies;
- no 2015–2019-specific feature or threshold;
- no use of future information in E0;
- E5 / E10 may only inform post-entry sizing research;
- no production Trend Quality score is created in this pass;
- any later composite must be separately preregistered and then challenged on new heterogeneous / weekly / prospective data.

## Intended outputs

- reproducible analyzer;
- episode-level feature table;
- per-feature cross-market separation table;
- within-market quintile table;
- temporal / within-era separation table;
- a concise finding that names survivors, rejects weak families, and states what should be tested next.

This preregistration is frozen before the Big-vs-Failed feature outcomes are inspected.