# Issue #68 Phase B3.2 — Range-Grace Hold Semantics Preregistration

Status: **preregistered semantic experiment / no PnL**

## Motivation

B3 human review on EURUSD 1D showed that regime-first v3 materially restored trend exposure but still washed established positions out too often inside large trends. The failure is localized to hold/exit semantics: Formal Stage 1/4 immediately forced Flat.

The opposite overcorrection — holding forever through 1/4 — would violate the other half of the objective because sustained range regimes should eventually remove directional exposure.

## Frozen B3.2 state machine

No entry rule changes in this phase.

### Flat

- Formal 2 => Long
- Formal 5 => Short
- all other Formal stages => Flat

### Existing Long

- Formal 2/3 => keep Long and reset range-grace counter
- Formal 5/6 => flip directly to Short and reset range-grace counter
- Formal 1/4 => increment range-grace counter; keep Long while counter < `confirmBars`; exit to Flat when counter reaches `confirmBars`
- Formal 0 => keep Long; do not advance or reset the range-grace counter

### Existing Short

- Formal 5/6 => keep Short and reset range-grace counter
- Formal 2/3 => flip directly to Long and reset range-grace counter
- Formal 1/4 => increment range-grace counter; keep Short while counter < `confirmBars`; exit to Flat when counter reaches `confirmBars`
- Formal 0 => keep Short; do not advance or reset the range-grace counter

## Parameter boundary

B3.2 introduces **no new threshold**. The grace window reuses the classifier's inherited `confirmBars` value (default 3).

## Gates

Before human TradingView review:

1. synthetic mirrored sequences must produce exact reciprocal position/event behavior;
2. burned four-FX desired-position reciprocal mirror must remain >= 99.00%;
3. B3.2 should reduce range-triggered washout events versus B3 without consulting returns;
4. report occupancy, holding duration, episode counts, and range-grace exits only;
5. no return/PnL/Sharpe/drawdown/hit-rate/cost/sizing/stop/target metrics.

## Human-review objective

On EURUSD 1D, B3.2 should visibly preserve core Short exposure through transient 2021–2022 consolidation calls better than B3, while still allowing genuinely sustained Stage 1/4 ranges to return the lifecycle to Flat.

Entry quality inside 2023–2024 ranges is explicitly **out of scope** for B3.2 and remains a later experiment.
