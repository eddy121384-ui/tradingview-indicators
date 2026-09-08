# Issue #68 — Cross-Market S1-vs-S2 RAW Component Attribution

Status: **RESULT RECORDED / S1-ONLY ATTRIBUTION OPENED / NO TUNING / PRODUCTION C-2 FROZEN**

## Trigger

The fixed 2022-01-03 -> 2023-12-29 RAW-family audit found the first large FR10Y-vs-GB10Y divergence at the RAW layer.

Primary contrast:

- FR10Y: S1 Acc winner 69.9%, S2 Markup winner 0.0%; average S1/S2 RAW = 75.1 / 59.1.
- GB10Y: S1 Acc winner 4.8%, S2 Markup winner 48.1%; average S1/S2 RAW = 66.1 / 70.1.

FR10Y also has material S6 Redistribution competition (24.0% winner occupancy), but S1 is the dominant suppressor and is therefore the first frozen component-attribution target.

## Exact frozen formulas under audit

### S1 Accumulation RAW0

`accRaw0 = weighted5(bearMaturityTrace 0.20, rangeScore 0.20, downsideExhaustion 0.25, supportHolding 0.25, lowVolScore 0.10)`

### S2 Markup RAW0

`markupBaseRaw = weighted5(breakoutScore 0.20, heatUp 0.20, structureStrong 0.20, markupExtensionScore 0.25, markupContinuationScore 0.15)`

`markupRaw0 = weighted2(markupBaseRaw 0.85, accTraceForMarkup 0.15)`

## Observed FR10Y vs GB10Y result

### GB10Y control

- Breakout: 83.1
- Heat up: 52.1
- Structure strong: 82.1
- Markup extension: 62.1
- Markup continuation: 65.1
- Acc trace -> Markup: 73.1
- S2 Base / RAW0 / RAW: 69.1 / 70.1 / 70.1
- S1 RAW0 / RAW: 66.1 / 66.1
- S2 - S1 average gap: +3.1
- S2 > S1: 58.1% of bars
- longest S1>=S2 run: 57 bars

### FR10Y adverse

- Breakout: 83.1
- Heat up: 20.1
- Structure strong: 84.1
- Markup extension: 39.1
- Markup continuation: 58.1
- Acc trace -> Markup: 79.1
- S2 Base / RAW0 / RAW: 56.1 / 59.1 / 59.1
- S1 RAW0 / RAW: 75.1 / 75.1
- S2 - S1 average gap: -16.1
- S2 > S1: 0.1% of bars
- longest S1>=S2 run: 512 bars

## Interpretation

The FR10Y failure is two-sided.

S2-side missing trend evidence is **not** caused by Breakout or Structure Strong; both are comparable to, or stronger than, GB10Y. The dominant S2 divergences are:

- much lower Heat Up (20.1 vs 52.1),
- much lower Markup Extension (39.1 vs 62.1),
- moderately lower Markup Continuation (58.1 vs 65.1).

`Acc trace -> Markup` is not deficient on FR10Y and therefore is not the primary S2 bottleneck.

At the same time, S1 itself remains materially elevated on FR10Y (75.1 vs 66.1). The current combined table did not provide a clean enough visual read of the five S1 primitive rows, so S1 over-support remains unresolved.

## Next preregistered step

Open a dedicated S1 component-only attribution:

`indicators/wyckoff-regime-radar/research/decisions/issue-68-cross-market-s1-component-only-preregistration.md`

The next question is only which frozen S1 primitive(s) account for FR10Y's elevated S1 RAW versus GB10Y. No repair or counterfactual is authorized.

## Hard boundary

- no Strategy Tester / PnL / returns / Sharpe / drawdown / hit-rate;
- no parameter, weight, threshold, MA, smoothing, `breakoutBars`, persistence or gate search;
- no component removal or counterfactual in this phase;
- no S6 repair yet;
- no Exposure / A-vs-C decision;
- no Volume / MTF / Divergence / HMM rescue;
- production C-2 unchanged;
- PR #73 remains Draft/Open;
- Issue #68 remains Open.
