# Issue #68 — Cross-Market S1-vs-S2 RAW Component Attribution

Status: **POST-HOC DISCOVERY ATTRIBUTION / NO TUNING / PRODUCTION C-2 FROZEN**

## Trigger

The fixed 2022-01-03 -> 2023-12-29 RAW-family audit found the first large FR10Y-vs-GB10Y divergence at the RAW layer.

Primary contrast:

- FR10Y: S1 Acc winner 69.9%, S2 Markup winner 0.0%; average S1/S2 RAW = 75.1 / 59.1.
- GB10Y: S1 Acc winner 4.8%, S2 Markup winner 48.1%; average S1/S2 RAW = 66.1 / 70.1.

FR10Y also has material S6 Redistribution competition (24.0% winner occupancy), but S1 is the dominant suppressor and is therefore the first frozen component-attribution target.

## Question

> Why does frozen S1 Accumulation remain much stronger than S2 Markup on FR10Y during the obvious 2022-2023 Bull yield regime, while the same relationship reverses on GB10Y?

This phase does not change any formula and does not yet test a repair.

## Exact frozen formulas under audit

### S1 Accumulation RAW0

`accRaw0 = weighted5(bearMaturityTrace 0.20, rangeScore 0.20, downsideExhaustion 0.25, supportHolding 0.25, lowVolScore 0.10)`

Audit components:

- bearMaturityTrace
- rangeScore
- downsideExhaustion
- supportHolding
- lowVolScore
- accRaw0
- smoothed accRaw

### S2 Markup RAW0

`markupBaseRaw = weighted5(breakoutScore 0.20, heatUp 0.20, structureStrong 0.20, markupExtensionScore 0.25, markupContinuationScore 0.15)`

`markupRaw0 = weighted2(markupBaseRaw 0.85, accTraceForMarkup 0.15)`

Audit components:

- breakoutScore
- heatUp
- structureStrong
- markupExtensionScore
- markupContinuationScore
- accTraceForMarkup
- markupBaseRaw
- markupRaw0
- smoothed markupRaw

## Descriptive diagnostics

Within the same fixed 2022-01-03 -> 2023-12-29 window, record:

- mean value of every frozen S1 and S2 primitive above;
- mean S2-minus-S1 smoothed RAW gap;
- fraction of bars where S2 RAW > S1 RAW;
- longest continuous run where S1 RAW >= S2 RAW.

These statistics are semantic diagnostics only.

TradingView audit:

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue68-cross-market-s1-vs-s2-component-audit.pine`

The audit uses only three plot-safe lanes; detailed diagnostics are carried by the table.

## Attribution interpretation

Primary comparison remains FR10Y vs GB10Y.

- If one or two S1 primitives are materially higher on FR while S2 primitives are broadly similar, treat those S1 primitives as upstream over-support candidates.
- If S1 primitives are broadly similar but one or two S2 primitives are materially lower on FR, treat those S2 primitives as missing-trend-evidence candidates.
- If both occur, record a two-sided competition failure rather than forcing a single-cause story.
- If the difference is mostly in `accTraceForMarkup` or smoothing rather than primitive inputs, isolate that transformation next.
- Do not infer causality from mean differences alone; any later counterfactual requires a separate preregistration and safety gate.

Secondary descriptive control after the primary contrast: JP10Y. DE10Y / IT10Y / AU10Y / US10Y remain available only if the FR-vs-GB split is not interpretable.

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
