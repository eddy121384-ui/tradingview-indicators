# Issue #61 — Phase E early breakout-invalidation freeze

Status: **PRE-OUTCOME RULE FREEZE**.

Phase D found that the entry breakout level contains useful risk information but that an always-on stop is too aggressive for a trend lifecycle. This Phase E is a new reused-data development hypothesis, not a rescue of the Phase-D result and not OOS evidence.

## Frozen rule

Keep the exact Phase-D structural entry anchor:

- long anchor = `range_high_break` from the fresh upside break that caused entry;
- short anchor = `range_low_break` from the fresh downside break that caused entry.

The only change is **time scope**.

### Early invalidation window

The anchor can invalidate a trade only for the first existing model confirmation window after entry / re-entry:

`early_window_bars = confirmBars = 3`

Entry bar age is 0. The next three completed signal bars are ages 1, 2, and 3.

During ages 1–3:

- long exits if `close <= entry_break_level`;
- short exits if `close >= entry_break_level`.

If the trade survives through age 3 without invalidation, the structural stop anchor is retired. From that point onward, the ordinary frozen base lifecycle / Formal family exit controls the position.

### After an early stop

- desired exposure becomes flat;
- no automatic re-entry;
- a new matching fresh break while Formal is Stage 2 / 5 is required;
- that re-entry starts a new age-0 early invalidation window with a new structural anchor.

## Explicitly unchanged / prohibited

- no ATR or percentage buffer;
- no new bar-count parameter: use the existing `confirmBars = 3` exactly;
- no take-profit target;
- no trailing stop;
- no partial sizing;
- no Early-Damaged combination;
- no continuation-break re-anchoring while already holding;
- no threshold shopping after results.

## Comparators

Report exactly:

1. `stage_lifecycle_base`;
2. `stage_lifecycle_breakout_invalidation` (Phase-D always-on comparator);
3. `stage_lifecycle_early_breakout_invalidation`.

Primary question: can the early-only version retain the drawdown benefit of structural invalidation without collapsing holding duration / exposure as severely as the always-on version?

All data are reused development evidence. Favorable results require future untouched validation before production claims.