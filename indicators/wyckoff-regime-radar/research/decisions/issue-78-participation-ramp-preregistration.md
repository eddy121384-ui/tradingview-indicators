# Issue #78 — Participation Ramp Preregistration

## Purpose

Test whether a trend should begin as a probe position and earn larger exposure only after causal evidence accumulates, before the already-frozen Issue #78 health / damage-latch layer manages deterioration.

This is discovery research on the accepted Issue #76 nine-market daily sample. It is not OOS validation and does not select a production policy.

## Scope and invariants

- Formal trend regimes remain unchanged: Markup and Markdown only.
- Classifier logic, feeds, representation, thresholds and witness settings remain frozen.
- Cross-market equal weighting is primary; asset-class-specific ramps are prohibited.
- All decisions are causal and apply to the next bar only.
- The existing Issue #78 giveback buckets and Gentle / Balanced damage-latch ladders remain unchanged.

## Participation states

Use four fixed exposure caps:

`Probe 25% -> Build 50% -> Confirmed 75% -> Full 100%`

The purpose is not to optimize these percentages but to compare distinct evidence architectures.

## Frozen participation candidates

### A. Full-at-entry baseline

Immediately permit 100% exposure on the first formal Markup / Markdown bar.

### B. Persistence Ramp

Exposure cap depends only on formal-regime age:

- age 0–4 bars: 25%
- age 5–9 bars: 50%
- age 10–19 bars: 75%
- age 20+ bars: 100%

These 5 / 10 / 20 bar landmarks are reused from the already-preregistered Issue #76 / #78 lifecycle work.

### C. Excursion-Proof Ramp

Start at 25%. Increase the participation cap when the active formal trend demonstrates favorable excursion from episode entry in entry-ATR units:

- favorable excursion < 0.5 ATR: 25%
- >= 0.5 ATR: 50%
- >= 1.0 ATR: 75%
- >= 2.0 ATR: 100%

The 0.5 / 1 / 2 ATR landmarks reuse existing Issue #76 / #78 discovery landmarks rather than introducing a parameter search.

### D. Persistence + Health-Gated Ramp

Use the same age-based cap as candidate B, but an upward step is permitted only when current giveback from the running favorable extreme is < 1 ATR. Once a participation level is earned, the participation ramp itself does not reduce it; deterioration is handled only by the already-frozen damage-latch layer.

## Combining participation with damage-latch management

For each participation candidate, combine separately with the already-frozen:

- Gentle + Damage Latch
- Balanced + Damage Latch

Actual next-bar target exposure is:

`min(participation_cap, damage_latch_exposure)`

A new favorable close-path extreme may reset the damage latch toward Full, but actual exposure still cannot exceed the currently earned participation cap.

Formal regime loss sets exposure to zero.

## Primary measurements

Per completed known-start Markup / Markdown episode, report:

- direction-aligned harvested move in entry-ATR units;
- terminal giveback;
- maximum favorable excursion (MFE);
- capture ratio on positive-MFE episodes;
- average exposure;
- time below Full exposure;
- exposure turnover;
- participation upgrade count;
- damage-latch de-risk and re-risk counts;
- bars to Full exposure, and share of episodes that never reach Full.

Report equal-market universal summaries for:

- all episodes;
- failed / small episodes with MFE < 4 ATR;
- MFE >= 4 ATR;
- MFE >= 8 ATR.

## Questions

1. Does a participation ramp reduce damage from short-lived false trend labels versus Full-at-entry?
2. How much large-trend capture is sacrificed while exposure is still being earned?
3. Does persistence alone work, or does requiring price / health proof improve the frontier?
4. Can one universal ramp behave acceptably across heterogeneous markets without asset-specific tuning?
5. Does combining participation with damage-latch management reduce total whipsaw, or merely move cost from exit to delayed entry?

## Guardrails

- no search over arbitrary day counts, ATR milestones or exposure percentages;
- no separate Markup / Markdown optimization;
- no market-specific rules;
- no ranking by one scalar objective such as Sharpe or PnL;
- no classifier retuning;
- no choosing a candidate as production policy from this discovery sample;
- any surviving candidate must be frozen before new-market / weekly / prospective validation.

Refs #78, #80 and #76.
