# Issue #57 — Retake severity × duration behavior map

Status: preregistered reused-data structural diagnostic only.

This study does not change the v0.6 indicator and does not select a production threshold.

## Event population

Start from post-handoff seizure events where the carried new stage initially leads the old context stage, then keep only events with a pre-resolution old-context retake as already defined in `diagnose_post_handoff_hold_persistence.py`.

## Predictor definitions fixed before reading outcomes

At the first retake bar:

- `normalized_first_retake_margin = (context - carried) / (context + carried)` when the denominator is positive.
- `first_control_spell_bars` = consecutive bars from the first retake while `context >= carried`, stopping before the original watch resolves or carried regains the lead.
- `max_normalized_retake_margin` = maximum normalized retake margin during that first control spell.
- `dominance_area` = sum of positive normalized retake margins during that first control spell.

## Outcome

Use the already-frozen bridge-watch resolution within 20 bars:

- same-direction actionable completion;
- opposite-direction actionable failure;
- timeout.

## Analysis

Primary evidence is continuous/pair-aware:

- per-pair Spearman association of each retake-severity metric with same-direction completion (binary 0/1);
- pair median of those correlations;
- same associations with opposite-actionable failure.

Descriptive grouping is fixed before outcomes are read:

- first-control duration: `1 bar`, `2–3 bars`, `4+ bars`;
- severity: within-pair predictor-only terciles (`low`, `mid`, `high`) based solely on normalized first-retake margin. These are descriptive ranks, not production thresholds.

Also report a 3×3 severity-tercile × duration-bin matrix where sample size permits.

## Interpretation boundary

This is repeated exploration on already-used FX fixtures. It may describe transition damage but cannot establish an independent trading rule or OOS edge. No threshold is to be selected from these results.
