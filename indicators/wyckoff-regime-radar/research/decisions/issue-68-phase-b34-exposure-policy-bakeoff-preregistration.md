# Issue #68 Phase B3.4 — Exposure Policy Bakeoff Preregistration

Status: **preregistered semantic comparison / no PnL**

Parent milestone: B3.3 Core Bias Memory. The Core Bias architecture is frozen for this phase and must not be modified.

## Objective

Translate the frozen B3.3 directional memory into executable ternary exposure without re-merging the concepts of direction memory and current position.

Required invariant:
- Core Bias +1 may produce only Long or Flat exposure.
- Core Bias -1 may produce only Short or Flat exposure.
- Core Bias 0 must produce Flat exposure.
- Local range / clue states may reduce exposure to Flat but must not reverse Core Bias.

No return, PnL, Sharpe, drawdown, hit-rate, cost, stop, target, sizing optimization, or Strategy Tester metric may be used to choose among candidates.

## Frozen candidates

### Candidate A — Formal trend-family exposure

- Bull Bias + Formal 2/3 => Long.
- Bear Bias + Formal 5/6 => Short.
- Otherwise => Flat.

Purpose: simplest direct translation of trend-family participation versus non-trend observation.

### Candidate B — Flat Action authorization exposure

Reuse the existing v0.5 Flat Action output exactly; add no new thresholds.

- Bull Bias + Flat Action F2/F3 => Long.
- Bear Bias + Flat Action F4/F5 => Short.
- Otherwise => Flat.

Purpose: test the existing dedicated flat-entry authorization layer as the complete exposure gate.

### Candidate C — Stateful Flat Action entry + Pace defensive flat

Entry/re-entry:
- from Flat, Bull Bias requires F2/F3 to enter Long;
- from Flat, Bear Bias requires F4/F5 to enter Short.

Holding:
- while Core Bias remains aligned, exposure persists unless an existing Pace Guide state explicitly moves the binary implementation into defensive/observe mode.

Mirrored defensive-flat mappings, derived from existing Pace text only:
- Long defensive/observe: Pace 0, 40, 70, 71, 75.
- Short defensive/observe: Pace 0, 15, 70, 71, 74.

Bias reversal:
- an exposure whose sign no longer matches Core Bias first returns to Flat;
- no direct Long-to-Short or Short-to-Long executable flip is allowed inside Candidate C;
- a later same-direction Flat Action authorization is required to re-enter under the new Bias.

No new numeric threshold is introduced.

## Human semantic review target

TradingView EURUSD 1D remains the first visual gate.

The preferred behavior is not selected by profitability. The review asks:
1. Does a major trend spend meaningful time exposed in the Bias direction?
2. Do broad range / ambiguous periods recover genuine Flat intervals?
3. Does exposure avoid repeatedly taking the direction opposite to Core Bias?
4. Does the policy avoid pathological one-bar on/off churn?
5. Does the 2021–2022 EURUSD bearish regime remain directionally coherent while permitting sensible observation gaps rather than bullish flips?

No candidate is accepted until human semantic review.
