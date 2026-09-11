# Issue #76 — Cross-Asset Regime Persistence / Lifecycle Finding

## Why this analysis exists

The earlier Phase-A/Phase-B work emphasized fixed 1/5/10/20-bar forward outcomes. That is useful for measuring conditional drift, but it is not the right primary lens for a medium/long-horizon regime indicator. A 10-bar forward return can include cases where the formal regime changed after only one or two bars.

This finding therefore asks a more fundamental question:

> After a formal regime begins, how long does the classifier actually remain in that regime, and how does persistence change as the regime ages?

No classifier parameter or asset-specific rule is changed.

## Sample and method

Use the same accepted nine-market 1D Issue #76 Pine-log sample (68,118 formal-stage event rows). Reconstruct a regime spell when consecutive TradingView `event_bar` values remain in the same formal stage. A stage change or gap into no formal stage ends the spell.

- Total reconstructed spells: 2,494.
- Known-start spells used for survival analysis: 2,493.
- The first incomplete left-censored spell is excluded from entry-cohort statistics.
- Final spells are treated as right-censored rather than assumed to have ended.
- Survival is estimated with Kaplan-Meier logic.
- Primary aggregation is equal-market, not observation-weighted pooled history.

`survive_10b` means the formal regime is still the same 10 trading bars after its entry. Approximate lifecycle landmarks: 20 bars ≈ 1 trading month, 60 bars ≈ 1 quarter, 120 bars ≈ 6 months.

## Universal equal-market survival results

| Regime | Known-start spells | Median of market KM medians | Still same after 10b | Still same after 20b | Still same after 60b | Still same after 120b |
|---|---:|---:|---:|---:|---:|---:|
| Accumulation | 426 | 8 bars | 41.2% | 19.6% | 0.0% | 0.0% |
| Markup | 813 | 24 bars | 74.8% | 55.9% | 14.3% | 2.6% |
| Reaccumulation | 20 | 3 bars | 18.8% | 0.0% | 0.0% | 0.0% |
| Distribution | 412 | 10 bars | 49.1% | 21.7% | 0.7% | 0.0% |
| Markdown | 819 | 28 bars | 77.5% | 59.9% | 18.4% | 3.2% |
| Redistribution | 3 | 6 bars | 33.3% | 0.0% | 0.0% | 0.0% |

The practical structure is clear: **Markup and Markdown are persistent trend regimes; Accumulation and Distribution behave much more like shorter transition/decision regimes.** Reaccumulation and Redistribution remain too sparse to support strong lifecycle claims.

## Cross-market robustness

For Markup:

- all 9/9 markets have more than 50% probability of still being in Markup after 10 bars;
- all 9/9 markets have more than 50% probability of still being in Markup after 20 bars;
- market-level KM median spell duration ranges roughly 22–28 bars.

For Markdown:

- all 9/9 markets have more than 50% probability of still being in Markdown after 10 bars;
- 8/9 markets remain above 50% survival after 20 bars;
- market-level KM median spell duration ranges roughly 19–32 bars.

By contrast, no market has >50% Accumulation survival after 10 bars, and no market has >50% Distribution survival after 20 bars.

## Age-conditional persistence

Persistence does not simply disappear once a trend regime becomes 'old'. Equal-market probability of remaining in the same regime for **another 20 bars**, conditional on having already survived to the stated age:

| Current regime age | Markup: another 20b | Markdown: another 20b |
|---|---:|---:|
| fresh / age 0 | 55.9% | 59.9% |
| age 10 | 56.0% | 56.3% |
| age 20 | 59.6% | 53.7% |
| age 40 | 42.7% | 56.6% |

This argues against treating trend regimes as fixed 10-bar trades. The state itself can remain economically relevant for weeks, and in many cases for months. The appropriate product behavior is therefore to re-evaluate exposure while the state persists, rather than opening on entry and forcing a fixed exit horizon.

## Exit destinations

Equal-market direct-exit frequencies also show that the classifier does not follow a single rigid textbook lifecycle path.

- Accumulation exits next into Markdown about 54.6% and Markup about 39.3% of the time.
- Markup exits next into Distribution about 39.1%, Markdown about 37.5%, and an unclassified gap about 14.3%.
- Distribution exits next into Markup about 56.5% and Markdown about 40.5%.
- Markdown exits next into Accumulation about 41.5%, Markup about 36.9%, and an unclassified gap about 11.8%.

Therefore the indicator should not be evaluated as if every market must walk a canonical Wyckoff sequence. The empirical lifecycle is a state machine with persistent trend states, shorter transition states, skips, reversals, and occasional unclassified intervals.

## Research consequence

The primary decision unit for the intended universal indicator should be:

> current regime × current regime age × current cross-asset conditional distribution

not:

> fresh entry × fixed 10-bar hold.

The next research step is to combine this persistence map with baseline-relative return/risk distributions over longer landmarks (including 20/40/60/120 bars where reconstructable) and ask what directional exposure remains favorable **while the regime is still alive**.

Asset-class slices remain diagnostics for heterogeneity only. If a conclusion requires a separate FX/rates/equity rule to survive, downgrade its universality rather than adding market-specific parameters.
