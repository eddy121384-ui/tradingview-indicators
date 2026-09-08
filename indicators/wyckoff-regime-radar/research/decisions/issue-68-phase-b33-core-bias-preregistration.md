# Issue #68 Phase B3.3 — Core Bias Memory Preregistration

Status: **preregistered semantic architecture experiment / no PnL**

## Why B3/B3.2 failed

A single `position = -1/0/+1` state was being asked to represent two different concepts:

1. persistent trend/bias memory; and
2. current exposure authorization.

That conflation makes every Stage1/4 range/precursor call destructive: flattening exposure also erases the trend memory, producing repeated washout/re-entry inside large trends.

B3.2 showed that delaying Stage1/4 flattening by the inherited `confirmBars=3` grace window is insufficient and should not be threshold-tuned further.

## B3.3 scope

B3.3 introduces a **core bias state only**. It is not yet the executable desired exposure.

### Core bias state machine

Initial state: `0`.

From Flat/unknown bias:
- Formal 2 => bias +1
- Formal 5 => bias -1
- all other stages => remain 0

Existing bullish bias +1:
- Formal 5/6 => flip bias to -1
- Formal 0/1/2/3/4 => keep +1

Existing bearish bias -1:
- Formal 2/3 => flip bias to +1
- Formal 0/1/4/5/6 => keep -1

Thus Stage1/4/0 cannot erase core trend memory. Only an opposite trend family can reverse it.

## Important semantic boundary

B3.3 bias is **not a trade position**. It may remain +1/-1 through a sustained range by design. A later exposure layer will decide whether a biased market warrants full, reduced, or zero directional exposure using the existing Flat Action / Pace framework.

Do not interpret B3.3 occupancy as portfolio exposure and do not compute PnL.

## Gates

- synthetic reciprocal core-bias sequence: exact mirror;
- burned four-FX core-bias reciprocal mirror >= 99.00%;
- compare trend-bias flip counts with B3 position episode churn;
- no return/PnL/Sharpe/drawdown/hit-rate/cost/sizing/stop/target metrics.

## Human review objective

EURUSD 1D should show a stable bearish core bias through the broad 2021–2022 downtrend unless the classifier truly confirms an opposite bullish trend family. Stage1/4 fluctuations alone must not erase the bearish bias.
