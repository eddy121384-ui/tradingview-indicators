# Issue #68 Phase B3.15 — Human review closeout / B3.16 direction

Status: **B3.15 human review PASS for a local stale-memory mechanism; NOT a primary-cause claim**.

## Reviewed TradingView evidence

User-provided 1D Bull-direction screenshots on 2026-09-01 covered:

- FR10Y — locked primary adverse rates case;
- JGB10Y — locked rates control;
- US10Y — additional rates context;
- EURUSD — FX control;
- S&P 500 — non-rates directional control.

The B3.15 visual contract was unchanged:

- BREAK EDGE: green target / red old;
- MA TARGET SIDE: green when current MA relation is target-side;
- OLD RANGE MEMORY: red while old range-break memory remains active;
- STALE OVERLAP: yellow when MA is target-side while old range memory remains active;
- NEW RANGE EVIDENCE: green when target range evidence exists;
- BREAK OLD DURING OVERLAP: red when stale overlap exists while Break still votes old;
- MA FLIP: aqua;
- BREAK FINAL BLOCKER: orange.

## Human review result

### FR10Y — primary adverse case

PASS for mechanism visibility.

Across the 2021–2024 adverse window there are repeated, visually coherent sequences where:

1. MA relation flips to / remains on the Bull target side;
2. OLD RANGE MEMORY remains active;
3. the yellow STALE OVERLAP persists for multiple bars rather than appearing only as a one-bar artifact;
4. red BREAK OLD DURING OVERLAP marks occur inside those windows;
5. in several of those windows NEW RANGE EVIDENCE is already present before the old range memory clears.

This is the exact qualitative sequence preregistered for B3.15. The mechanism therefore survives the primary adverse-case review.

However the yellow/red windows are episodic, not continuous through the entire multi-year adverse period. B3.15 therefore does **not** establish stale Break memory as the sole or dominant explanation for the full FR10Y regime lag.

### JGB10Y — rates control

The same mechanism is visible but generally cleaner / more episodic. Mature Bull sections return to the expected clean state: target-side MA, old range memory cleared, target Break and new range evidence established.

This supports the interpretation that the Break module is not permanently stuck. The issue is handoff-local.

### US10Y — additional rates context

Repeated stale-overlap / Break-old windows are visible around major yield handoffs, including the post-2022 regime changes. This shows the pattern is not unique to FR10Y.

### EURUSD and S&P 500 — controls

Both controls also exhibit isolated stale-overlap windows and Break-old marks. Therefore the mechanism is **not rates-specific**. This weakens any claim of a special rates-only defect, while supporting a generic handoff-memory effect in the Break component.

## Combined B3.15 interpretation

Mechanical evidence already showed that only **20/106** Break-final-blocker events are in the strict causal population where MA is already target-side at the blocker. Within that population:

- old range-memory survival and Break release are both slow;
- target range evidence is typically much faster;
- target range appears before old memory clears in all jointly observable cases;
- Break remains old-negative through a majority of stale-overlap bars.

The TradingView review now confirms that this sequence is genuinely visible in FR10Y and is not an FX-only mechanical artifact.

Decision:

**B3.15 PASS as `credible_local_stale_range_memory_handoff_delay`, but reject the stronger statement `stale_break_memory_is_the_primary_full_rates_lag_cause`.**

## B3.16 direction

Do not tune `breakoutBars`.

The next question is causal rather than parametric:

> If the old-direction range-memory contribution were removed only after the current MA relation has already flipped to the target side, would Break and total S2-vs-S5 raw handoff actually release earlier?

B3.16 should therefore be one preregistered **counterfactual stale-range-release shadow**, not a parameter search.

Production C-2 remains frozen. No PnL / Strategy Tester interpretation. PR #73 stays Draft / Open and Issue #68 stays Open.
