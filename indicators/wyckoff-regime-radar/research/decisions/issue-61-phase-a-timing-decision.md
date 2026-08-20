# Issue #61 — Phase A timing decision

Status: **FROZEN BEFORE PHASE-B PNL**.

This decision is based only on the preregistered fresh-break / Formal-stage timing audit. No return, hit-rate, Sharpe, stop, sizing, or PnL statistic has been inspected for the lifecycle rules below.

## Evidence used

Four already-burned, repository-pinned FX D1 fixtures were evaluated with the exact Issue #57 v0.6 Phase-B six-stage engine carried forward byte-for-byte.

Aggregate timing result:

- Bull fresh `rangeBreakUp`: 282 events.
  - 104 occurred when Formal Stage 2 was already active before the break.
  - 178 occurred before Stage 2 was already active.
  - of those 178, Stage 2 appeared same bar in 20, by +3 in 47, by +5 in 54, and by +20 in 82.
- Bear fresh `rangeBreakDn`: 277 events.
  - 94 occurred when Formal Stage 5 was already active before the break.
  - 183 occurred before Stage 5 was already active.
  - of those 183, Stage 5 appeared same bar in 25, by +3 in 67, by +5 in 80, and by +20 in 95.

Initial Formal transitions were much more tightly associated with a preceding break:

- Stage 1→2: 22 events; fresh up break same bar 6, within prior 1 bar 12, within prior 3 bars 16, within prior 5 bars 18, within prior 20 bars 21.
- Stage 4→5: 12 events; fresh down break same bar 2, within prior 1 bar 5, within prior 3 bars 11, within prior 5 bars 12, within prior 20 bars 12.

Literal Formal renewal transitions were too sparse to support an add rule:

- Stage 3→2: 2 events, 0 same-bar fresh breaks.
- Stage 6→5: 0 events.

## Interpretation

### 1. Do not wait for Formal Stage 2 / 5 indefinitely after every break

A fresh structural break frequently does **not** become Formal Stage 2 / 5 within 20 bars. Therefore `fresh break -> eventually wait for Formal` is not an acceptable open-ended execution rule.

### 2. Initial 1→2 / 4→5 transitions support a short break-then-confirm handshake

When the classifier actually makes the intended initial transition from Accumulation to Markup or Distribution to Markdown, a fresh structural break is usually close in time, especially within the model's already-existing confirmation horizon.

Phase B therefore freezes the setup window at the existing `confirmBars` value (**3 bars under defaults**). This is a model-semantic choice, not a PnL-selected lag.

### 3. A fresh break inside an already-active Stage 2 / 5 is a distinct event class

Roughly one third of fresh breaks occurred while the matching trend stage was already Formal. These are not initial stage confirmations. They are **trend-stage continuation break events** and are retained as candidate re-entry / future add-on events.

The first Phase-B proxy will not increase leverage on these events because add size has not been preregistered. It will count them separately for later risk/sizing research.

### 4. Do not force literal Stage 3→2 / 6→5 as the add mechanism

The current Formal six-state path almost never emits those literal renewal transitions in the pinned FX sample. The Issue #61 preregistered decision rule explicitly said to stop forcing the add-on concept if this path was rare.

Therefore Stage 3 / 6 remain valid descriptive hold/consolidation states, but Phase B will **not require** literal 3→2 / 6→5 to make the base lifecycle test work.

## Frozen Phase-B base lifecycle semantics

No stops, take-profit percentage, partial-size percentage, leverage, or tuned breakout threshold is introduced.

### Flat / entry logic

Long side:

1. Stage 1 = observe; no long solely from the stage.
2. A fresh `rangeBreakUp` while Stage 1 is Formal arms a bullish setup for `confirmBars` bars.
3. If Formal Stage 2 appears while that setup is still armed, emit a long-entry signal.
4. If the same fresh break bar itself transitions 1→2, emit the signal on that bar.
5. If Stage 2 is already Formal while flat and a fresh `rangeBreakUp` occurs, emit a trend-stage breakout re-entry signal.
6. An armed setup expires after `confirmBars`; it does not wait indefinitely.

Short side is the exact mirror using Stage 4, Stage 5, and `rangeBreakDn`.

### Holding / exit logic

- Long exposure is allowed to remain while Formal is Stage 2 or Stage 3.
- Short exposure is allowed to remain while Formal is Stage 5 or Stage 6.
- Stage 3 / 6 does **not** add exposure in Phase B; it means hold core / no chase.
- If an existing long leaves the {2,3} family, exit to flat.
- If an existing short leaves the {5,6} family, exit to flat.
- Stage 1 / 4 are therefore observe states when flat and exit-to-observe states when the prior trend family has ended.

### Continuation-break diagnostic

A fresh same-direction range break while already holding in matching Formal Stage 2 / 5 is counted as a candidate continuation/add event, but position size remains 1.0 in the base proxy.

## Phase-B comparison

First compare:

1. `binary_color` historical comparator: 1/2/3 long; 4/5/6 short.
2. `stage_lifecycle_base`: the frozen rules above, unit exposure only.

Only after the base lifecycle result is recorded may the already-frozen Early-Damaged overlay be added as a separate third variant.

Execution must be causal: close-observed signals affect the next close-to-close return.

## Boundary

All data used here are reused evidence. A favorable Phase-B result is development evidence only and requires a later untouched sample before any validation or production trading claim.
