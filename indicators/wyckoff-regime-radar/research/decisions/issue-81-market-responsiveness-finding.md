# Issue #81 — Market Responsiveness finding

Date: 2026-09-16

## Executive conclusion

The discretionary idea that a live trend can `feel right` is not purely a synonym for `it has already moved in my favor`, but most intuitive path descriptors do become substantially redundant once cumulative progress is controlled.

Two properties survive best:

1. **Directional path efficiency** — the market reaches its directional progress with less wasted back-and-forth path.
2. **Repeated favorable frontier extension** — the path repeatedly ends at new favorable cumulative close-path extremes rather than relying on one isolated jump.

The strongest interpretation is therefore:

> A trend that is `responding correctly` is not merely profitable early. Conditional on similar early directional progress, it tends to travel more efficiently and to keep extending the favorable frontier.

This remains a diagnostic finding. It does not authorize a production Responsiveness / Trend Quality composite or a classifier change.

## Data gate

The exact accepted Issue #76 nine-market daily sample was supplied again and reproduced the frozen sample counts:

- accepted event rows: **68,118**;
- completed known-start formal trend episodes: **1,624**;
- Large (`MFE >= 8 entry ATR`): **308**;
- Failed (`MFE < 4 entry ATR`): **1,058**;
- Middle (`4 <= MFE < 8`): **258**.

This exactly matches the prior Issue #78 Big-vs-Failed study. No relabeling or classifier change was made.

## Baseline: cumulative directional progress

The previous finding is reproduced:

- E5 cumulative progress AUC: **0.776**, 9/9 markets > 0.50;
- E10 cumulative progress AUC: **0.842**, 9/9 markets > 0.50.

2015–2019 remains separable:

- E5: **0.767**, 4/4 eligible markets;
- E10: **0.905**, 4/4.

This remains the strongest single early proof variable, but it is the control variable for the incremental path-quality test.

## Strong survivor 1 — directional path efficiency

Unconditional separation is strong and broad:

- E5 AUC: **0.755**, 9/9 markets > 0.50;
- E10 AUC: **0.815**, 9/9.

The quintiles are well ordered. Equal-market Large share rises:

- E5: **6.3% -> 36.6%** from Q1 to Q5;
- E10: **5.2% -> 45.3%**.

Failed share falls:

- E5: **86.6% -> 38.6%**;
- E10: **88.3% -> 21.3%**.

Direction diagnostics survive both sides:

- E5 Markup **0.770**, Markdown **0.758**;
- E10 Markup **0.844**, Markdown **0.807**.

2015–2019 separation also remains strong:

- E5 **0.747**, 4/4;
- E10 **0.858**, 4/4.

Most importantly, this feature retains information after controlling for cumulative directional progress with preregistered within-market terciles:

- E5 conditional AUC: **0.649**, 8/8 eligible markets > 0.50;
- E10 conditional AUC: **0.641**, 6/7.

### Decision

**STRONG SURVIVOR.**

This is the cleanest evidence that `how` price travels contains information beyond `how far` it has already traveled.

## Strong secondary survivor — new favorable extreme rate

Unconditional separation is also broad:

- E5 AUC: **0.710**, 9/9;
- E10 AUC: **0.759**, 9/9.

Quintiles are reasonably ordered. Large share rises from:

- E5 **8.9% -> 34.2%**;
- E10 **8.4% -> 38.9%**.

Failed share falls from:

- E5 **83.7% -> 38.2%**;
- E10 **84.2% -> 29.4%**.

Direction diagnostics survive Markup and Markdown:

- E5 Markup **0.733**, Markdown **0.698**;
- E10 Markup **0.789**, Markdown **0.745**.

2015–2019 separation remains useful:

- E5 **0.686**, 4/4;
- E10 **0.733**, 3/4.

Incremental conditional evidence remains positive but weaker than path efficiency:

- E5 conditional AUC **0.586**, 7/8 markets > 0.50;
- E10 **0.578**, 6/7.

### Decision

**STRONG / SECONDARY SURVIVOR.**

