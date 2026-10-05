# Issue #78 — Classifier Methodology Audit preregistration

Date: 2026-10-03

## Why this audit exists

The project began as a six-regime market-state classifier:

- Accumulation
- Markup
- Re-accumulation
- Distribution
- Markdown
- Re-distribution

Later Issue #78 work increasingly studied exposure management after a fresh Markup / Markdown label. OOS2/OOS3 showed that stock-level policy economics are weak even though some downstream evidence families remain informative.

Before adding another filter, this audit returns to the more basic question:

> **Does the current classifier architecture itself represent six distinct and economically meaningful market states, or has the implementation become a winner-take-all scoring system whose hard labels discard useful continuous information?**

This is a methodology diagnostic. It does not change the classifier and it does not authorize a new trading policy.

---

## Frozen cohort and data

Reuse the already-frozen OOS3 equity cohort and recovered exact FIGI membership:

- 300 stocks;
- FIGI-set SHA-256:
  `017e9360402afa002dc0970088649e7c411c4f02333dec550f2432be3c0dd701`;
- Bloomberg history through 2026-08-31;
- same price / liquidity eligibility used in OOS2/OOS3;
- same frozen classifier blob:
  `1eec08e791403453853b589373bb2270c508c3bb`.

No security may be replaced.

The cohort is already outcome-inspected. All forward-return work here is descriptive / diagnostic, not fresh OOS validation.

---

## Static architecture under audit

The current implementation has four distinct layers:

1. **Raw stage evidence**
   - six smoothed raw scores;
2. **Stage gates and effective evidence**
   - each raw score is multiplied by stage-specific gates / bounded witness multipliers;
3. **Relative competition**
   - six effective scores are sharpened and normalized into six probabilities;
   - one top stage and one runner-up are selected;
4. **Hard state logic**
   - dominant weight, gap, evidence and conflict rules determine strong/weak candidates;
   - confirmation and state inertia produce the final formal regime.

This audit treats these as separate transformations. It must not assume the final formal label is automatically the most informative layer.

---

## Frozen raw formula map

The existing source conceptually mixes several dimensions inside each stage score.

### Accumulation

Uses:

- prior bearish maturity trace;
- range score;
- downside exhaustion;
- support holding;
- quiet-range context.

### Markup

Uses:

- breakout evidence;
- positive heat;
- bullish structure;
- bullish extension;
- bullish continuation;
- prior Accumulation trace.

### Re-accumulation

Uses:

- bullish background;
- range score;
- support holding;
- absence of opposite panic;
- absence of upside exhaustion.

### Distribution

Uses:

- prior bullish maturity trace;
- range score;
- upside exhaustion;
- resistance holding;
- quiet-range context.

### Markdown

Uses:

- breakdown evidence;
- downside panic;
- bearish structure;
- bearish extension;
- bearish continuation;
- prior Distribution trace.

### Re-distribution

Uses:

- bearish background;
- range score;
- resistance holding;
- absence of opposite heat;
- absence of downside exhaustion.

This map is frozen before the audit results. The audit asks whether these six mixtures behave as six separable states.

---

## Diagnostic A — where do stages disappear?

For every eligible daily bar report, by named stage:

- raw-score winner count / share;
- effective-probability winner count / share;
- strong-candidate count / share;
- formal-label count / share.

Special question:

> Do Re-accumulation and Re-distribution already fail at the raw-score layer, or are they removed later by gates, relative competition, confirmation, or inertia?

Also report the top-two winner pair frequencies and top-gap distribution.

No threshold changes are allowed from this diagnostic.

## Aggregation / adequacy

Primary summaries are one-stock-one-vote.

For any stock × diagnostic cell × horizon:

- require at least **5 eligible bars** before that stock contributes a cell-level estimate;
- report the number of contributing stocks and bars;
- treat aggregate cells with fewer than **30 contributing stocks** as underpowered / descriptive only.

The 5-bar / 30-stock adequacy rules are frozen before results.

---

## Diagnostic B — raw-score redundancy / separability

For the six raw stage scores:

- calculate within-stock Spearman pair correlations;
- aggregate correlations one-stock-one-vote;
- report the most strongly positive pairs and most strongly negative pairs;
- report how often the two highest raw scores come from conceptually neighboring states.

