# Issue #57 — Phase A decision

Decision: **phase_a_passed_boundary_robustness**

Phase A is accepted as complete for its stated purpose: materially reducing local price-boundary discontinuity without evaluating trading PnL or reusing the burned Issue #55 Final OOS as an independent validation sample.

## Evidence

- Frozen `chase-risk-market-regime-radar-v0.5.2.1.pine` remains byte-identical to `main` (Git blob `ab6861181a27697ad566c19bf405a0571be2eb1a`).
- Frozen v0.5 Python research mirror remains pinned at Git blob `b7d1c7e02194e46e162c999854aff6907bd5be3d`.
- 50-bar structural-boundary counterfactual:
  - median six-weight L1 jump: `26.092328 -> 0.005560`;
  - median reduction: `99.979%`;
  - v0.6 lower/equal/higher than v0.5: `8 / 0 / 0`;
  - worst remaining v0.6 L1 jump: `0.028210`.
- 20-bar breakout/breakdown counterfactual:
  - median six-weight L1 jump: `18.832590 -> 0.004469`;
  - median reduction: `99.976%`;
  - worst remaining v0.6 event-toggle L1 jump: `0.028210`.

## What Phase A changed

Only boundary-sensitive price evidence/gating families identified by the #55/#57 diagnostics were softened:

1. 50-bar no-break scores;
2. 50-bar structural continuation strength;
3. 20-bar range-break evidence strength;
4. downstream range-break gate strength.

The transition width remains `0.25 ATR`, chosen as an engineering smoothing width and not from trading PnL.

## What Phase A did not validate

This decision does **not** show that v0.6 predicts returns, improves profitability, has calibrated confidence, uses the right number of states, or has acceptable formal-state persistence. Those are separate gates.

## Next gate

Proceed to **Phase B: candidate -> formal-state persistence audit**. Measure disagreement duration, switch delay, one-bar flip rate, dwell-time distribution, and stale-state behavior before changing confirmation/persistence rules.
