# Issue #61 — Early-Damaged lifecycle overlay freeze

Status: **FROZEN BEFORE OVERLAY PNL**.

This note fixes the exact way the already-frozen Issue #57 Transition Health mechanism is allowed to interact with the Issue #61 base lifecycle. No overlay PnL has been inspected before writing this rule.

## Preserved engines

- Base lifecycle rules remain exactly those frozen in `issue-61-phase-a-timing-decision.md` and evaluated in `issue-61-stage-lifecycle-base.md`.
- Transition Health is the exact Issue #57 online state machine carried forward byte-for-byte from archived PR #58.
- `CHECKPOINT = 3` and `MAX_WATCH_BARS = 20` are inherited from Issue #57; they are not re-tuned here.

## Early Damaged pulse

Issue #57 defines a tracked handoff when one new-direction carried stage already leads the old context stage at bridge onset.

During watch ages +1 through +3, the first bar where strict `carried > context` is no longer true is the **Early Damaged** pulse. `NaN` also fails the strict lead, matching the frozen Issue #57 semantics.

No weight-margin magnitude threshold is added.

## Lifecycle interaction

The third comparison variant is `stage_lifecycle_plus_early_damage`.

It starts from the exact base lifecycle state machine and adds only the following risk overlay:

1. If a long position is active and a bullish Transition Health watch emits a matching Early Damaged pulse, exit the long to flat at that close signal.
2. If a short position is active and a bearish watch emits a matching Early Damaged pulse, exit the short to flat at that close signal.
3. The damaged direction is **blocked from new entry while that same Transition Health watch remains active**.
4. The block is removed when the frozen Transition Health watch emits its resolution pulse (same-direction actionable pair, opposite actionable pair, or 20-bar timeout).
5. Removing the block does **not** automatically restore exposure. A future position must satisfy the unchanged base lifecycle entry mechanism again: a fresh structural break / armed setup / trend-stage confirmation, or a fresh break while the matching trend stage is already Formal.
6. `Healthy +3` does not enter, re-enter, add, or automatically restore position. It remains confirmation / hold-quality information only.
7. An Early Damaged pulse that does not match the currently held direction does not force an unrelated exit.
8. Any armed same-direction setup is cancelled when its direction receives Early Damaged, preventing an already-damaged handoff from confirming into a new position during the same watch.

## What is intentionally not tested here

- no stop loss;
- no profit target;
- no trailing stop;
- no partial-profit percentage;
- no reduced Stage-3 / Stage-6 position size;
- no add-on leverage;
- no Healthy-based re-risk;
- no new breakout threshold;
- no weight-margin threshold.

## Comparison

Report all three on the same reused four-FX fixtures:

1. `binary_color`;
2. `stage_lifecycle_base`;
3. `stage_lifecycle_plus_early_damage`.

The primary question for the overlay is incremental risk efficiency versus `stage_lifecycle_base`: return, Sharpe, drawdown, exposure, turnover, and the number of Early-Damaged exits/blocks.

## Boundary

This is reused development evidence only. A favorable overlay result does not validate a trading system and does not authorize post-outcome tuning of the Early-Damaged rule.
