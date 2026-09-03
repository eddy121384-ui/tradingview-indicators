# Issue #68 — FR10Y vs DE10Y Path-Geometry / Transformation Audit Preregistration

## Status

Discovery-only attribution. Production C-2 remains frozen. No PnL, no tuning, no classifier repair.

## Why this gate exists

FR10Y and DE10Y look visually similar during the 2022–2023 yield-rise regime, yet the frozen classifier treats them very differently:

- both have severe RAW/S1 pathology and `RAW Bull = 0%`;
- DE10Y nevertheless produces materially more Bull TOP / Strong continuity and eventually acquires Bull Formal once;
- FR10Y produces sparse Bull Strong bars, weak TOP-gap continuity, and never acquires Bull Formal;
- earlier component attribution showed FR10Y Breakout and Structure are not deficient, while Heat Up and Markup Extension are materially weaker.

This phase asks:

> Is the FR-vs-DE divergence already present in raw yield-path geometry, or does the classifier transformation / normalization amplify a visually modest market difference into a large semantic difference?

## Fixed window and primary contrast

All charts: 1D.

Shared window:

`2022-01-03 -> 2023-12-29`

Primary contrast:

- FR10Y — catastrophic adverse case
- DE10Y — negative-rate-history control that eventually rescues to Bull Core

No third market is inspected until the FR/DE interpretation is frozen.

## Raw market-path metrics

Computed directly from the chart yield series, without changing C-2:

1. average absolute 1D change in basis points (`abs(change(close)) * 100`);
2. average signed 20D change in basis points;
3. average absolute 20D change in basis points;
4. share of 20D changes that are positive;
5. average signed 60D change in basis points;
6. average absolute 60D change in basis points;
7. 20D path efficiency = `abs(close-close[20]) / sum(abs(1D changes),20)`;
8. 60D path efficiency using the same definition;
9. average 20D high-low range in basis points;
10. average signed 20D move divided by ATR(20);
11. daily direction-flip share, using sign changes in non-zero 1D yield moves.

The basis-point conversion assumes the TradingView government-yield chart is expressed in percentage points (e.g. `4.25` = 4.25%, so `0.01` = 1 bp), matching the FR10Y/DE10Y charts used in this discovery.

## Frozen model-side metrics

Report, without changing their formulas:

- `heatUp`;
- `markupExtensionScore`;
- `markupContinuationScore`;
- `rangeScore`;
- `accRaw` (S1);
- `markupRaw` (S2);
- `markupRaw - accRaw`;
- Bull-family TOP occupancy (`topId == 2 or topId == 3`);
- average `topGap` conditional on Bull-family TOP;
- Bull TOP `topGap >= topGapMin` pass share.

## Interpretation rules locked before results

- If FR has materially lower raw trend efficiency / normalized move and higher flip/chop metrics than DE, while model-side Heat / Extension / gap move in the same direction, retain a **market-path geometry** explanation.
- If raw path metrics are broadly comparable but model-side Heat / Extension / Range / S1-S2 gap diverge sharply, escalate **transformation / normalization / input-domain amplification** as the primary explanation.
- If raw geometry differs modestly but model divergence is much larger, retain a **hybrid amplification** explanation: real path difference exists, but C-2 magnifies it.
- Do not infer causality from endpoint yield changes alone.
- Do not use percentage returns of yields as the primary geometry metric; use basis-point and ATR-normalized changes.
- This audit does not validate or reject the separate log-domain / zero-crossing hypothesis by itself.

## Hard boundary

- no Strategy Tester, returns, PnL, Sharpe, drawdown or hit rate
- no threshold search
- no changes to `topGapMin`, `confirmBars`, `dominantMin`, evidence gates, persistence, weights, MA lengths, Break, Structure, Heat, Range, maturity or trace
- no feature replacement, rescaling, shift, log repair or zero-floor counterfactual
- no Exposure / A-vs-C decision
- no Volume / MTF / Divergence / HMM rescue
- production C-2 unchanged

PR #73 must remain Draft / Open. Issue #68 must remain Open. Do not merge or close either without Eddy's explicit approval.
