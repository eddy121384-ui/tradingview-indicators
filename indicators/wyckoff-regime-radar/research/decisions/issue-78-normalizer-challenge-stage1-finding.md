# Issue #78 — Normalizer Challenge Stage 1 Finding

## Scope

This finding executes the frozen preregistration in
`issue-78-normalizer-challenge-stage1-preregistration.md`.

The question was deliberately narrower than a trading-policy test:

> **When the same directional price progress is measured with entry ATR, pre-entry realized sigma, or a robust pre-entry move scale, do we learn essentially the same thing about future trend continuation?**

The numerator is identical for all three candidates. Only the entry-fixed denominator changes.

No lookback, statistic, checkpoint, outcome, or market-specific parameter was changed after results were inspected.

## Sample / eligibility

Accepted base sample remains:

- 68,118 Issue #76 event rows;
- 1,624 completed known-start Markup / Markdown episodes;
- 9 daily markets.

The two challenger normalizers require 20 consecutive strictly pre-entry one-bar moves.

Therefore:

- 1,341 episodes have all three valid entry-fixed normalizers;
- 1,233 episodes are eligible at the 5-move checkpoint;
- 1,024 episodes are eligible at the 10-move checkpoint;
- 283 early-history episodes are excluded because a full consecutive 20-move pre-entry window is unavailable;
- no eligible episode was lost because of a zero / invalid scale.

## Result 1 — The scale-free information content is almost unchanged

Primary outcomes are independent of ATR / sigma / range magnitude.

### 5 completed moves

Equal-market AUC:

| Outcome | Entry ATR | Sigma20 | MedianAbs20 |
|---|---:|---:|---:|
| Later new favorable extreme | 0.7470 | **0.7500** | 0.7480 |
| Positive future net move | 0.4945 | 0.4979 | 0.4966 |
| Remaining life >=20 moves | **0.7274** | 0.7253 | 0.7231 |

### 10 completed moves

| Outcome | Entry ATR | Sigma20 | MedianAbs20 |
|---|---:|---:|---:|
| Later new favorable extreme | 0.7706 | **0.7708** | 0.7679 |
| Positive future net move | **0.5454** | 0.5439 | 0.5433 |
| Remaining life >=20 moves | **0.7636** | 0.7627 | 0.7597 |

The differences are tiny.

No challenger creates a materially new separation frontier.

The one weak outcome is future net sign at five moves: all three normalizers are near random. That weakness therefore belongs to the **information set / outcome**, not to ATR specifically.

## Result 2 — Cross-market paired differences are economically trivial

Against entry ATR:

### Sigma20

At 5 moves:

- favorable-extension AUC: mean delta **+0.00295**, better in 7/9 markets;
- positive-future-net AUC: +0.00342, better in 5/9;
- remaining-life>=20 AUC: -0.00210, better in 3/9.

At 10 moves:

- favorable-extension AUC: +0.00026, better in 5/9;
- positive-future-net AUC: -0.00145, better in 3/9;
- remaining-life>=20 AUC: -0.00084, better in 4/9.

This is not a robust challenger advantage.

MedianAbs20 is similarly mixed and generally a few thousandths below ATR on the primary AUCs.

## Result 3 — Changing the denominator barely changes episode ordering

Equal-market ranking similarity:

### ATR vs Sigma20

- 5 moves: Spearman **0.987**, same quintile **84.8%**, within one quintile **100%**;
- 10 moves: Spearman **0.984**, same quintile **83.3%**, within one quintile **100%**.

### ATR vs MedianAbs20

- 5 moves: Spearman **0.983**, same quintile **82.6%**, within one quintile **100%**;
- 10 moves: Spearman **0.980**, same quintile **83.5%**, within one quintile **100%**.

So the three denominators almost always identify the same episodes as relatively weak / strong progress.

This is the clearest evidence that the earlier signal is mainly **directional progress**, not a special property of ATR.

## Result 4 — Quintile gradients survive the normalizer swap

At 10 moves, Q5 minus Q1 equal-market differences are:

### Later favorable extension probability

