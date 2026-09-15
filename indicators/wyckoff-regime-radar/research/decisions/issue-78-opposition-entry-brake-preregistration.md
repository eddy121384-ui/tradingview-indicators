# Issue #78 — Temporary weekly-opposition entry brake with daily proof release

## Objective

Test a narrower multi-timeframe architecture suggested by the completed weekly-context diagnostics:

> **Daily remains the trading engine. If a fresh daily trend starts against an already-established opposing completed-weekly directional regime, begin with extra skepticism; remove that skepticism permanently once the daily trend proves itself causally.**

This is intentionally different from the rejected broad weekly hard gate. Weekly context is sampled **only at fresh daily trend entry**. It does not continuously cap an episode after entry.

No production rule is selected in this study.

## Frozen entry-conflict definition

At a fresh daily Markup entry, conflict exists when the latest completed weekly bar is:

- Markdown, or
- Redistribution.

At a fresh daily Markdown entry, conflict exists when the latest completed weekly bar is:

- Markup, or
- Reaccumulation.

Use only weekly data satisfying:

`week_close_time <= daily_entry_time`

No unfinished weekly bar is visible.

## Frozen baseline

Benchmark = existing daily **Persistence + Gentle damage-latch** policy:

Participation ramp:

- age 0–4: 25%
- age 5–9: 50%
- age 10–19: 75%
- age 20+: 100%

Gentle damage cap:

- giveback <0.5 ATR: 100%
- 0.5–1: 100%
- 1–2: 75%
- 2–4: 50%
- 4+: 25%

Damage latch / re-risk semantics remain unchanged.

## Frozen temporary brake

For episodes **without** opposing weekly context at entry, exposure is exactly the baseline.

For episodes **with** opposing weekly context at entry:

1. begin with an additional 25% maximum-exposure cap;
2. monitor favorable close-path excursion from the daily episode entry using only information available through the current close;
3. once the chosen proof threshold has been reached, release the weekly-opposition brake **permanently** for the rest of that daily formal trend episode;
4. after release, exposure immediately reverts to the ordinary baseline `min(Persistence cap, Gentle damage latch)`; weekly context is no longer consulted.

The bar that first reaches the proof threshold is still traded with the pre-release exposure. Release applies from the next bar, preserving causal execution.

## Frozen proof-threshold frontier

Do not optimize a new threshold. Compare only the three favorable-excursion milestones already frozen in the earlier Excursion-Proof participation research:

- **Early proof**: 0.5 entry ATR
- **Medium proof**: 1.0 entry ATR
- **Strict proof**: 2.0 entry ATR

These candidates form a protection-vs-capture frontier. No candidate may be called production-optimal from this discovery sample.

## Policies to compare

1. Daily Persistence + Gentle baseline
2. Weekly-opposition entry brake, release at 0.5 ATR
3. Weekly-opposition entry brake, release at 1.0 ATR
4. Weekly-opposition entry brake, release at 2.0 ATR

No age-specific, asset-specific or direction-specific variants.

## Primary metrics

Across all 1,624 completed known-start daily trend episodes, equal-market weighted:

- mean episode return;
- positive-return markets;
- profit factor;
- sequential max drawdown;
- turnover;
- bootstrap 95% interval of equal-market mean episode return;
- top-1%-winner removal stress;
- generic friction stress using the already-frozen economic-audit grid.

## Opportunity / protection decomposition

Report separately:

- failed/small episodes: MFE <4 ATR;
- large episodes: MFE >=8 ATR;
- favorable move missed vs baseline because of the temporary brake;
- adverse move avoided vs baseline;
- fraction of opposing-entry episodes that earn release;
- bars to release where release occurs.

Primary practical question:

> Can an entry-only weekly brake reduce false-countertrend damage while sacrificing materially less large-trend harvest than the previously rejected continuous weekly cap?

For reference, the prior continuous weekly-direction cap reduced all-sample expectancy from ~+0.332 to ~+0.254 ATR and large-trend harvest by ~1.175 ATR. The new rule should be judged against that trade-off, not merely against zero.

## Temporal stress

Report:

- 2010–2014
- 2015–2019
- 2020–2026

2015–2019 remains a stress test, **not** an optimization target.

## Cross-market / direction guardrails

- equal-market weighting primary;
- report Markup and Markdown diagnostics separately but do not create separate rule parameters;
- no separate FX/rates policy;
- no classifier changes;
- no weekly Trendability layer;
- no opposition-age layer.

## Promotion gate

A temporary entry brake is only a promising successor candidate if it:

1. reduces damage on MFE <4 episodes;
2. preserves substantially more MFE >=8 harvest than the continuous weekly cap;
3. does not materially destroy all-sample expectancy / cross-market breadth;
4. does not become dependent on one market or top-tail winners;
5. does not claim to fix 2015–2019 unless the improvement is broad and temporally defensible.

Even if one candidate dominates in-sample, it must remain a frozen research candidate and require new-market / weekly / prospective validation before production selection.
