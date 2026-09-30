# Issue #78 — Daily Trigger × Weekly Sizing Context Preregistration

## Purpose

Test the user-facing hypothesis that the daily classifier should provide the early probe / participation signal while the weekly classifier should act as a slower sizing context rather than a mandatory entry gate.

Working product statement:

> **Daily tells us whether to participate and in which direction. Weekly tells us how much confidence / exposure that daily trend deserves. Daily trend health tells us how much of that exposure should still be retained.**

This is a research extension of Issue #78. It does not change the frozen Issue #68 classifier and does not authorize production policy changes.

## Motivation

The 2015–2019 economic-value audit showed that all frozen daily-only management policies lost equal-market gross expectancy in that era. Visual inspection of US10Y also showed an important distinction:

- a market can remain inside a very wide multi-year structural range while still producing economically meaningful multi-month trend legs;
- therefore `range vs trend` at a multi-year scale must **not** be used as a hard veto;
- the research question is instead whether a slower weekly context can distinguish daily trends that deserve larger sizing from daily trends that should remain only probe-sized.

## Frozen sample and provenance

Daily outcomes remain the accepted Issue #76 sample:

- OANDA:EURUSD
- OANDA:GBPUSD
- OANDA:USDJPY
- TVC:US10Y
- TVC:DE10Y
- TVC:FR10Y
- TVC:GB10Y
- TVC:AU10Y
- TVC:JP10Y

The daily classifier remains the frozen Issue #68 RC source. No daily stage parameters are changed.

Weekly formal regime context must be produced by running the **same frozen Issue #68 RC classifier code on native 1W bars with its existing parameters unchanged**. This intentionally treats weekly formal regime as a slower structural context; it is not a calendar-equivalent reparameterization of the daily classifier.

## Causal weekly availability rule

No incomplete weekly bar may influence a daily decision.

The weekly logger must export both `week_open_time` and `week_close_time`. For a daily decision at daily bar open timestamp `t`, use only the latest weekly observation satisfying:

`week_close_time <= t`

If no completed weekly observation exists, weekly context is unavailable.

This is the primary anti-lookahead contract.

## Weekly Trendability definition

Weekly Trendability is a separate context diagnostic and **does preserve calendar-ish semantics** relative to the daily 63 / 126 / 252-day experiment:

- 13 weeks ≈ one quarter;
- 26 weeks ≈ half-year;
- 52 weeks ≈ one year.

For each horizon `L`:

`ER_L = abs(x_t - x_{t-L}) / sum(abs(x_i - x_{i-1}), i=t-L+1..t)`

where `x` is the frozen representation-aware model series:

- Price Log for price assets;
- Yield Level for yield feeds.

Each weekly ER is percentile-ranked against the same market's trailing **156 completed weeks** (~3 years), matching the intent of the daily 756-trading-day normalization.

Weekly Trendability Composite:

`WTrend = mean(rank(ER13), rank(ER26), rank(ER52))`

Frozen descriptive boundary for this study:

- `WTrend > 66.67` = high weekly trendability;
- otherwise = not-high weekly trendability.

The old `<33.33 / 33.33–66.67 / >66.67` labels remain descriptive only. This study deliberately uses only one high/not-high split to minimize degrees of freedom.

## Frozen policy comparison

All policies use the same daily direction, daily Persistence participation ramp, and daily Gentle + damage-latch health logic already defined before this study unless noted.

### A. Daily-only benchmark

Existing practical candidate:

- fresh daily Markup / Markdown starts at 25% directional exposure;
- Persistence Ramp cap = 25 / 50 / 75 / 100% at daily regime ages 0 / 5 / 10 / 20 bars;
- Daily Gentle health cap = 100 / 100 / 75 / 50 / 25% across the frozen `<0.5 / 0.5–1 / 1–2 / 2–4 / 4+ ATR` giveback buckets;
- damage latch retains the existing re-risk rule;
- final exposure = `min(DailyParticipationCap, DailyHealthCap)`.

### B. Weekly formal-direction sizing context

Add a weekly cap without Weekly Trendability:

- completed weekly formal regime same direction as daily trend: `WeeklyCap = 100%`;
- completed weekly formal regime opposite direction: `WeeklyCap = 25%`;
- weekly formal regime is transitional / non-trend / unavailable: `WeeklyCap = 50%`.

Final exposure:

`min(DailyParticipationCap, DailyHealthCap, WeeklyCap)`

This tests whether weekly direction alone adds value.

### C. Weekly formal-direction + Trendability sizing context

Freeze the following cap:

- weekly formal regime opposite direction: `25%`;
- weekly formal regime transitional / non-trend / unavailable: `50%`;
- weekly formal regime same direction but `WTrend <= 66.67` or WTrend unavailable: `50%`;
- weekly formal regime same direction and `WTrend > 66.67`: `100%`.

Final exposure:

`min(DailyParticipationCap, DailyHealthCap, WeeklyCap)`

Interpretation: the weekly layer never vetoes the daily probe. It only controls whether exposure is allowed to scale beyond probe / reduced size.

## Why there is no 75% weekly state in the first pass

The first pass deliberately uses only 25 / 50 / 100% weekly caps. A 75% context state would add another discretionary boundary without answering the basic question of whether weekly context has incremental value.

## Primary metrics

Use the same causal episode accounting conventions as the Issue #78 economic-value audit.

For each policy report, equal-market first:

- mean normalized directional return per episode;
- positive-mean markets;
- median profit factor;
- sequential normalized maximum drawdown;
- total turnover;
- average exposure;
- fraction of trend bars below full exposure;
- time / bars until first full exposure;
- failed-trend (`MFE < 4 ATR`) retained move;
- large-trend (`MFE >= 4`, `>= 8 ATR`) retained move and capture;
- under-exposure cost versus the daily-only benchmark;
- number of weekly-context cap changes per daily episode.

## Temporal robustness

Reuse the already-frozen calendar slices without modification:

- 2010–2014;
- 2015–2019;
- 2020–2026.

The crucial diagnostic is whether weekly sizing improves the 2015–2019 failure era **without destroying** the other eras. Do not choose or tune a rule solely to rescue 2015–2019.

Also report the existing top-1%-winner removal stress and generic normalized friction grid from the economic-value audit.

## Decision criteria

The weekly layer merits advancement only if it provides a meaningful risk / robustness improvement that is reasonably broad across markets and eras. A visually cleaner equity curve or a single-era rescue is insufficient.

Allowed conclusions:

- weekly context adds no measurable incremental value;
- weekly context mainly reduces risk but sacrifices too much trend capture;
- weekly context improves the risk / capture frontier in-sample and merits OOS validation.

Not allowed:

- stable alpha;
- production-ready;
- asset-specific weekly rules;
- retuning the weekly classifier to fit this sample.

## Anti-overfit guardrails

- no new classifier thresholds;
- no asset-specific parameters;
- no long / short tuning split;
- no optimizer over weekly caps or Trendability thresholds;
- no hard multi-year structural-range veto;
- no use of incomplete current-week data;
- no parameter changes after inspecting the first results;
- PR #80 remains Draft.

## Required evidence before analysis

Generate one compact native-1W context log for each frozen market containing every confirmed weekly bar:

- ticker / representation;
- week open / close timestamps;
- weekly formal regime;
- ER13 / ER26 / ER52;
- their 156-week percentile ranks;
- Weekly Trendability Composite.

These weekly rows will be as-of joined to the already accepted daily Issue #76 rows using the causal `week_close_time <= daily_event_time` rule.

Refs #78, #80, #76.