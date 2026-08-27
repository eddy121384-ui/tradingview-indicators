# Issue #68 Phase B2 — lifecycle semantic audit transport

Status: preregistered before reviewing a replacement TradingView chart.

## Why Phase B2 exists

The first Phase B TradingView artifact mixed two different visual clocks on the same chart:

1. the lifecycle event is decided at bar close `t`; and
2. `strategy(..., process_orders_on_close=false)` renders the resulting order on the next executable bar.

The artifact also displayed custom ARM/ENTRY/FAIL/EXIT shapes while TradingView rendered native strategy order markers. The duplicated labels make human semantic review ambiguous and visually noisy. This is a review-transport failure, not evidence by itself that the frozen lifecycle state machine is wrong.

## Frozen semantic parent

Phase B2 MUST preserve the exact Issue #68 / Issue #61 human-review-v2 lifecycle state machine already tested in Phase A:

- Stage 1 fresh breakout -> Stage 2 within `confirmBars=3` for initial long;
- mirrored Stage 4 -> Stage 5 for initial short;
- exact transition-bar fresh break accepted;
- no flat chase inside an already-running Stage 2 / 5;
- Formal 0 / same-side pauses do not force exit;
- exit only on the opposite Formal family;
- Early Fail only at entry ages 1..`confirmBars`;
- Early Fail requires a brand-new setup cycle before re-entry;
- continuation fresh breaks while holding remain observation-only `ADD?` events.

No classifier, threshold, lifecycle rule, stop, target, sizing rule, or entry/exit rule may change in Phase B2.

## Audit transport

Generate a separate `indicator(..., overlay=false)` from the Phase B source. It MUST:

- contain no `strategy.entry`, `strategy.close`, or other order calls;
- preserve the lifecycle state-machine segment byte-for-byte;
- plot desired position as a step line: `+1 / 0 / -1`;
- show ARM events at `+0.5 / -0.5`;
- show ENTRY at `+1 / -1`;
- show Early Fail and opposite-family EXIT with distinct symbols;
- use the Formal stage only as a faint pane background;
- keep Formal ID, desired position, ARM direction, Early Fail age, and anchor in Data Window.

The purpose is human timing/semantic review only. Strategy Tester output is explicitly out of scope.

## Acceptance

Phase B2 static gate passes only if:

1. the audit artifact has an `indicator(...)` declaration and no `strategy.` calls;
2. the lifecycle state-machine segment is byte-identical to the Phase B strategy artifact;
3. Phase A synthetic semantics and the >=95% reciprocal lifecycle gate still pass unchanged.

Only after a clean Phase B2 human review may the strategy-order transport be used for performance work.
