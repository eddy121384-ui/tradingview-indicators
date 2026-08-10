# Issue #57 — Phase D decision

Decision: **phase_d_remove_confidence_claim_use_descriptive_regime_strength**

Phase D rejects the word **confidence** for the v0.6 price-only regime layer.

The four-state canonical weights contain useful information about **classification persistence**, but the tested strength measures do not reliably calibrate future Markup/Markdown directional outcomes. They therefore must not be presented as probabilities or predictive confidence.

## Frozen naming / semantics

### Primary descriptive field — Regime Margin

Use the existing `canonical_formal_margin` calculation:

> current canonical Formal weight minus the strongest competing canonical weight.

Interpretation:

- large positive value: the confirmed Formal regime has a clear weight advantage;
- near zero: competing regimes are close;
- negative value: persistence is carrying a Formal label that is no longer the largest current four-state weight.

This field is descriptive. It does **not** mean probability of correctness or probability of a future market move.

### Secondary descriptive field — Regime Support

Use `canonical_formal_support`:

> the current four-state weight assigned to the confirmed Formal regime.

This is also descriptive support for the current classification, not predictive confidence.

### Diagnostic-only field — Weight Concentration

`canonical_concentration` remains available for research/diagnostics but should not be a primary user-facing confidence gauge.

## Evidence

Development-derived Low / Medium / High bins were applied unchanged to later already-observed segments.

### Classification retention

Higher Formal Support / Formal Margin was strongly associated with the current regime persisting:

- Exploratory OOS: high > low in `26 / 27` cases (`96.3%`) for both Support and Margin.
- Burned Final segment: high > low in `26 / 32` cases (`81.2%`) for both Support and Margin.
- Margin showed Low <= Medium <= High retention in `63.0%` and `65.6%` of comparable cases, respectively.

### Directional Markup / Markdown outcomes

The same scores failed the predictive-confidence test:

- Exploratory OOS: high > low aligned return only `3 / 15` (`20.0%`) for Support and Margin.
- Burned Final segment: only `6 / 24` (`25.0%`).
- Median high-minus-low aligned return was negative in both later segments for Support and Margin.

Weight Concentration also failed to show repeatable monotonic directional calibration.

## Product boundary

v0.6 price-only UI / documentation must not label these fields as:

- Confidence;
- Probability;
- Prediction probability;
- Probability of continuation;
- Probability that the Wyckoff stage is correct.

Permitted language is descriptive, e.g. **Regime Margin**, **Regime Support**, **weight concentration**, or **classification strength** with an explicit non-probabilistic explanation.

## Validation boundary

No PnL was used for this decision. The Issue #55 Final OOS remains burned.

## Next gate

Proceed to **Phase E: new independent validation**. Freeze a new post-2022 FX daily dataset that was not used to select Phases A-D, establish Pine/Python implementation parity for the frozen v0.6 design, then evaluate robustness/state separation and any predeclared response rule exactly once on the untouched sample.
