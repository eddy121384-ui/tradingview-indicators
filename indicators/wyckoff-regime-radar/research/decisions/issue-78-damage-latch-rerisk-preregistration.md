# Issue #78 — Damage-Latch Re-risk Follow-up Preregistration

## Why this follow-up exists

The already-frozen memoryless progressive ladders may change exposure every time current giveback crosses a health-bucket boundary. Before testing an alternative, freeze one deliberately less reactive architecture whose purpose is to reduce resize churn without introducing a fitted time parameter.

This follow-up is still discovery research. It is motivated by the architecture problem, not by a search over thresholds.

## Frozen architecture

Reuse the Issue #78 frozen giveback buckets and the already-frozen **Gentle** and **Balanced** exposure ladders.

For deterioration:

- de-risk immediately when the current causal giveback bucket maps to a lower target exposure than the current exposure.

For recovery:

- **do not re-risk merely because giveback moves back into a healthier bucket**;
- hold the reduced exposure until the active formal trend makes a **new favorable close-path extreme** relative to the running extreme known so far;
- on that new favorable extreme, reset target exposure to Full (1.00);
- subsequent deterioration can de-risk again using the same frozen ladder.

This is called the **damage latch**. It adds no new ATR threshold and no N-bar confirmation parameter.

## Causal timing

A new favorable extreme observed at close of bar `t` may restore Full exposure only for the next move `t -> t+1`. No same-bar hindsight fill is allowed.

Formal regime loss still sets exposure to zero.

## Candidates

Compare only:

1. Formal Hold baseline;
2. Gentle memoryless ladder;
3. Balanced memoryless ladder;
4. Gentle + damage latch;
5. Balanced + damage latch.

No other re-risk trigger is introduced in this pass.

## Main question

Can a threshold-free recovery latch materially reduce whipsaw / turnover while preserving enough large-trend harvest to remain competitive on the capture-vs-giveback frontier?

Report the same fixed all-episode, MFE >=4 ATR, and MFE >=8 ATR slices, cross-market equal-weighted.

Do not select a production policy from this discovery sample.

Refs #78 and #76.
