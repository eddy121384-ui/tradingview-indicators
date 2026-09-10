# Issue #76 — Phase B Regime-Conditioned Exposure Map Preregistration

## Status

Preregistered descriptive / decision-support research on the **existing accepted nine-market daily sample**.

This phase does **not** require a new OOS sample because the immediate objective is not to prove a fixed trading rule. The objective is to map how the conditional forward distribution changes by current Wyckoff regime and translate that information into a defensible exposure posture.

Any later claim that a selected exposure policy has profitable out-of-sample performance must still be tested on independent data after the policy is frozen.

## Research objective

The operational question is:

> Given the market's current formal regime, what directional exposure / risk posture has the most favorable conditional distribution relative to that market's own unconditional baseline?

This is explicitly **not** a Buy/Sell signal study.

The output should be useful for decisions such as:

- keep / reduce / add existing directional exposure;
- permit or discourage counter-regime positions;
- choose Full risk / Half risk / Flat / Hedge-like posture;
- distinguish fresh regime entry from mature occupancy;
- identify whether opportunity comes from expected direction, reduced adverse excursion, improved asymmetry, or volatility expansion.

## No symmetry requirement

Classifier construction may remain directionally reciprocal, but realized market behavior and the resulting exposure policy are **not required to be symmetric**.

Do not penalize a result because bullish and bearish regimes produce different forward distributions.

For every market and regime, compare conditional outcomes to that market's own baseline. Do not use 50% directional hit rate as the primary benchmark when the unconditional distribution is itself asymmetric.

## Frozen sample

Reuse the accepted Issue #76 nine-market 1D sample:

FX:
- OANDA:EURUSD
- OANDA:GBPUSD
- OANDA:USDJPY

10Y government yields:
- TVC:US10Y
- TVC:DE10Y
- TVC:FR10Y
- TVC:GB10Y
- TVC:AU10Y
- TVC:JP10Y

Retain all existing data caveats, especially DE10Y's possible Pine Logs 10,000-message early-history truncation.

No market may be dropped merely because its result is inconvenient.

## Frozen horizons

Retain the existing preregistered 1 / 5 / 10 / 20 daily-bar horizons.

Do not optimize a new holding period inside this phase.

## Event/state layers

Measure at least these layers separately:

1. **Formal-stage occupancy** — every confirmed bar in the regime.
2. **Fresh entry** — first confirmed bar after formal-stage change.
3. **Regime age** — days since fresh entry, using fixed descriptive buckets rather than optimized cutoffs:
   - age 0 (fresh entry)
   - age 1–4
   - age 5–9
   - age 10–19
   - age 20+
4. Canonical transition labels may be shown as diagnostics, but they are not privileged as the primary decision unit.

S3 / Reaccumulation and S6 / Redistribution are expected to be sparse in the current sample; report them but do not manufacture confidence from small n.

## Conditional distribution metrics

For each market × regime × state layer × horizon, report:

- sample size;
- mean forward move;
- median forward move;
- q10 / q25 / q75 / q90;
- positive / negative directional rate;
- mean MFE;
- mean MAE;
- future realized volatility;
- all available normalized versions using event-time symATR.

Also derive direction-aligned diagnostics only where useful, but keep the raw signed distribution visible.

## Baseline-relative metrics

For every market, calculate the same horizon metrics on its own all-formal-stage baseline.

Primary information measures are conditional-minus-baseline, including:

- mean-return lift;
- median-return lift;
- directional-probability lift;
- MFE lift;
- MAE improvement / deterioration;
- future-volatility lift;
- tail shift at q10 and q90.

This is the main guard against confusing an asset's structural drift with classifier information.

## Exposure interpretation

Do not force the output into symmetric +1 / 0 / -1 signals.

The research may recommend asymmetric postures such as:

- Strong Long / Long / Neutral / Reduced Long / Hedge / Short;
- or Strong Short / Short / Neutral / Long, depending on asset-class semantics.

However, the first Phase-B output is a **distribution map**, not a fully optimized executable policy.

A suggested posture must be traceable to the observed conditional distribution and baseline-relative change, not to a hand-tuned PnL search.

## Asset-class semantics

FX and yield-level series should not be pooled blindly into one economic exposure sign.

- FX: signed price direction can be interpreted directly, subject to pair quotation convention.
- Yields: yield-up / yield-down must remain explicitly labeled as yield exposure; any later mapping to bond-futures / duration exposure is a separate semantic step.
- Equities are not part of the current nine-market sample. If equities are added later, their positive long-run drift must be handled through their own unconditional baseline rather than assuming 50/50 direction symmetry.

## Cross-market aggregation

Report both:

- pooled observation-weighted results;
- equal-market summaries.

Do not let long-history markets dominate the economic conclusion solely through sample size.

Where meaningful, show FX and rates separately before any all-market summary.

## Decision questions

Phase B should answer, in plain language:

1. In each major regime, is Long, Flat, or Short direction statistically more attractive **relative to that market's normal state**?
2. Does a fresh regime entry deserve more risk than mature occupancy?
3. How quickly does any conditional edge decay with regime age?
4. Is the advantage driven by expected direction, better MFE/MAE geometry, smaller adverse tail, or simply higher volatility?
5. Are some regimes best understood as **risk-reduction / no-chase states** rather than directional opportunities?
6. Which conclusions are stable across markets, and which are asset-class-specific?

## Anti-overfit rule for this phase

Allowed:
- reuse the original sample;
- descriptive slicing by the frozen regime-age buckets above;
- baseline-relative distribution analysis;
- asymmetric interpretation;
- cross-market / asset-class comparison.

Not allowed:
- searching arbitrary thresholds to maximize Sharpe/PnL;
- choosing bespoke holding periods after seeing results;
- market-specific parameter tuning;
- deleting weak markets;
- classifier changes based on the forward outcomes;
- claiming a production strategy from this in-sample map.

## Expected Phase-B deliverable

A trader-readable **Regime-Conditioned Exposure Map** that, for each major regime, states something of the form:

> Current state historically shifts the next 1/5/10/20-day distribution toward X, with Y change versus baseline, Z adverse-excursion behavior, and therefore supports / discourages this exposure posture.

The final map may be deliberately asymmetric. That is a feature if it reflects the data rather than a classifier defect.
