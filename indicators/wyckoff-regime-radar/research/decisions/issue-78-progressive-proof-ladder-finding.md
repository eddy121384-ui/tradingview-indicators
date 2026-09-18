# Issue #78 — Progressive Proof Ladder vs One-Step Confirmation Finding

## Scope

This finding executes the frozen preregistration in `issue-78-progressive-proof-ladder-preregistration.md`.

Primary comparison isolates the add-risk layer only:

- Full-at-entry;
- 25% probe -> Full at +0.5 ATR;
- 25% probe -> Full at +1 ATR;
- 25% probe -> Full at +2 ATR;
- progressive ladder: 25% -> 50% at +0.5 -> 75% at +1 -> 100% at +2 ATR.

All exposure changes apply to the next completed move. No damage-latch layer is active in this comparison.

Accepted sample remains 68,118 event rows and 1,624 completed known-start episodes across nine daily markets.

## Result 1 — The ladder is a real frontier point, not a free lunch

Failed/small MFE <4 ATR equal-market mean harvest:

- Full-at-entry: **-2.249 ATR**
- +0.5 one-step: **-1.769**
- +1 one-step: **-1.645**
- +2 one-step: **-1.325**
- Progressive ladder: **-1.579**

Relative to Full-at-entry, the ladder reduces failed/small-trend damage by about **29.8%**.

Large MFE >=8 ATR equal-market mean harvest:

- Full-at-entry: **+10.725 ATR**
- +0.5 one-step: **+9.527**
- +1 one-step: **+9.183**
- +2 one-step: **+8.457**
- Progressive ladder: **+9.056**

The ladder retains about **84.4%** of Full-at-entry large-trend harvest.

Thus the ladder lands between the +1 and +2 one-step policies: more protection than +1, more participation than +2.

## Result 2 — Cross-market behavior is exceptionally clean

Relative to the +1 ATR one-step policy:

- the ladder improves failed/small-trend harvest in **8/9 markets**;
- the ladder reduces large-trend harvest in **9/9 markets**.

Relative to the +2 ATR one-step policy:

- the ladder has weaker failed/small-trend protection in **9/9 markets**;
- the ladder preserves more large-trend harvest in **9/9 markets**.

Relative to the +0.5 ATR one-step policy:

- the ladder improves failed/small-trend harvest in **9/9 markets**;
- the ladder reduces large-trend harvest in **9/9 markets**.

The ladder therefore genuinely smooths the protection / participation frontier; its position is not driven by one market.

## Result 3 — The incremental benefit versus +1 ATR is modest

The closest simple benchmark is the +1 ATR one-step policy.

Versus +1 ATR:

- failed/small harvest improves by only about **+0.066 ATR per episode** on an equal-market basis;
- large-trend harvest falls by about **-0.127 ATR**;
- all-episode equal-market mean harvest is essentially unchanged: **+0.444 ATR ladder vs +0.441 ATR +1 one-step**;
- average exposure is slightly lower: **62.9% vs 64.1%**.

Operationally, however, the ladder produces more resize actions:

- all-episode mean participation increase count: **1.41 ladder vs 0.63 +1 one-step**.

Gross turnover is similar because the ladder splits approximately the same total exposure change into more pieces.

Interpretation: the ladder buys a smoother exposure path, not a large new economic edge.

## Result 4 — Temporal evidence does not create a hidden winner

Equal-market all-episode harvest:

### 2010–2014

- Full: +1.481
- +0.5: +1.487
- +1: +1.452
- +2: +1.344
- Ladder: +1.428 ATR

### 2015–2019

- Full: -0.101
- +0.5: -0.066
- +1: -0.043
- +2: -0.047
- Ladder: -0.052 ATR

### 2020–2026

- Full: +0.170
- +0.5: +0.147
- +1: +0.087
- +2: +0.053
- Ladder: +0.096 ATR

The ladder does not repair the previously documented 2015–2019 weakness. No stable-alpha claim is allowed.

## Result 5 — Direction diagnostics do not justify separate rules

All-episode equal-market harvest:

- Markup: Full +0.024, +1 one-step +0.042, ladder +0.034 ATR.
- Markdown: Full +0.985, +1 one-step +0.808, ladder +0.820 ATR.

Direction differences remain descriptive only. No separate long / short ladder is justified.

## Research decision

The progressive ladder **passes as a valid Pareto-frontier architecture**, but it does **not** dominate the simpler +1 ATR one-step policy.

The evidence supports two interpretations:

1. **If implementation simplicity is the priority**, the +1 ATR one-step policy captures almost the same all-episode gross result with fewer resize decisions.
2. **If smoother exposure acquisition is a product goal**, the 25/50/75/100 ladder is justified: it spreads confirmation tax across the already-frozen proof landmarks and occupies a stable cross-market point between +1 and +2 one-step confirmation.

Do not claim the ladder is economically superior from this in-sample discovery pass.

For subsequent de-risk research, preserve **both** as frozen add-risk benchmarks:

- simple benchmark: 25% -> 100% at +1 ATR;
- progressive benchmark: 25% -> 50% -> 75% -> 100% at +0.5 / +1 / +2 ATR.

This avoids prematurely selecting complexity while allowing the de-risk layer to reveal whether a smoother earned-exposure state interacts materially better with deterioration management.

Refs #78, #80, #76.
