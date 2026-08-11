# Issue #57 — Consensus formation / Formal-lag diagnostic preregistration

Status: **FROZEN BEFORE RUNNING THIS DIAGNOSTIC**

This phase follows the user's live-use observation that Candidate + Secondary may be more informative than Formal. It deliberately remains **price-only**. Volume, MTF, Divergence, HMM, and witness stage bias are excluded from this research path.

All seven FX fixtures currently available to this branch are already burned / observed. They may be used only for hypothesis development. No result from this phase is independent OOS validation.

## Fixed stage-direction semantics

Use the original six-stage weights. Action-compatible directional pairs are frozen from the original Pine Flat Action semantics:

- bullish consensus pair: **Markup (2) + Re-accumulation (3)**;
- bearish consensus pair: **Markdown (5) + Redistribution (6)**;
- Accumulation (1), Distribution (4), and no-regime (0) are transition/context for this directional diagnostic.

Candidate and Secondary mean the two largest six-stage normalized weights on the same bar.

## Question A — Does stronger same-direction agreement improve monotonically?

For bars where Candidate and Secondary are an action-compatible pair, measure `Candidate + Secondary` as a continuous consensus-strength variable.

Predeclared strength bins:

- `<70%`
- `70–<80%`
- `80–<90%`
- `90–<95%`
- `>=95%`

At 5 / 10 / 20 / 60 bars, report:

- aligned forward return;
- hit rate;
- aligned MFE / MAE where practical;
- observation count;
- per-pair continuous Spearman relation between consensus strength and aligned forward return.

The purpose is to inspect shape / monotonicity, **not to select the best threshold**. The user's 90% heuristic remains the primary pre-existing live-use reference.

## Question B — Is Top-2 consensus useful specifically when Formal has not caught up?

At the fixed `>=90%` Top-2 consensus condition, classify every signal bar using Formal's action direction:

1. `formal_aligned`: Formal is already 2/3 for bullish consensus or 5/6 for bearish consensus;
2. `formal_transition_or_neutral`: Formal is 0/1/4;
3. `formal_opposite`: Formal is in the opposite action family.

For each category and 5 / 10 / 20 / 60 bars, report aligned return, hit rate, and count.

For categories 2 and 3, also measure whether Formal adopts the Top-2 direction within 5 / 10 / 20 bars and the median adoption lag among adopted cases.

This directly tests the hypothesis that Formal may be a lagged confirmation layer while Candidate + Secondary contain earlier transition information.

## Question C — Does persistence improve the signal?

Keep the threshold fixed at 90%. Compare consensus that has persisted for 1 / 2 / 3 consecutive bars.

To avoid counting every bar of one long episode as an independent new signal, score only the **first bar at which an episode reaches the required streak length**.

At 5 / 10 / 20 / 60 bars report aligned return, hit rate, and event count.

The 1/2/3-bar sweep is engineering sensitivity only. Do not select a persistence rule from PnL alone.

## Engines

Run the exact same diagnostic against:

- frozen v0.5.2.1 price-only Python mirror;
- current Issue #57 v0.6 price-only core.

This distinguishes a genuine weight-formation property from a redesign side effect.

## Interpretation boundary

A useful burned-data result can justify freezing a new hypothesis and obtaining another untouched sample. It cannot validate a production signal.

A weak result does not justify adding Volume/MTF/Divergence back into this phase. The price-only boundary remains fixed unless a later, separately approved research issue changes it.
