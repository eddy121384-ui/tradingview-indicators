# Issue #78 — Progressive Proof Ladder vs One-Step Confirmation Preregistration

## Purpose

The Confirmation Tax study established a smooth protection-versus-participation frontier across the frozen +0.5 / +1 / +2 entry-ATR proof levels. It did not identify a magic universal cutoff.

The next question is:

> **Does spreading confirmation tax across a fixed progressive exposure ladder produce a better participation frontier than waiting for one binary proof threshold and then jumping directly to Full exposure?**

This study isolates the add-risk architecture only. No damage-latch / de-risk overlay is active in the primary comparison.

## Frozen sample

Reuse the accepted Issue #76 nine-market daily sample:

- 68,118 accepted event rows;
- 1,624 completed known-start Markup / Markdown episodes;
- same entry-ATR normalization;
- same formal-regime boundaries;
- no classifier changes.

## Frozen causal policies

All decisions use only information observed through the current completed daily move and change exposure for the **next** move.

### A. Full-at-entry baseline

- 100% from fresh formal Markup / Markdown entry until formal regime loss.

### B. One-step +0.5 ATR proof

- 25% until cumulative favorable excursion from episode entry first reaches +0.5 entry ATR;
- 100% thereafter.

### C. One-step +1.0 ATR proof

- 25% until cumulative favorable excursion first reaches +1.0 entry ATR;
- 100% thereafter.

### D. One-step +2.0 ATR proof

- 25% until cumulative favorable excursion first reaches +2.0 entry ATR;
- 100% thereafter.

### E. Progressive proof ladder

- 25% before +0.5 ATR proof;
- 50% after +0.5 ATR proof;
- 75% after +1.0 ATR proof;
- 100% after +2.0 ATR proof.

Once a proof level is earned it is not revoked by the participation layer. Formal regime loss sets exposure to zero.

The ladder is identical in spirit to the already-preregistered Issue #78 Excursion-Proof participation architecture. This pass differs by isolating participation from the damage-latch layer and comparing directly against the newly measured one-step confirmation policies.

## Primary evaluation slices

Report equal-market results for:

- all completed episodes;
- failed / small episodes with final MFE <4 ATR;
- middle episodes with final MFE 4–8 ATR;
- large episodes with final MFE >=8 ATR.

Final MFE is evaluation-only and never used in live policy decisions.

## Primary measurements

Per policy report:

- direction-aligned harvested move in entry-ATR units;
- harvest difference versus Full-at-entry;
- large-trend harvest retention versus Full-at-entry;
- failed/small-episode damage reduction versus Full-at-entry;
- average exposure;
- fraction of episode spent below Full exposure;
- exposure-increase count;
- total exposure turnover including final flattening.

Also report:

- 9-market equal-market summary;
- per-market direction;
- Markup / Markdown diagnostic split;
- temporal slices 2010–2014, 2015–2019, 2020–2026.

## Primary research question

The progressive ladder is interesting only if it occupies a useful point on the frontier:

- materially better failed/small-trend protection than early one-step confirmation;
- materially better large-trend participation than late one-step confirmation;
- behavior is broad across markets and directions;
- no obvious dependence on one temporal era.

This study does not require the ladder to beat every one-step policy on every metric. That would be structurally impossible because the policies intentionally trade protection for participation.

The question is whether the ladder **smooths the frontier** in a practically useful way.

## Guardrails

- no new ATR thresholds;
- no alternative exposure percentages;
- no search over 33/66, 20/40/70, or other ladders;
- no time-to-proof gate;
- no directional-efficiency gate;
- no market-specific rules;
- no separate Markup / Markdown ladder;
- no damage-latch tuning in the primary comparison;
- no choosing a winner from one scalar PnL or Sharpe statistic;
- no classifier retuning;
- all results remain in-sample discovery evidence.

## Intended decision

If the ladder shows a robust compromise between false-start protection and large-trend participation, preserve it as the leading simple add-risk architecture and move the research frontier to the de-risk side.

If it does not add a useful frontier point, retain the simpler one-step proof family and do not add unnecessary exposure states.

Refs #78, #80, #76.