This asks whether six labels correspond to six distinguishable evidence patterns or whether several stage formulas are largely redundant mixtures of the same underlying dimensions.

No clustering algorithm or optimized number of states is allowed in this pass.

---

## Diagnostic C — continuous evidence versus hard labels

Frozen forward horizons:

- 1 bar
- 5 bars
- 10 bars
- 20 bars

Forward move:

`(log_close[t+h] - log_close[t]) / entry_symATR[t]`

For Markup and Markdown separately, compare these predeclared layers:

1. top within-stock quintile of the **raw stage score**;
2. top within-stock quintile of the **normalized stage probability**;
3. stage is the **effective winner**;
4. stage is a **strong candidate**;
5. stage is the **formal label**;
6. formal label has already survived **>=10 bars**.

For Markup, favorable direction is positive.
For Markdown, favorable direction is negative.

Report one-stock-one-vote:

- aligned mean forward move;
- aligned median forward move;
- aligned hit rate;
- stock count.

Primary methodological question:

> Does the hard-label pipeline improve directional information, preserve it, or discard information already present in the continuous raw evidence?

There is no pass/fail threshold and no layer is selected for production from this cohort.

---

## Diagnostic D — all six formal labels

For every formal regime and each frozen horizon report:

- equal-stock mean forward move;
- median forward move;
- positive-move fraction;
- mean absolute forward move;
- stock count / bar count.

Do not direction-align Accumulation, Re-accumulation, Distribution or Re-distribution in the primary table. Their empirical forward sign must be observed rather than imposed.

Also report fresh-label and regime-age summaries where sample size permits:

- fresh / age 0–4;
- age 5–9;
- age 10–19;
- age 20+.

This re-tests the original regime-lifecycle premise without embedding a trading strategy.

---

## Diagnostic E — three-family collapse

Before seeing results, freeze a simple non-optimized collapse of the existing six normalized probabilities:

- **Up family** = Markup + Re-accumulation probability;
- **Transition family** = Accumulation + Distribution probability;
- **Down family** = Markdown + Re-distribution probability.

The family with the highest summed probability is the family winner.

Report:

- winner occupancy;
- Up-family direction-aligned forward outcomes;
- Down-family direction-aligned forward outcomes;
- Transition-family signed and absolute forward outcomes.

This is not a replacement classifier. It asks whether the six-way competition is adding information beyond a simpler directional family representation.

Do not change family definitions after results.

---

## Diagnostic F — hard-state inertia audit

For each formal Markup / Markdown bar report:

- whether the effective winner still agrees with the formal label;
- whether the current bar is strong-candidate support, weak-candidate pressure, coexistence, chaos, or stale persistence;
- formal regime age;
- forward outcomes by agreement / disagreement state.

This asks whether state inertia improves persistence or merely keeps stale labels alive after the underlying evidence has moved elsewhere.

No alternative confirmation or stale-decay setting may be tested here.

---

## Interpretation rules

Possible conclusions include:

### Raw evidence useful, hard labels weaker

Interpret as an architecture / discretization problem. Candidate next work may separate:

- direction;
- expansion versus range;
- lifecycle maturity;
- deterioration / supply-demand pressure.

Do not immediately retune thresholds.

### Raw evidence and hard labels both useful

Keep six-stage semantics provisionally and locate the problem in exposure translation / lifecycle management.

### Raw evidence itself weak

The underlying stage formulas require a more fundamental redesign before further sizing-policy research.

### Re-accumulation / Re-distribution absent only after gating

Treat this as a state-competition / admission problem, not proof that those concepts do not exist.

### Re-accumulation / Re-distribution absent already in raw evidence

Treat the six-stage formulation itself as structurally suspect.

---

## Guardrails

After results are inspected, do not:

- change any stage weight;
- change any gate;
- change regime gamma;
- change dominant / gap / evidence thresholds;
- change confirmation bars;
- change stale-state decay;
- delete a stage;
- merge stages;
- select a new three-state classifier;
- add a new strategy policy.

Any model redesign must be a separate preregistered issue / branch and must later face new untouched evidence.

Refs #78, #138, #135, #132, #131, #80.
