# Issue #68 — Cross-Market RAW Family Competition Attribution

Status: **PRIMARY FR-vs-GB CONTRAST COMPLETE / RESULT RECORDED / NEXT GATE OPENED**

## Why this step exists

The prior cross-market Formal-path audit localized the first major FR10Y-vs-GB10Y divergence to the RAW layer in the shared 2022-01-03 through 2023-12-29 10Y yield-rise window.

Observed before this preregistration:

- FR10Y RAW Bull-family winner occupancy: 0.0%
- GB10Y RAW Bull-family winner occupancy: 48.3%

Therefore the next question was:

> Which exact RAW stage/family repeatedly beats S2/S3 on FR10Y, and how does that competition differ from the cleaner controls?

This is discovery attribution only. It cannot validate a repair and cannot select parameters.

## Frozen comparison set

All charts are 1D and use the same fixed window:

`2022-01-03 -> 2023-12-29`

Primary contrast:

- FR10Y — extreme adverse case
- GB10Y — lower-error control

Secondary descriptive controls after the primary contrast:

- JP10Y
- DE10Y
- IT10Y
- AU10Y
- US10Y

These labels are post-hoc and descriptive only.

## Frozen RAW semantics

Use the exact existing smoothed C-2 RAW stage scores, with no formula change:

- S1 = `accRaw`
- S2 = `markupRaw`
- S3 = `reaccRaw`
- S4 = `distRaw`
- S5 = `markdownRaw`
- S6 = `redistRaw`

RAW winner uses strict-greater comparison in Stage1 -> Stage6 order, matching the prior Formal-path diagnostic.

Family mapping:

- Bull = S2 / S3
- Neutral / range-transition = S1 / S4
- Bear = S5 / S6

## Descriptive metrics

For each market/window record only:

1. winner occupancy % for each S1..S6;
2. mean raw score for each S1..S6;
3. family winner occupancy for Bull / Neutral / Bear;
4. mean per-bar family maximum;
5. mean Bull margin = `Bull max - max(Neutral max, Bear max)`.

No performance metric is allowed.

## Primary FR-vs-GB result

FR10Y:

- S1 Acc: 69.9% winner occupancy, avg RAW 75.1;
- S2 Markup: 0.0%, avg RAW 59.1;
- S6 Redist: 24.0%, avg RAW 70.1;
- Bull family: 0.0% winner occupancy, mean max 60.1;
- Neutral family: 71.7%, mean max 77.1;
- Bear family: 28.3%, mean max 71.1;
- mean Bull margin: -18.1.

GB10Y:

- S1 Acc: 4.8% winner occupancy, avg RAW 66.1;
- S2 Markup: 48.1%, avg RAW 70.1;
- S6 Redist: 0.0%, avg RAW 47.1;
- Bull family: 48.3% winner occupancy, mean max 70.1;
- Neutral family: 47.3%, mean max 75.1;
- Bear family: 4.4%, mean max 49.1;
- mean Bull margin: -5.1.

Interpretation under the preregistered rule:

- the FR failure is not mainly near-tie geometry;
- S1 Accumulation is the dominant FR suppressor and differs materially from GB;
- S2 Markup is simultaneously materially weaker on FR than GB;
- S6 Redistribution is a meaningful secondary suppressor but is not the first attribution target.

Therefore the next allowed step is the preregistered S1-vs-S2 primitive/component attribution. Result memo:

`indicators/wyckoff-regime-radar/research/reports/issue-68-cross-market-raw-family-competition-fr-vs-gb-result.md`

Next preregistration:

`indicators/wyckoff-regime-radar/research/decisions/issue-68-cross-market-s1-vs-s2-raw-component-attribution-preregistration.md`

## Hard boundary

- no Strategy Tester / PnL / returns / Sharpe / drawdown / hit-rate;
- no threshold search;
- no `breakoutBars`, Break weight, MA length, smoothing, persistence or gate tuning;
- no component counterfactual yet;
- no Exposure / A-vs-C decision;
- no Volume / MTF / Divergence / HMM rescue;
- production C-2 unchanged;
- PR #73 remains Draft / Open;
- Issue #68 remains Open.
