# Issue #76 — Phase B methodology correction: universal cross-asset exposure first

## Why this correction exists

The initial Phase-B interpretation split FX and rates into separate exposure maps. That is useful as a diagnostic, but it does not match the intended product objective.

The intended objective is a **general-purpose regime indicator** whose semantics do not require market-specific parameter sets or asset-class-specific exposure rules. The reason for using deliberately mixed cross-market data is precisely to test whether the same regime state carries useful information across heterogeneous markets and environments.

Therefore asset class must not be the primary policy branch.

This note is a methodology correction made after clarification of the research objective. It is not presented as a pre-outcome preregistration.

## Correct primary question

> After causal normalization, does a given Wyckoff regime shift the forward distribution in a sufficiently consistent direction across heterogeneous markets to justify a universal exposure tilt?

The desired output is a universal regime-conditioned posture, not:

- one rule for FX;
- another rule for rates;
- later another rule for equities;
- and so on.

If a state only works after conditioning on asset class, that is evidence against universality, not permission to create another asset-specific rule inside this indicator.

## Primary aggregation

For every market × regime × regime-age bucket × 1/5/10/20-bar horizon:

1. Keep the existing event-time `symATR` normalization.
2. Compare the conditional distribution with that same market's unconditional all-formal-stage baseline.
3. Treat each market as one equal-weight cross-market vote so long-history markets do not dominate.
4. Aggregate across **all accepted markets together**, with asset class removed from the primary grouping key.
5. Report both the absolute conditional distribution and the baseline-relative shift.

The absolute distribution answers: **what direction is favored now?**

The baseline-relative shift answers: **did the regime add information beyond this market's normal drift?**

A universal exposure interpretation should consider both. A regime can, for example, leave an asset with positive absolute expectancy while still making it less attractive than normal; that should mean reduced long risk rather than an automatic short.

## Cross-market robustness diagnostics

Primary evidence should include:

- cross-market median of market-level conditional medians;
- cross-market median of market-level baseline-relative median shifts;
- number of markets with positive/negative conditional median;
- number of markets with positive/negative baseline-relative median shift;
- leave-one-market-out sign stability of the equal-market baseline-relative median shift;
- primary versus splice-screened sensitivity stability.

These diagnostics are deliberately market-agnostic.

## Role of asset-class slices

FX/rates/equity/commodity slices may still be inspected, but **only as adversarial diagnostics**.

Their purpose is to answer:

> Is a pooled-looking result actually being carried by one family while another family systematically disagrees?

If yes, the correct universal conclusion is to **downgrade that regime's generality/confidence**.

Do not solve disagreement by introducing `if asset == FX ... else if asset == RATES ...` policy logic.

## Current sample limitation

The accepted Issue #76 sample is heterogeneous but still narrow in economic breadth: three FX pairs and six 10Y government-yield series.

Therefore the present study can test cross-market generality inside this mixed sample, but it cannot yet establish full cross-asset universality for equities, commodities, credit, or other instruments.

Future expansion should add additional asset families using the same frozen classifier semantics and the same universal evaluation framework. Those markets should test the universal map; they should not trigger market-specific retuning by default.

## First universal re-read of the existing Phase-B output

The existing per-market Phase-B table was re-aggregated with asset class removed from the primary grouping key. No classifier parameter, horizon, regime-age bucket, or market was changed.

At the 10-bar occupancy horizon for the four statistically material major regimes:

### Markdown

This is currently the clearest universal directional state.

- 7/9 market-level conditional medians are negative.
- 7/9 market-level median shifts versus own baseline are negative.
- Cross-market median conditional move is about **-0.133 event-time ATR**.
- Cross-market median baseline-relative shift is about **-0.083 ATR**.
- Fresh Markdown entry is stronger: 9/9 market-level 10-bar medians are negative.
- The negative direction remains visible through later regime ages rather than being confined to one asset family.

Interpretation: **universal negative / short-chart-variable tilt is supported descriptively.**

### Markup

Markup contains useful universal information, but it is not strongest on the fresh entry bar.

At 10-bar occupancy:

- only 4/9 conditional medians are positive;
- but 7/9 baseline-relative median shifts are positive;
- cross-market median baseline-relative shift is about **+0.073 ATR**.

The age structure is more informative:

- age 1–4: 6/9 conditional medians positive, 7/9 baseline-relative median shifts positive;
- age 5–9: 6 markets positive, 2 negative and 1 zero on conditional median; 8/9 baseline-relative median shifts positive;
- age 20+: the effect largely decays.

Interpretation: **Markup looks more like a universal positive exposure tilt after the regime has survived several bars, not a fresh-entry buy signal.**

### Accumulation

Results are mixed across horizons and ages. The 10-bar occupancy cross-market median is negative, while the baseline-relative shift is near neutral and market agreement is weak.

Interpretation: **no strong universal directional posture is established yet.**

### Distribution

The original asset-split interpretation was misleading for the intended general-purpose product.

At 10-bar occupancy:

- 6/9 market-level conditional medians are negative;
- 6/9 baseline-relative median shifts are negative;
- however the equal-market average baseline-relative median is pulled positive by a few large positive markets, while the cross-market median shift remains negative.

This is precisely the kind of heterogeneity the universal test is meant to expose.

Interpretation: **Distribution may contain a weak negative/cautionary tilt, but it is materially less universal than Markdown and should not receive asset-specific rescue rules.**

## Revised decision philosophy

The indicator should eventually answer in market-independent language such as:

- increase positive-direction exposure;
- maintain positive-direction exposure;
- reduce positive exposure / neutral;
- increase negative-direction exposure;
- maintain negative-direction exposure;
- reduce negative exposure / neutral.

For non-price chart variables such as yields, any translation from “positive/negative chart-variable exposure” into duration or instrument-specific trade mechanics is a downstream execution translation, not a classifier parameter branch.

## Immediate next step

Continue Phase B using the universal all-market aggregation as primary.

Do **not** freeze an executable sizing policy yet.

First produce the complete universal map across all four horizons and fixed regime-age buckets, rank conclusions by cross-market agreement and leave-one-market-out stability, and explicitly mark states that fail generalization.

The asset-class tables remain supplementary diagnostics only.
