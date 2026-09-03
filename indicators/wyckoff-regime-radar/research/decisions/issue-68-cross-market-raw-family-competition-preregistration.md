# Issue #68 — Cross-Market RAW Family Competition Attribution

Status: **POST-HOC DISCOVERY ATTRIBUTION / NO TUNING / PRODUCTION C-2 FROZEN**

## Why this step exists

The prior cross-market Formal-path audit localized the first major FR10Y-vs-GB10Y divergence to the RAW layer in the shared 2022-01-03 through 2023-12-29 10Y yield-rise window.

Observed before this preregistration:

- FR10Y RAW Bull-family winner occupancy: 0.0%
- GB10Y RAW Bull-family winner occupancy: 48.3%

Therefore the next question is not yet which component to change. The next question is:

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
4. mean per-bar family maximum:
   - Bull max = `max(markupRaw, reaccRaw)`
   - Neutral max = `max(accRaw, distRaw)`
   - Bear max = `max(markdownRaw, redistRaw)`
5. mean Bull margin = `Bull max - max(Neutral max, Bear max)`.

No performance metric is allowed.

## Attribution rule

The purpose of this step is to identify the dominant competing RAW family/stage on FR10Y.

Interpretation:

- if one non-Bull stage/family dominates FR but not GB, the next allowed step is component attribution between S2/S3 and that dominant competitor;
- if several non-Bull stages share the suppression, record a distributed RAW competition failure and compare only the shared primitives that feed those stages;
- if FR and GB RAW stage-score means are similar despite very different winner occupancy, inspect score spacing / near-tie geometry next rather than component levels;
- do not change any formula in this phase.

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
