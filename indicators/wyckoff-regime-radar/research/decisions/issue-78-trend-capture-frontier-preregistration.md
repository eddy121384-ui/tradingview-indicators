# Issue #78 — Trend Capture / Giveback / Whipsaw Frontier Preregistration

## Purpose

Issue #78 studies the original position-management objective behind the Regime Radar:

> When a genuine Markup or Markdown regime appears, how much of the trend can be retained while keeping unavoidable false-start loss, whipsaw, re-entry cost, and terminal giveback within a reasonable range?

This is a successor to Issue #76. It does not change classifier semantics.

## Universal-first principle

Primary conclusions are cross-market and equal-market weighted. Asset-class slices may diagnose heterogeneity but may not introduce FX/rates/equity/commodity-specific parameter sets.

If a result requires market-specific tuning to survive, downgrade universality rather than add parameters.

## Primary trend regimes

The first-pass management study focuses on the two persistent directional regimes:

- Markup: positive-direction trend regime.
- Markdown: negative-direction trend regime.

Accumulation, Distribution, Reaccumulation, and Redistribution remain part of the broader classifier but are not assumed to be equally attractive for initiating directional risk.

## Frozen first-pass questions

1. How often does a newly identified trend regime fail before becoming a meaningful trend?
2. Does surviving for 5/10/20 bars improve trend quality, and what early-move capture is sacrificed by waiting?
3. How much trend does a pure Formal Exit retain after the best favorable point has already occurred?
4. How does giveback-based damage detection trade lower terminal giveback against false exits and missed continuation?
5. Is there a stable cross-market frontier rather than one optimized stop/exit threshold?

## Frozen primary metrics

All directional outcomes are aligned so positive means favorable to the active trend regime.

- Trend opportunity / MFE in entry-ATR units.
- Retained directional move.
- Trend Capture Ratio = retained directional move / maximum favorable move available in the episode, when the denominator is positive.
- Terminal Giveback = maximum favorable move minus retained move at exit.
- Failed-regime adverse excursion.
- False Exit Rate = defensive exit followed by a later new favorable extreme within the same formal regime episode.
- False Exit Cost = additional favorable move that occurs after the defensive exit.
- Re-entry count / re-entry cost for dynamic gating.
- Regime survival / hazard by age and health.

## Frozen discovery landmarks

Regime-age landmarks: 0, 5, 10, 20 bars.

Existing exploratory giveback landmarks from Issue #76 remain frozen for the first frontier map:

- <0.5 ATR
- 0.5–1 ATR
- 1–2 ATR
- 2–4 ATR
- 4+ ATR

These boundaries are not to be tuned on the current nine-market discovery sample.

## Management philosophies

### A. Late / Formal Exit
Maintain full directional exposure until the formal trend regime is no longer active.

### B. Early Defensive Exit
Exit when a pre-defined damage/giveback condition is reached and remain out for the remainder of that formal regime episode.

### C. Dynamic Health Gate
Permit exposure only while the frozen health condition remains acceptable; re-entry within the same formal regime is allowed if health recovers.

### D. Progressive De-risking
Compare a fixed monotonic exposure schedule across the frozen health buckets. This is a structural comparison, not a threshold optimizer.

## Sample policy

The accepted Issue #76 nine-market 1D sample may be reused for discovery, mechanism understanding, and frontier construction.

Any policy selected after viewing these results is in-sample discovery. Before being called a robust trading policy, it must be frozen and challenged on new markets / asset classes, weekly data and/or prospective observations.

## Anti-overfit guardrails

- no optimizer over stop / target / trailing parameters;
- no market-specific parameter sets;
- no choosing a single "best" age or threshold solely from current-sample PnL;
- no classifier retuning;
- no attempt to force long/short symmetry;
- no claim that maximum trend capture and minimum giveback can both be achieved without cost.

The intended output is a trade-off frontier and a small number of robust management hypotheses, not a perfect exit rule.

Refs #78 and #76.
