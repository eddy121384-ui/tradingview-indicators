# Issue #76 — Universal Regime-Health Validation Preregistration

## Status

Preregistered successor validation target derived from the Issue #76 lifecycle/exposure-value study. This note freezes the hypothesis **before** collecting any new asset classes or weekly-timescale evidence.

## Product objective

The intended product remains one general-purpose cross-asset regime indicator. No asset-specific parameter branch is allowed.

The candidate architecture is:

> current formal regime × regime persistence × causal regime health

where regime health is measured from information already available at the current bar, not from a fixed future holding period.

## Frozen hypothesis

For the two persistent trend states:

- Markup health = ATR-normalized drawdown from the running intraregime peak;
- Markdown health = ATR-normalized rebound from the running intraregime trough.

Hypothesis:

> As ATR-normalized giveback from the regime's own running extreme increases, the probability that the same formal trend regime survives should decrease, the near-term formal-exit hazard should increase, and the directional exposure value of the current trend state should weaken.

The relationship is expected to be monotonic in broad form, not necessarily at every adjacent bucket in every market.

## Frozen descriptive grid for validation

Use the same coarse bins discovered in the current sample without retuning them on the validation sample:

- `<0.5 ATR`
- `0.5–1 ATR`
- `1–2 ATR`
- `2–4 ATR`
- `4+ ATR`

These are validation bins, **not production thresholds**. Do not optimize alternative cutoffs after seeing validation outcomes.

## Primary validation metrics

For Markup and Markdown separately, report by health bucket:

- next-bar formal-exit hazard;
- probability of remaining in the same formal state for another 10 bars;
- causal 10-bar chart-direction movement, capped by formal state exit;
- equal-market mean and median;
- cross-market sign agreement;
- leave-one-market-out stability where sample size permits.

Primary pass condition is qualitative cross-market ordering, not a single p-value or Sharpe threshold:

1. `4+ ATR` giveback should have materially higher exit hazard than `<0.5 ATR`;
2. `4+ ATR` should have materially lower 10-bar same-state survival than `<0.5 ATR`;
3. directional exposure value should weaken materially as giveback becomes large;
4. the conclusion must not require asset-specific rescue parameters.

## Adversarial expansion

Preferred new evidence is deliberately heterogeneous:

- equity indices;
- commodities;
- optionally bond futures or other tradable rates instruments;
- weekly-timescale replication of the same classifier logic.

The purpose is to try to break universality, not to find friendly markets.

## Prohibited changes during validation

Do not change:

- production classifier weights or thresholds;
- HARD caps;
- `confirmBars`;
- representation routing;
- market-specific parameters;
- health bins;
- holding periods in order to rescue weak results;
- asset-class-specific policy rules.

If the health relation fails materially on new heterogeneous evidence, downgrade the universal product hypothesis rather than tune around the failure.

## Current-sample reference only

The discovery sample showed the expected deterioration in all 9/9 markets on both trend sides when comparing `<0.5 ATR` with `4+ ATR` giveback. Because that relationship was discovered in-sample, it is not sufficient for production use by itself.