- ATR: **+61.7 percentage points**
- Sigma20: **+62.3 pp**
- MedianAbs20: **+59.9 pp**

### Remaining-life >=20 probability

- ATR: **+60.4 pp**
- Sigma20: **+61.9 pp**
- MedianAbs20: **+59.7 pp**

### Mean remaining formal-regime life

- ATR: **+30.2 moves**
- Sigma20: **+30.0**
- MedianAbs20: **+30.0**

The ordered continuation gradient is therefore not an ATR artifact.

At five moves, the same broad pattern holds for favorable extension and remaining life, while future-net sign remains weak for all three.

## Result 5 — 2015–2019 does not reveal a hidden challenger

Primary AUCs remain broadly similar in the stress era.

At 10 moves in 2015–2019:

### Favorable extension

- ATR: 0.7534
- Sigma20: 0.7572
- MedianAbs20: 0.7491

### Remaining-life >=20

- ATR: 0.7313
- Sigma20: 0.7295
- MedianAbs20: 0.7271

No challenger fixes a temporal weakness that ATR uniquely creates.

Some quintile Q5-v-Q1 magnitudes move around more in smaller era cells, but the primary rank-based AUC ordering remains close.

## Result 6 — No direction-specific normalizer is justified

Markup and Markdown show the same broad result.

For example, at 10 moves:

### Favorable-extension AUC

Markdown:
- ATR 0.7552
- Sigma20 0.7540
- MedianAbs20 0.7499

Markup:
- ATR 0.7918
- Sigma20 0.7919
- MedianAbs20 0.7898

### Remaining-life >=20 AUC

Markdown:
- ATR 0.7391
- Sigma20 0.7339
- MedianAbs20 0.7319

Markup:
- ATR 0.7938
- Sigma20 0.7976
- MedianAbs20 0.7946

No long / short-specific scale is supported.

## Secondary legacy bridge — ATR-defined Large vs Failed

Because the old label itself is ATR-defined, this is explicitly secondary.

Equal-market Large-vs-Failed AUC:

5 moves:
- ATR 0.7642
- Sigma20 0.7605
- MedianAbs20 0.7556

10 moves:
- ATR 0.8362
- Sigma20 0.8278
- MedianAbs20 0.8225

ATR is modestly strongest on its own ATR-defined label, which is unsurprising and is exactly why this outcome was not allowed to decide the challenge.

## Research decision

### Main conclusion

> **Directional progress is the information-bearing feature. Entry ATR is mainly a practical normalization choice, not the apparent source of the continuation signal.**

The core Issue #78 progress finding survives two conceptually different pre-entry scale estimators.

### Normalizer decision

Do **not** promote Sigma20 or MedianAbs20 into Stage 2 matched-confirmation-cost policy testing.

Reason:

- neither challenger materially improves scale-free continuation separation;
- differences are only a few AUC thousandths;
- episode rankings are almost identical;
- no temporal or directional robustness advantage emerges.

Therefore entry ATR remains the preferred frozen normalizer for the current architecture because it is:

- already integrated;
- fixed and causal;
- cross-market interpretable;
- simpler than adding a 20-move estimator;
- not empirically dominated by either challenger.

This is a simplicity decision, not a claim that ATR is theoretically optimal.

## What this changes

The earlier Issue #78 findings should now be worded more generally:

Not:

> "+1 ATR contains unique predictive information."

Better:

> **"Sufficiently strong direction-aligned price progress contains continuation information; entry ATR is one convenient way to express that progress across markets."**

The exact +0.5 / +1 / +2 ATR landmarks remain architecture-specific engineering landmarks, not universal constants of market behavior.

## Next research gate

Because no alternative normalizer materially beats ATR, the preregistered Stage-2 economic normalizer contest is **not triggered**.

The next non-redundant research question is therefore the **Proof-Basis Challenge**:

> **Holding the regime and normalization framework fixed, does price structure / breakout evidence add or outperform raw directional progress as the reason to increase risk?**

Do not search additional volatility normalizers or lookbacks on this discovery sample.

Refs #78, #80, #76.
