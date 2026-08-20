# Issue #61 — Phase A breakout / breakdown trigger audit

Status: **PRE-OUTCOME SEMANTIC AUDIT**.

This note is written before any new lifecycle PnL comparison. It does not change production Pine and does not select a trading lag from returns.

## Question

Which existing price-only mechanism is semantically suitable for the Stage-aware Position Lifecycle definition of an **effective fresh breakout / breakdown**?

The intended lifecycle is:

- Stage 1 / 4 = observe;
- Stage 2 / 5 + effective fresh break = candidate initial entry;
- Stage 3 / 6 = hold / reduce, no chase;
- Stage 3→2 / 6→5 + a new effective fresh break = candidate add-on.

## Existing mechanisms audited

### 1. `rangeBreakUp` / `rangeBreakDn`

```pine
rangeHighBreak = ta.highest(high[1], breakoutBars)
rangeLowBreak  = ta.lowest(low[1], breakoutBars)
rangeBreakUp   = not na(rangeHighBreak) and close > rangeHighBreak and close[1] <= rangeHighBreak[1]
rangeBreakDn   = not na(rangeLowBreak) and close < rangeLowBreak and close[1] >= rangeLowBreak[1]
```

Properties:

- causal on the current bar;
- structurally interpretable: current close crosses a prior rolling range extreme;
- symmetric long / short definitions;
- emits a **fresh event pulse**, rather than remaining true for many bars;
- uses the already-existing `breakoutBars` input (default 20), so no new threshold is invented.

**Phase-A status: primary structural event candidate.**

This does **not** yet mean it is the final entry rule. Formal-stage confirmation may occur after the fresh break, so timing must be audited before entry semantics are frozen.

### 2. `recentBreakUp` / `recentBreakDn`

`recentBreakUp` includes either a range break **or an MA crossover** and remains true for up to `breakoutBars` bars.

Properties:

- not a fresh event pulse;
- mixes two different mechanisms (structural range break and MA cross);
- intentionally carries stale recent evidence.

**Phase-A status: unsuitable as the precise entry event.** It may remain descriptive context.

### 3. `breakoutModeUp` / `breakdownModeDn`

These are defined as low-volatility breakout / breakdown **exemption modes**. They require heat / panic, low-vol history, maturity conditions, and recent-break context, and are used to prevent a strong break from being mislabeled as end-risk.

Properties:

- designed as a risk-warning exemption, not as an entry trigger;
- can stay true after the actual break;
- depends on `recentBreakUp` / `recentBreakDn`, which can originate from MA crossing rather than a structural range break.

**Phase-A status: do not use directly as the lifecycle entry pulse.**

### 4. `breakoutScore`, `explicitBreakdownScore`, and Stage-2 / Stage-5 gates

These scores feed the stage classifier. Markup / Markdown gates also accept extension and continuation pathways in addition to breakout pathways.

Therefore `Formal Stage 2` or `Formal Stage 5` does not imply that a fresh structural break happened on the same bar.

**Phase-A status: stage context / classifier evidence, not a fresh execution pulse.**

## Frozen Phase-A event audit

Before any PnL comparison, measure the timing relationship between fresh structural breaks and Formal trend stages.

For bullish and bearish sides separately, report:

1. total `rangeBreakUp` / `rangeBreakDn` event count;
2. Formal Stage 2 / 5 on the same bar;
3. Formal Stage 2 / 5 first appears within the next 1 / 3 / 5 bars;
4. distribution of first-confirmation lag, capped at 20 bars;
5. whether the path passed through Stage 1→2 / 4→5 or Stage 3→2 / 6→5;
6. how often Stage 3→2 and Stage 6→5 transitions have a genuinely new `rangeBreakUp` / `rangeBreakDn` event rather than merely trend continuation;
7. event counts only — **no return / Sharpe / hit-rate outcome in Phase A**.

The 1 / 3 / 5 checkpoints are descriptive timing snapshots, not candidate trading parameters. Do not choose one because a later backtest looks best.

## Decision rule after Phase A

- If Formal 2 / 5 usually confirms very near a fresh structural break, the lifecycle can use a simple fresh-break + trend-stage handshake.
- If Formal confirmation systematically comes later, define the lifecycle as a two-step state machine (fresh break arms the setup; Formal 2 / 5 confirms within a mechanically justified window) **before** inspecting PnL.
- If Stage 3→2 / 6→5 rarely produces a new structural break, do not force an add-on rule. Treat renewed trend as continuation unless a distinct causal add trigger can be justified without threshold shopping.

## Data boundary

All Issue #57 samples are reused evidence for Issue #61. Phase A is a semantic/timing audit only and cannot create an independent validation claim.
