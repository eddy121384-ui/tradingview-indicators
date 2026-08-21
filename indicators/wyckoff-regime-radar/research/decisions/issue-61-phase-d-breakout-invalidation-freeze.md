# Issue #61 — Phase D breakout-invalidation stop freeze

Status: **PRE-OUTCOME RULE FREEZE**.

Phase B established the stage-aware lifecycle as a development candidate. Phase C rejected the specific `rangeScore >= 70` half-size management rule. Before introducing any ATR multiple, percentage stop, target, or optimized risk parameter, test the most direct semantic invalidation of the entry thesis itself.

## Frozen rule

The base lifecycle remains unchanged except for one additional exit condition.

### Long

A long can arise in either of two existing base paths:

1. `Stage 1 + fresh rangeBreakUp` arms a setup and Formal Stage 2 confirms within the already-frozen `confirmBars = 3`; or
2. a fresh `rangeBreakUp` occurs while Formal is already Stage 2, producing a direct entry / re-entry.

For both paths, store the structural level crossed by the fresh break that caused the entry setup:

`entry_break_level = range_high_break` from the fresh-break bar.

After the long position exists, if a later close satisfies:

`close <= entry_break_level`

then the breakout thesis is invalidated and desired exposure becomes flat.

### Short

Mirror the long rule:

`entry_break_level = range_low_break` from the fresh-break bar.

After the short exists, if a later close satisfies:

`close >= entry_break_level`

then the breakdown thesis is invalidated and desired exposure becomes flat.

## Execution / state semantics

- All decisions are close-observed and retain the existing one-bar execution lag used by the Issue #61 strategy proxies.
- The entry bar itself cannot be stopped by the same level; invalidation is evaluated only after a position has already existed from an earlier signal state.
- An invalidation exit clears any armed setup and stored entry level.
- No automatic re-entry is allowed after invalidation. A **new** existing lifecycle fresh-break event is required.
- A same-bar invalidation exit has precedence over any potential same-direction re-entry logic.
- Formal family exit remains active; whichever exit condition appears first can end the position.

## Explicitly not allowed in this phase

- no ATR stop multiple;
- no percentage stop;
- no buffer around the breakout level;
- no intrabar high/low stop simulation;
- no take-profit target;
- no trailing stop;
- no partial sizing;
- no Early-Damaged overlay combination;
- no threshold or rule rescue after seeing Phase-D PnL.

## Comparator

Compare exactly:

1. `stage_lifecycle_base`;
2. `stage_lifecycle_breakout_invalidation`.

Report gross and fixed 2 bp sensitivity, Sharpe, max drawdown, exposure, turnover, holding duration / entries, invalidation-exit counts, and cross-pair consistency.

## Decision rule

This phase asks whether a semantically coherent failed-breakout stop improves the already-frozen base lifecycle **consistently across reused FX pairs**. A favorable single pair is insufficient. If the rule is inconsistent, reject it rather than tune buffers or ATR multiples on these samples.

All samples are reused development evidence. No validation or production trading claim is permitted.