Repeated favorable extension appears to describe a real path property rather than merely restating total progress, but its incremental effect is materially smaller than directional path efficiency.

## Weak survivor — early activity expansion

Unconditional separation is modest:

- E5 AUC **0.593**;
- E10 **0.652**.

Conditional evidence is interesting:

- E5 conditional AUC **0.586**, 6/7 eligible markets;
- E10 **0.591**, 5/5.

The E10 quintiles are reasonably ordered, but E5 is not cleanly monotonic. Coverage is lower because a contiguous 20-bar pre-entry activity baseline is required. In the 2015–2019 stress slice only two markets meet the minimum sample condition, so temporal validation is too sparse.

### Decision

**WEAK-BUT-INTERESTING SURVIVOR.**

Activity expansion may contain independent information, but current coverage is insufficient to promote it into a separate production component.

## Weak survivors — adverse pain, favorable-day share, and time-to-proof

### Maximum adverse excursion from entry

Unconditional:

- E5 **0.712**;
- E10 **0.724**;
- 9/9 markets > 0.50 at both horizons.

But after controlling for cumulative progress:

- E5 conditional AUC **0.571**, 7/8;
- E10 **0.500**, 3/7.

Interpretation: large trends do tend to hurt less early, but by E10 this is essentially explained by how far the trend has already traveled.

**Decision: WEAK SURVIVOR.**

### Favorable-day share

Unconditional:

- E5 **0.683**;
- E10 **0.697**.

Conditional:

- E5 **0.558**, 8/8;
- E10 **0.482**, 3/7.

Winning more individual days is descriptively associated with better trends, but adds little independent information by E10.

**Decision: WEAK SURVIVOR.**

### Time to first +0.5 ATR

Unconditional:

- E5 **0.685**;
- E10 **0.672**.

Conditional:

- E5 **0.574**, 7/8;
- E10 **0.540**, 5/7.

Fast proof is useful descriptively, but much of it is mechanically related to cumulative progress.

**Decision: WEAK SURVIVOR.**

## Reject — maximum intra-window pullback

Unconditional separation exists:

- E5 AUC **0.652**;
- E10 **0.605**.

However the preregistered incremental test fails:

- E5 conditional AUC **0.498**, only 3/8 markets > 0.50;
- E10 conditional AUC **0.415**, 0/7.

Thus `small pullback` is not a credible independent responsiveness dimension once the amount of cumulative progress is held roughly constant.

### Decision

**REJECT as a separate component.**

Do not rescue it by changing windows or thresholds.

## What this says about discretionary `盤感`

The results do not support a mystical interpretation. They support a narrower and testable one.

A trader who says `this market is right` may be recognizing two related but distinguishable properties:

- **distance:** the position begins making money in the intended direction;
- **quality of travel:** for a similar amount of directional progress, price wastes less movement fighting itself and repeatedly extends the favorable frontier.

Several other intuitive sensations — `it does not pull back much`, `it wins more days`, `it reached +0.5 ATR quickly` — are real descriptively but are largely consequences or alternate views of that progress rather than separate information sources.

So the best current decomposition is:

> **Market Responsiveness = early directional progress + path efficiency + repeated favorable extension.**

This is a research decomposition, not yet a production formula or weighted score.

## Temporal caveat

2015–2019 remains an important stress slice. Unconditional path-efficiency and new-high-rate separation survive inside the eligible 2015–2019 sample. The stricter cumulative-band conditional test becomes too sparse by era under the preregistered minimum-count rules, so it must remain an all-years primary diagnostic. We do not relax those minimums after seeing results.

## Research decision

Issue #81 succeeds at identifying a small set of interpretable responsiveness dimensions, but does **not** authorize a production composite.

The next valid experiment, if pursued, should be separately preregistered and economic rather than classificatory: compare the existing probe / Persistence + Gentle architecture against proof-based exposure upgrades using only the surviving causal information. The first candidate pair should be cumulative progress plus directional path efficiency; new-high rate can be tested as a secondary incremental component. No optimized weights or thresholds should be selected from Issue #81 outcomes.

Refs #81 #78 #76 #68.
