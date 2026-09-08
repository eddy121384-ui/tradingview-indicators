# Issue #68 — Yield-Safe HARD Six-Market Regression Preregistration

## Decision boundary

This is the final classifier/lifecycle regression before production authorization. Representation repair is frozen after the TradingView runtime PASS on FR10Y, DE10Y, JP10Y, US10Y and USDJPY.

The comparison is deliberately isolated:

- **A — Yield-safe C-2 baseline:** accepted C-2 with the exact same Yield Level / Price Log representation, production witnesses, thresholds, weights and lifecycle, but without the Issue #68 HARD current-context caps.
- **B — Yield-safe HARD candidate:** the exact generated production candidate with the symmetric S1/S4 caps.

The only classifier intervention allowed between A and B is:

- S1: `min(downsideExhaustionGate, currentBearGate)` where `currentBearGate = f_gate(bearBg, 35, 75)`;
- S4: `min(upsideExhaustionGate, currentBullGate)` where `currentBullGate = f_gate(bullBg, 35, 75)`.

No PnL, Strategy Tester, return, Sharpe, drawdown, threshold search, weight tuning, alternate confirmBars, stateful grace, market-specific exception or representation change is authorized.

## Frozen markets

TradingView 1D:

1. FR10Y — motivating adverse case, priority human window 2021–2024, especially 2022–2023;
2. US10Y;
3. DE10Y;
4. GB10Y;
5. AU10Y;
6. JP10Y.

The same generated A/B audit must be used on all six markets with `資料表示模式 = Auto` and otherwise unchanged production defaults.

## Mandatory engineering invariants

The audit is invalid unless all of these hold:

1. S1 HARD direct effective score never exceeds A baseline S1 direct effective score.
2. S4 HARD direct effective score never exceeds A baseline S4 direct effective score.
3. S2/S3/S5/S6 RAW, gate, witness multiplier and pre-normalization effective score are shared exactly between A and B.
4. On bars where neither cap binds, A and B TOP must be identical.
5. A and B use the same yield-safe representation path and the same Volume/MTF/Divergence governance.
6. No lookahead, strategy/PnL logic or new classifier tuning input is introduced by the audit transport.

Any monotonicity or non-binding TOP parity violation is an automatic FAIL and blocks production authorization.

## Behavioral diagnostics

The audit will report, without optimizing against them:

- S1/S4 cap-binding bar counts;
- A-vs-B TOP changes;
- A-vs-B Formal changes;
- A-baseline stale S1/S4 TOP bars where the corresponding current-context cap binds;
- correction counts where B no longer keeps that stale S1/S4 TOP;
- the same counts restricted to existing `highConfidence` + `evidenceHigh` definitions;
- frozen Fresh S1/S4 retention cohorts reused from the earlier Issue #68 audit (`bear/bull context >=35`, exhaustion >=35, existing 20-bar path-direction label);
- maximum contiguous A-vs-B Formal disagreement run.

The Fresh cohort is diagnostic only and is not production eligibility. Its 20-bar path label must never enter the production classifier.

## Lifecycle review flag

A contiguous A-vs-B Formal disagreement longer than the already-existing `staleLimit = confirmBars * 2` is a **human-review flag**, not an automatic tuning trigger. It must be inspected on the chart before production authorization. No new duration threshold is introduced.

Cross-release remains legal: an unchanged stage can become TOP because S1/S4 was reduced. TOP occupancy is not a monotonic invariant; direct S1/S4 effective score is.

## Human acceptance rule

The six-market pass requires:

- zero mandatory invariant violations on every market;
- the FR10Y motivating window must show that HARD actually suppresses at least some mechanically stale S1/S4 baseline occupancy when the cap binds;
- every prolonged Formal disagreement flag must be reviewed and must not reveal a new obvious wrong-family lifecycle persistence caused by HARD;
- no newly discovered representation-domain failure.

There is deliberately no target correction percentage, Fresh-retention percentage or PnL gate. Those would turn this validation pass into tuning.

If all six markets pass, PR #73 may move from Draft to Ready for Review for Eddy's final production authorization. Do not merge and do not close Issue #68 during this regression.