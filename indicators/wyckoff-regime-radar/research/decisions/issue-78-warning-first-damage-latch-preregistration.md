# Issue #78 — Warning-First Damage-Latch Policy Preregistration

## Purpose

The post-proof deterioration diagnostic found:

- 0.5–1 ATR giveback is very common and still recovers to a new favorable extreme more often than not;
- 2 ATR is the first frozen giveback level where non-recovery becomes more common than recovery;
- 4 ATR is a severe-damage state, but a material recovery / rebound tail remains;
- giveback reaches comparable deterioration states earlier than pure 10 / 20-move stall signals.

This pass converts that diagnostic into one deliberately simple policy and tests it against already-frozen alternatives.

No result from this policy has been inspected before this preregistration.

## Frozen sample

Reuse the accepted Issue #76 nine-market daily sample:

- 68,118 accepted event rows;
- 1,624 completed known-start Markup / Markdown episodes;
- same entry-ATR normalization;
- same formal-regime boundaries;
- no classifier changes.

## Frozen add-risk benchmarks

Run every management overlay separately on both already-frozen participation architectures.

### A. Simple +1 ATR proof

- 25% from fresh formal trend entry;
- once running favorable close-path excursion reaches +1.0 entry ATR, earned participation becomes 100%;
- earned participation is not revoked by the add-risk layer itself.

### B. Progressive proof ladder

- 25% initially;
- 50% once favorable excursion reaches +0.5 ATR;
- 75% once it reaches +1.0 ATR;
- 100% once it reaches +2.0 ATR;
- earned participation is not revoked by the add-risk layer itself.

All upgrades apply to the next completed move.

## Frozen management overlays

### 1. No de-risk

Actual exposure = earned participation cap until formal regime loss.

### 2. Gentle + damage latch

Reuse the existing frozen Issue #78 Gentle ladder:

- giveback <0.5 ATR -> damage cap 100%;
- 0.5–1 -> 100%;
- 1–2 -> 75%;
- 2–4 -> 50%;
- 4+ -> 25%.

Actual exposure is the minimum of earned participation and latched damage cap.

Re-risk only after a new favorable close-path extreme; then reset damage cap to 100%.

### 3. Balanced + damage latch

Reuse the existing frozen Issue #78 Balanced ladder:

- giveback <0.5 -> 100%;
- 0.5–1 -> 75%;
- 1–2 -> 50%;
- 2–4 -> 25%;
- 4+ -> 0%.

Same new-extreme recovery latch.

### 4. Warning-First + damage latch — new candidate

Do **not** cut existing earned exposure at 0.5 or 1 ATR giveback.

Use only the two diagnostic severity levels where recovery becomes materially worse:

- giveback <2 ATR -> no damage reduction;
- 2–4 ATR -> reduce earned exposure by one fixed 25-percentage-point participation step;
- 4+ ATR -> reduce earned exposure by two fixed 25-percentage-point steps.

Minimum positive exposure is 25% while the formal trend remains active.

Examples:

- earned 100% -> 75% at 2–4 ATR -> 50% at 4+ ATR;
- earned 75% -> 50% -> 25%;
- earned 50% -> 25% -> 25%.

The reduction is latched. A temporary shrink in giveback does not restore exposure.

A **new favorable close-path extreme** resets the damage reduction to zero for the next move, after which actual exposure again equals the currently earned participation cap.

If damage worsens from 2–4 ATR to 4+ before recovery, the second reduction step applies immediately to the next move.

Formal regime loss sets exposure to zero.

## Why the new candidate is frozen this way

- 2 / 4 ATR are existing Issue #78 giveback landmarks; no new threshold is introduced.
- 25 percentage points is the existing participation-state step; no new exposure size is introduced.
- mild 0.5 / 1 ATR damage remains warning-only because the diagnostic found recovery remains common.
- the recovery latch is reused unchanged from earlier Issue #78 work.

No threshold or step may be altered after results are inspected.

## Primary measurements

Per policy combination report:

- direction-aligned harvested move in entry-ATR units;
- average exposure;
- fraction of episode below earned participation;
- total exposure turnover including initial entry and final flattening;
- de-risk count;
- re-risk count;
- maximum reduction from earned participation;
- harvested move / full formal-hold move where interpretable.

Report equal-market summaries for:

- all completed episodes;
- failed / small MFE <4 ATR;
- middle MFE 4–8 ATR;
- large MFE >=8 ATR.

Also report:

- 9-market per-market direction;
- Markup / Markdown diagnostic split;
- 2010–2014, 2015–2019, 2020–2026.

## Primary research question

Does Warning-First occupy a useful frontier point relative to:

- no de-risk;
- Gentle + latch;
- Balanced + latch?

A useful result would preserve materially more large-trend harvest and/or reduce resize churn than the earlier ladders while still reducing failed-trend damage versus no de-risk.

It need not dominate every alternative on every metric.

## Guardrails

- no new giveback threshold;
- no new exposure step;
- no stall-duration gate in this pass;
- no directional-efficiency gate;
- no market-specific parameters;
- no separate Markup / Markdown policy;
- no classifier retuning;
- no same-bar hindsight action;
- no scalar Sharpe / PnL optimization;
- no production claim from this discovery sample.

## Intended decision

If Warning-First adds a robust Pareto-frontier point, preserve it as the leading simple de-risk candidate alongside the two frozen add-risk architectures.

If it merely reproduces Gentle / Balanced behavior without a meaningful participation or turnover advantage, reject the added policy and keep the older frozen management family.

Refs #78, #80, #76.
