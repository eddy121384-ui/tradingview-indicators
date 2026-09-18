# Issue #78 — Add-Risk Evidence Incrementality Finding

## Scope

This finding executes the frozen Phase-2 preregistration in
`issue-78-add-risk-evidence-incrementality-preregistration.md`.

The question was deliberately narrow:

> Once realized directional progress is known, does directional path efficiency add enough stable incremental information to justify a second dimension in the add-risk rule?

No entry rule, classifier setting, exposure percentage, checkpoint, or threshold was changed after outcomes were inspected.

Accepted sample:

- 9 daily markets from Issue #76;
- 68,118 accepted formal-stage event rows;
- 1,624 completed known-start Markup / Markdown episodes;
- 1,467 episodes eligible after 5 completed moves;
- 1,228 episodes eligible after 10 completed moves.

The 5- and 10-move samples are survival-conditioned by construction and are not treated as the same cohort.

## Result 1 — Both features look strong on a standalone basis

When each feature is ranked within market, both realized progress and directional efficiency show large endpoint separation in forward continuation.

### After 5 completed moves

Progress Q5 versus Q1:

- remaining favorable excursion: **7.78 vs 2.87 ATR**;
- probability of at least +2 ATR additional favorable excursion: **61.4% vs 32.5%**;
- probability of at least +4 ATR additional favorable excursion: **47.2% vs 22.5%**;
- remaining regime life: **46.0 vs 18.3 bars**;
- remaining directional net move: **+1.70 vs +0.27 ATR**.

Efficiency Q5 versus Q1:

- remaining favorable excursion: **6.95 vs 2.96 ATR**;
- +2 ATR continuation: **60.3% vs 29.4%**;
- +4 ATR continuation: **43.0% vs 19.7%**;
- remaining regime life: **44.0 vs 18.8 bars**;
- remaining directional net move: **+1.46 vs +0.38 ATR**.

### After 10 completed moves

Progress Q5 versus Q1:

- remaining favorable excursion: **7.42 vs 3.14 ATR**;
- +2 ATR continuation: **59.0% vs 30.1%**;
- +4 ATR continuation: **42.7% vs 19.3%**;
- remaining regime life: **44.4 vs 17.0 bars**.

Efficiency Q5 versus Q1:

- remaining favorable excursion: **7.01 vs 2.81 ATR**;
- +2 ATR continuation: **60.5% vs 28.5%**;
- +4 ATR continuation: **42.2% vs 18.4%**;
- remaining regime life: **44.7 vs 16.8 bars**.

These standalone gradients are broad across markets and remain visible in the preregistered temporal slices, including 2015–2019.

However, neither feature predicts *lower* remaining adverse excursion. Higher-feature episodes also experience larger absolute remaining adverse excursion, consistent with the fact that they remain alive much longer. The features therefore describe remaining opportunity / regime persistence, not a clean low-pullback state.

## Result 2 — Progress and efficiency are too collinear for the preregistered endpoint conditional contrast

The primary incrementality test requires comparing low versus high efficiency **within similar progress**.

The two features are extremely dependent in this sample:

- Pearson correlation, 5-move checkpoint: **0.864**;
- Pearson correlation, 10-move checkpoint: **0.876**;
- same progress and efficiency quintile: **73.4%** at 5 moves and **75.1%** at 10 moves;
- within one quintile of each other: **99.45%** at 5 moves and **99.35%** at 10 moves.

The 5x5 joint grid is therefore almost diagonal.

As a consequence, the analyzer's preregistered market-level `efficiency Q5 - Q1 within progress quintile` contrast has **no eligible cells with at least three observations on both endpoints**. No conditional-contrast CSV is produced because the frozen contrast is not estimable at the required market-level support.

This is an identification result, not proof that the true incremental effect is exactly zero.

But under the preregistered promotion rule, efficiency must demonstrate stable expected orientation **after controlling for progress**. It does not clear that gate.

## Result 3 — The observable joint grid does not show a clean incremental efficiency gradient

The occupied joint cells also fail to show a reasonably monotonic efficiency ordering at fixed progress.

Examples using equal-market remaining favorable excursion:

At 5 moves:

- progress Q4: efficiency Q3 **4.33**, Q4 **4.45**, Q5 **3.36 ATR**;
- progress Q5: efficiency Q4 **6.02**, Q5 **8.16 ATR**.

At 10 moves:

- progress Q4: efficiency Q3 **9.94**, Q4 **5.81**, Q5 **5.57 ATR**;
- progress Q5: efficiency Q4 **7.09**, Q5 **7.71 ATR**.

Some cells favor higher efficiency and others do not. The sparse off-diagonal cells prevent a robust universal conditional ordering.

The same conclusion is not rescued by Markup / Markdown diagnostics: standalone efficiency gradients exist in both directions, but the study does not identify stable independent efficiency information once realized progress is held similar.

## Temporal interpretation

The 2015–2019 stress era still shows a standalone efficiency gradient. For example, efficiency Q5 versus Q1 has:

- at 5 moves, about **+2.77 ATR** more remaining favorable excursion and **+31.0 percentage points** higher +2 ATR continuation;
- at 10 moves, about **+2.54 ATR** more remaining favorable excursion and **+13.7 percentage points** higher +2 ATR continuation.

That does **not** satisfy the incrementality requirement because the same collinearity / overlap problem remains. A standalone relationship cannot be promoted as an independent sizing input merely because it survives an era slice.

## Research decision

**Do not promote directional path efficiency into a two-dimensional add-risk rule.**

The simpler interpretation survives:

> **Realized directional price progress earns exposure; path efficiency remains descriptive / diagnostic only.**

This is a model-selection decision, not a claim that efficiency contains literally zero information.

The evidence says that, in the current daily nine-market discovery sample, efficiency is so tightly coupled to realized progress that the extra state variable is not justified by independently identified forward information.

The existing price-proof / Excursion-Proof participation architecture therefore remains the cleaner add-risk candidate.

No efficiency threshold, alternative formula, long/short split, market-specific rule, or new checkpoint should be searched in this pass.

## Implication for Issue #78

Phase 1 established that starting smaller reduces false-start damage but delays participation in genuine trends.

Phase 2 now says that the add-risk side should stay **one-dimensional and price-proof driven** rather than adding an efficiency gate.

The next research question is Phase 3:

> **Once exposure has been earned, what causal deterioration should stop further adds or trigger reduction without turning normal trend pullbacks into repeated whipsaw?**

That phase should be separately preregistered before any new damage threshold is inspected.

Refs #78, #80 and #76.
