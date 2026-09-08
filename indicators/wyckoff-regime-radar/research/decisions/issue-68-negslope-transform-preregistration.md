# Issue #68 — FR10Y vs DE10Y NegSlopeDull Transformation Audit Preregistration

Status: discovery-only causal attribution. Production C-2 remains frozen.

## Trigger

The downside-exhaustion component audit over 2022-01-03 through 2023-12-29 localizes the largest FR-vs-DE split to `NegSlopeDull`.

Production C-2 defines:

`negSlopeDullScore = f_gate(speedRank, 15.0, 55.0) * 100`

where:

- `speedRank = ta.percentrank(speedZ, rankLen)`;
- `speedZ = f_slopeZ(logPrice, speedLen, vol)`;
- `f_slopeZ` uses a 20-bar linear-regression slope of `logPrice`, multiplied by `len`, divided by `vol * sqrt(len)`;
- `vol = stdev(log(close / close[1]), volLen)`;
- `safeClose = close > 0 ? close : na`;
- defaults: speedLen=20, volLen=60, rankLen=756.

DE10Y has materially lower `NegSlopeDull` than FR10Y despite very similar raw bp path geometry, especially on RAW-S1 -> EFF-S2 flip bars.

## Primary question

At which transformation step does the visually similar FR10Y / DE10Y yield path begin to diverge enough to create the `NegSlopeDull` split?

## Frozen window and controls

- 2022-01-03 through 2023-12-29 inclusive.
- Primary charts: FR10Y 1D and DE10Y 1D.
- Expected semantic family: Bull yield regime.
- Frozen C-2 source, all production thresholds and weights unchanged.
- No PnL, no threshold search, no weight changes, no alternative production feature replacement.

## Diagnostic chain

The audit must expose the same bars through the following chain:

1. **Economic path:** 20D regression-implied slope in basis points.
2. **Full-history bp rank:** 756-bar percentile rank of the 20D bp slope using the price series directly, including negative-yield history.
3. **Positive-domain bp rank:** the same bp slope, but only on bars where the production log-slope is defined, to isolate sample-support / zero-crossing effects.
4. **Log-domain slope rank:** percentile rank of the production 20D log-price regression slope before volatility normalization.
5. **Volatility normalization:** production `speedZ` and the 60D log-return volatility denominator.
6. **Final historical rank:** production `speedRank`.
7. **Gate output:** production `NegSlopeDull` score.

Also measure the rolling 756-bar share of positive closes and valid `speedZ` observations, because the production log domain is undefined when yield <= 0.

## Populations

Report ALL / RAW-S1->EFF-S2 FLIP / NO-FLIP populations using the already frozen flip definition:

`accRaw >= markupRaw and markupEff > accEff`.

## Required measurements

- 20D bp slope average.
- 20D bp-slope rank using full history.
- 20D bp-slope rank using positive-domain support only.
- 20D log-slope implied relative move and log-slope rank.
- 60D log-return volatility.
- production `speedZ` average.
- production `speedRank` average.
- production `NegSlopeDull` average.
- share with `speedRank <= 15`, `15 < speedRank < 55`, and `speedRank >= 55`.
- 756-bar positive-close share and valid-speedZ share.
- reconstruction error for `speedZ = logSlopeTotal / (vol * sqrt(speedLen))`.
- transformation rank shifts:
  - full-bp-rank -> positive-support-bp-rank;
  - positive-support-bp-rank -> log-slope-rank;
  - log-slope-rank -> final speedRank.

## Preregistered interpretation

- **20D bp slope / full bp rank already materially split FR vs DE:** genuine path geometry remains the primary explanation; do not blame transformation.
- **Full bp rank similar but positive-support bp rank diverges together with coverage:** zero/negative-rate history support is the primary amplifier.
- **Positive-support bp rank similar but log-slope rank diverges:** the `log(yield)` level transform is the primary amplifier.
- **Log-slope rank similar but speedZ / final speedRank diverges:** log-return volatility normalization is the primary amplifier.
- **speedZ levels similar but final speedRank diverges:** the 756-bar percentile-history distribution is the primary amplifier.
- **No single step dominates:** classify as hybrid amplification and do not tune any individual threshold.
- **Reconstruction error non-zero:** stop; audit implementation before any semantic conclusion.

## Repair boundary

This audit authorizes no production change. Any later repair proposal must use a frozen counterfactual, preserve semantic symmetry, and be checked on FR/DE plus JP/GB/US controls before merge consideration.