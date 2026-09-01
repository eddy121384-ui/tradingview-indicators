# Issue #68 Phase B3.16 — Human Review Closeout / B3.17 Direction

Status: **B3.16 HUMAN PASS — NARROW LOCAL CAUSAL EFFECT ONLY**

## Reviewed TradingView set

Bull / 1D:
- FR10Y — primary adverse case
- JGB10Y — locked rates control
- US10Y — additional rates context
- EURUSD — control
- S&P 500 — control

## Human finding

The B3.16 counterfactual does visibly create `RAW ADVANCE` bars inside the same `STALE OVERLAP` episodes identified in B3.15. The strongest rates evidence is local rather than broad:

- FR10Y shows a visible raw-advance episode around the late-2023 / early-2024 handoff where observed raw remains old-side while shadow raw is already target-side inside stale overlap.
- FR10Y also shows several Break-release events that do not propagate into raw advance, confirming that removing the stale source is not a universal cure.
- JGB10Y and US10Y show similarly sparse local releases rather than wholesale regime rewrites.
- EURUSD and S&P 500 also exhibit local releases, supporting the interpretation that this is a generic handoff-memory mechanism rather than a rates-only defect.

## Decision

Accept B3.16 as:

`confirmed_local_causal_stale_range_brake`

Do **not** accept either stronger claim:

- `stale_range_memory_explains_full_rates_reversal_lag`
- `remove_old_range_memory_is_ready_for_production`

The visual result is consistent with the mechanical frozen-FX result: the effect is real, usually short-lead, and episodic. In the primary adverse FR10Y window it does not repair the full multi-year lag.

## Why the next phase is not parameter tuning

B3.16 selected a strict event population around known Break-final-blocker handoffs. Before any production semantics change, the fixed rule must be tested **globally** on every eligible stale-overlap bar, including bars that were not followed by a successful handoff.

Otherwise the event-selected result could hide false early releases, one-bar flips, or churn.

## Next phase — B3.17 Global False-Release / Churn Audit

Apply the exact fixed B3.16 shadow rule to all eligible bars:

`MA target-side + old range memory active -> remove only old-direction range-memory source from old Break score`

No parameter changes.

Measure whether the global shadow creates:
- extra raw sign flips not followed by a durable observed handoff;
- one-bar / short-lived target flips;
- repeated flip-flop inside the same MA-side run;
- materially higher raw-transition count;
- asymmetry under reciprocal OHLC;
- control-market distortions.

B3.17 is a safety / semantics gate only. No PnL.

## Boundary

No `breakoutBars` tuning, no Break-weight tuning, no MA-length change, no threshold search, no production C-2 modification, no PnL / Strategy Tester selection.
