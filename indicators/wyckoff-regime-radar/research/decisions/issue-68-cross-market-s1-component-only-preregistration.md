# Issue #68 — Cross-Market S1 Accumulation Component-Only Attribution

Status: **POST-HOC DISCOVERY ATTRIBUTION / NO TUNING / PRODUCTION C-2 FROZEN**

## Trigger

The frozen 2022-01-03 -> 2023-12-29 FR10Y-vs-GB10Y S1-vs-S2 audit established a two-sided RAW competition failure:

- FR10Y S1 Acc RAW = 75.1 vs GB10Y 66.1.
- FR10Y S2 Markup RAW = 59.1 vs GB10Y 70.1.
- FR10Y S2-minus-S1 average gap = -16.1 vs GB10Y +3.1.
- FR10Y S2 > S1 on only 0.1% of bars and S1>=S2 persists for the full 512-bar window.
- S2-side divergence is already localized mainly to low Heat Up and low Markup Extension; Breakout and Structure Strong are not deficient on FR10Y.

The remaining unresolved half is why S1 itself stays abnormally high on FR10Y.

## Frozen S1 formula

Use the exact production C-2 S1 Accumulation RAW0 formula:

`accRaw0 = weighted5(bearMaturityTrace 0.20, rangeScore 0.20, downsideExhaustion 0.25, supportHolding 0.25, lowVolScore 0.10)`

No component, weight, threshold, smoothing or upstream calculation may change.

## Primary question

> Which frozen S1 primitive contributes most to FR10Y's elevated S1 Acc RAW versus GB10Y during the same obvious 2022-2023 Bull yield regime?

## Locked comparison

All charts: 1D.

Window:
`2022-01-03 -> 2023-12-29`

Primary contrast:
- FR10Y — adverse
- GB10Y — control

JP10Y is allowed only as a secondary descriptive adverse control after FR-vs-GB is interpreted.

## Descriptive metrics

For each market/window report:

- average `bearMaturityTrace` and weighted contribution `avg * 0.20`;
- average `rangeScore` and weighted contribution `avg * 0.20`;
- average `downsideExhaustion` and weighted contribution `avg * 0.25`;
- average `supportHolding` and weighted contribution `avg * 0.25`;
- average `lowVolScore` and weighted contribution `avg * 0.10`;
- average `accRaw0`;
- average smoothed `accRaw`;
- average smoothed `markupRaw` for context only;
- average `accRaw - markupRaw` gap for context only.

Because the five S1 weights sum to 1.0, the five mean weighted-point contributions should reconstruct mean `accRaw0` up to floating-point rounding.

## Interpretation rule

- One or two FR S1 primitives materially above GB and accounting for most of the S1 RAW0 difference => localize S1 over-support to those primitives.
- Broadly elevated FR S1 primitives => distributed S1 semantic over-support; do not force a single-cause story.
- Similar S1 primitive means despite elevated FR S1 RAW => inspect transformation/smoothing or source-series differences next.
- This phase does not establish causality and does not authorize a counterfactual repair.

## Hard boundary

- no Strategy Tester / PnL / returns / Sharpe / drawdown / hit-rate;
- no component removal;
- no parameter, weight, threshold, MA, smoothing, `breakoutBars`, persistence or gate search;
- no S2 repair;
- no S6 repair;
- no Exposure / A-vs-C decision;
- no Volume / MTF / Divergence / HMM rescue;
- production C-2 unchanged;
- PR #73 remains Draft/Open;
- Issue #68 remains Open.
