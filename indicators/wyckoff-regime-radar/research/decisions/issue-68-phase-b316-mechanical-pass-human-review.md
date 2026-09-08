# Issue #68 — B3.16 mechanical closeout / human review gate

Status: **MECHANICAL PASS / HUMAN RATES REVIEW REQUIRED / production C-2 frozen**

## Result

The preregistered one-source counterfactual passed all engineering gates.

Exact reproduction:
- Break final-blocker events: 106 / 106;
- strict B3.15 primary population: 20 / 20;
- reciprocal shadow-sign agreement: 100%;
- observed and shadow six-component reconstruction error <= 2.842e-14.

At the strict blocker bar `t-1`, removing only the old-direction range-memory source during `MA target-side + old range memory active` produces:
- shadow Break target-positive: 6 / 20 (30%);
- shadow Break neutral: 14 / 20 (70%);
- shadow Break still old-negative: 0 / 20;
- shadow total six-component raw target-positive: 16 / 20 (80%).

For those 16 events the earliest shadow-total target-positive bar occurs a median 1 bar before the observed handoff, p75 2 bars, max 7 bars.

## Interpretation

This is stronger than a mere correlation result.

Within the narrow preregistered B3.15 causal population, the stale old range-memory contribution is **sufficient to delay the fresh S2<->S5 raw handoff in most cases**. Importantly, it usually acts as a brake rather than as an independently dominant opposite signal: in 14/20 cases the counterfactual Break becomes neutral rather than target-positive, yet removal of that negative drag is enough for the other five frozen components to move the total raw duel to the target side in 16/20 cases.

Decision classification:

**confirmed_local_causal_stale_range_brake**

The stronger claim remains rejected:

**not_the_primary_full_rates_lag_explanation**

Reason: the strict population is only 20 of the 106 Break-final-blocker events, and B3.15/B3.16 do not explain the 86 cases where the blocker occurs before the MA relation flips.

## Accounting note

B3.16 reports 55 stale-overlap observations because the counterfactual event window is deliberately restricted to each primary event's MA flip through its blocker bar `t-1`. This is not the same denominator as B3.15's longer post-flip MA-run overlap accounting (166 bars).

Within the B3.16 event windows:
- observed Break old-negative: 46 / 55 observations;
- shadow Break target-positive: 16;
- shadow Break neutral: 39;
- shadow Break old-negative: 0;
- NEW RANGE present + observed Break old + shadow Break target: 2 observations.

This reinforces that the primary causal effect is often **removing stale negative drag**, not necessarily manufacturing a new positive Break vote.

## Human review artifact

Use:

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue68-phase-b316-counterfactual-stale-range-release-audit.pine`

Locked visual review:
1. FR10Y 1D Bull — primary adverse case;
2. JGB10Y 1D Bull — rates control;
3. US10Y 1D Bull — additional rates context;
4. EURUSD 1D Bull — control;
5. S&P 500 1D Bull — control.

Bands:
- OBS BREAK: current frozen Break vote;
- SHADOW BREAK: Break after removing only stale old range-memory source during overlap;
- OBS RAW: current frozen six-component S2-vs-S5 raw edge;
- SHADOW RAW: same raw edge with only the fixed Break counterfactual;
- STALE OVERLAP: MA is already target-side while old range memory remains active;
- NEW RANGE: target range evidence exists;
- BREAK RELEASE: observed Break is old but shadow Break becomes target-positive;
- RAW ADVANCE: observed raw is not target-positive but shadow raw is target-positive;
- BREAK FINAL BLOCKER: observed exact handoff event.

Human question: around the adverse FR10Y handoffs previously identified in B3.15, do RAW ADVANCE windows visibly occur inside the same stale-overlap episodes, and do they represent plausible earlier regime recognition rather than isolated one-bar artifacts? Controls cannot rescue a failure in FR10Y.

## Boundary

No PnL, no Strategy Tester interpretation, no `breakoutBars` tuning, no Break-weight tuning, no MA changes, no threshold search, no production C-2 modification, no Volume / MTF / Divergence / HMM rescue.
