# Issue #61 — Stage 3 / Stage 6 structural decision

Status: **DO NOT USE FORMAL OR CANDIDATE STAGE 3/6 AS POSITION-MANAGEMENT TRIGGERS**.

This decision is based on pre-PnL occupancy audits only.

## Formal occupancy while base lifecycle holds

- Long exposure: 1,409 bars total; Formal Stage 3 appears only **5 bars (0.35%)**, one run, in one of four FX pairs.
- Short exposure: 1,378 bars total; Formal Stage 6 appears **0 bars**.

## Candidate occupancy while base lifecycle holds

- Candidate Stage 3 appears **6 bars (0.43%)**, four runs, across only two of four FX pairs; median pair run length among pairs with any occurrence is one bar.
- Candidate Stage 6 appears **0 bars**.

## Interpretation

The current v0.6 six-weight engine does not operationally populate Re-accumulation / Redistribution as durable Formal or Candidate states in these pinned FX fixtures. This is consistent with Issue #57's earlier decision to prefer four-state macro semantics while retaining six internal weights.

Therefore Issue #61 must not force the user's intended partial-profit / hold behavior onto literal Stage 3 / Stage 6 IDs. A rule keyed to those IDs would be almost inert and would not represent the intended lifecycle.

## Revised architecture — semantic, not outcome-tuned

Preserve the user's original lifecycle concept but separate **regime** from **position substate**:

- Formal macro regime answers whether the market is in observation/basing, bullish trend, distribution/topping, or bearish trend.
- A separate **Trend Consolidation** substate should describe a temporary range/pullback *inside an already-active trend position*.
- A fresh same-direction structural break after that consolidation becomes the candidate renewed-trend / add-on event.

This does not re-label Stage 3/6 after seeing returns. It acknowledges that the v0.6 classifier already behaved as a four-state macro model and avoids pretending that missing states are useful triggers.

## Next pre-PnL audit

Before defining any new consolidation rule, inspect only existing price-only structural fields already present in v0.6 while the base lifecycle is holding:

- `range_score` and its existing gate boundaries;
- existing range / continuation diagnostics where available;
- fresh `rangeBreakUp` / `rangeBreakDn` after a consolidation-like interval.

First report occupancy, episode counts, and duration only. Do not select a threshold from returns.

If the existing range machinery cannot produce a usable consolidation substate without inventing/tuning new thresholds, stop and keep the lifecycle simpler rather than restoring Stage 3/6 by force.

## Boundary

No PnL was inspected for this Stage3/6 structural decision. All data remain reused development evidence.
