# Issue #78 — Weekly conflict diagnostic preregistration

## Objective

Diagnose which *kind* of completed-weekly context conflict is actually informative enough to justify braking a daily Markup / Markdown position.

This is a diagnostic extension of Issue #78. It does **not** change the frozen Issue #68 classifier, does **not** select a production exposure rule, and must not tune specifically to the discovered 2015–2019 weak era.

## Motivation

The first Daily Trigger × Weekly Sizing pass found that broad weekly gating lowers drawdown but also sacrifices too much large-trend capture. A full weekly confirmation requirement is therefore too blunt.

The next question is narrower:

> When a daily directional regime is active, which completed-weekly states contain genuinely adverse information, and which weekly states are merely "not yet confirmed" but should not cap exposure?

## Frozen causal join

For every daily decision bar, use only the most recent native-1W observation satisfying:

`week_close_time <= daily_event_time`

No unfinished weekly bar may be used.

Universe, daily sample, episode reconstruction, representation handling and equal-market weighting remain exactly those already accepted in Issues #76/#78:

- OANDA:EURUSD
- OANDA:GBPUSD
- OANDA:USDJPY
- TVC:US10Y
- TVC:DE10Y
- TVC:FR10Y
- TVC:GB10Y
- TVC:AU10Y
- TVC:JP10Y

## Frozen weekly-context taxonomy

The taxonomy is defined from the six existing formal weekly regimes before inspecting subgroup outcomes.

For a **daily Markup** bar:

- **Aligned directional**: weekly Markup or Reaccumulation.
- **Turn-risk conflict**: weekly Distribution.
- **Directional conflict**: weekly Markdown or Redistribution.
- **Other / neutral**: weekly Accumulation or unavailable context.

For a **daily Markdown** bar:

- **Aligned directional**: weekly Markdown or Redistribution.
- **Turn-risk conflict**: weekly Accumulation.
- **Directional conflict**: weekly Markup or Reaccumulation.
- **Other / neutral**: weekly Distribution or unavailable context.

Rationale: Reaccumulation is treated as bullish-context continuation, Redistribution as bearish-context continuation; Accumulation/Distribution are treated as possible turn-risk only when they oppose the current daily direction. No asset-specific remapping is permitted.

## Frozen trendability refinement

The already-frozen weekly Trendability score is **not** used as a positive confirmation gate in this study.

It is tested only as a diagnostic severity split inside `Directional conflict`:

- high-trendability directional conflict: `wtrend > 66.67`
- non-high directional conflict: `wtrend <= 66.67` or unavailable

The 66.67 boundary is inherited from the prior preregistration; it must not be moved after outcomes are viewed.

## Primary diagnostic outcomes

Evaluate each weekly-context bucket at two levels.

### A. Daily-bar forward behavior

For every daily Markup / Markdown bar with causal weekly context, measure in the daily trend direction:

- next 1-bar normalized move;
- next 5-bar cumulative move;
- next 10-bar cumulative move;
- next 20-bar cumulative move;
- probability the same formal daily trend survives at least 5 / 10 / 20 additional bars;
- probability of a new favorable close-path extreme within 10 / 20 bars.

Forward windows terminate at available sample boundaries but do **not** force the daily trend to remain active; survival is reported separately. This prevents mechanically rewarding buckets merely because the formal label persists.

### B. Episode-entry behavior

At fresh daily Markup / Markdown entry, classify the most recent completed weekly context and compare:

- episode mean retained move under the frozen `Persistence + Gentle` daily policy;
- episode MFE;
- MFE >= 4 ATR rate;
- MFE >= 8 ATR rate;
- episode duration;
- positive-return rate.

## Stress slices

Primary conclusions remain all-years and equal-market weighted.

The previously discovered eras are reported only as stress diagnostics:

- 2010–2014
- 2015–2019
- 2020–2026

2015–2019 is **not** an optimization target. A rule or taxonomy must not be altered merely because it fails that era.

## Cross-market standard

For every important comparison report:

- equal-market mean;
- number of markets with the expected ordering/sign;
- pooled observation count only as descriptive context;
- per-market sample counts to expose thin buckets.

No separate FX/rates rules.

## Interpretation gate

A weekly conflict type is considered *promising as a brake candidate* only if it shows, without parameter tuning:

1. materially worse forward directional behavior than `Other / neutral` and `Aligned directional`;
2. adverse ordering that is reasonably consistent across markets;
3. evidence in both Markup and Markdown, allowing magnitude asymmetry but not separate rule definitions;
4. the signal is not created solely by 2015–2019;
5. sample size is not obviously too thin.

No exposure percentage is selected in this diagnostic study.

## Explicit non-goals

- no new weekly thresholds;
- no optimizer;
- no asset-specific parameters;
- no requirement that weekly must confirm daily before entry;
- no classifier retuning;
- no attempt to "fix" 2015–2019;
- no production promotion from this discovery sample.

If the diagnostic identifies one robust conflict family, a separate preregistered simulation may later test a small fixed brake ladder against the current daily benchmark.
