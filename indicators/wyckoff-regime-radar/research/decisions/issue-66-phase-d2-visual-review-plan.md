# Issue #66 Phase D-2 — Production Visual Shell Review Plan

## Purpose

Phase D-1 proved that the accepted C-2 price-only classifier can be translated to Pine with runtime parity. Phase D-2 now answers a different question:

> When the same C-2 calculation core is placed back inside the real v0.5.2.1 visual/dashboard/alert shell, does the indicator behave coherently to a human reviewer on real TradingView charts?

This is a **visual/runtime integration review only**. It is not a strategy test and may not choose classifier formulas or thresholds.

## Parent

- immutable Pine source: `src/chase-risk-market-regime-radar-v0.5.2.1.pine`;
- accepted Issue #57 + Issue #66 C-2 calculation lineage used by D-1;
- corrected Pine-runtime semantics from D-1B (`ta.percentrank()` mirror and comparator warm-up handling);
- C-3 remains the closeout boundary for classifier-formula repair.

## D-2 generated indicator

Generate a TradingView review build mechanically from the immutable v0.5.2.1 Pine source:

1. apply the exact same `apply_issue66_c2()` calculation transformation used by the parity harness;
2. retain the original `// Visuals` section, dual-layer background, dashboard, Pace Guide, debug line, table, and alert layer instead of replacing them with parity plots;
3. force Volume, MTF, and Divergence witnesses off and Witness Stage Bias to Conservative so the visible state is exactly the accepted **price-only C-2 classifier**;
4. change only the indicator title/short title to identify it as the Issue #66 D-2 visual-review build;
5. do not include D-1 parity plots, screenshot checkpoint table, or D-1B Pine Logs transport.

## Frozen model boundary

D-2 may not change:

- any C-2 score formula;
- any gate or threshold;
- candidate conflict logic;
- confirmation / fast-switch / stale-pressure persistence;
- Stage 1–6 semantics;
- any PnL / strategy / position rule.

If TradingView reveals a compile/runtime integration bug, repair only the visual-shell translation or Pine runtime semantics. A visually surprising historical classification is evidence for review, not authorization to tune the classifier.

## Static acceptance

The generated D-2 Pine must:

- validate the immutable source blob before generation;
- contain the accepted C-2 representation/break/gate/raw/conflict/persistence markers;
- retain `// Visuals`, dual-layer background, Dashboard Table, Pace Guide, and alert conditions;
- retain price-only forced witness modes;
- contain no `PARITY ...` export block;
- contain no D-1B `D1B|` log transport.

## TradingView runtime / human review

First review set: the same four daily FX fixtures used by the symmetry research:

- EURUSD 1D;
- USDJPY 1D;
- GBPUSD 1D;
- AUDUSD 1D.

Review the visible behavior, not performance:

1. Formal stage background should be stable enough to read and should not flicker implausibly bar-to-bar.
2. Candidate state should visibly lead or challenge Formal state in plausible transition zones rather than contradict it persistently without explanation.
3. Markup/Markdown and Accumulation/Distribution transitions should be qualitatively sensible around obvious directional/range changes.
4. Pace Guide / dashboard text should agree with the displayed Formal/Candidate state and risk lines.
5. Bull and bear examples should not show an obvious one-sided semantic bias after the symmetry repair.
6. No compile error, runtime error, blank panel, or table overflow attributable to the D-2 integration.

Screenshots are sufficient. No chart-data export is required.

## Stop rule

If D-2 compiles and the visual review is coherent, Phase D is complete enough to prepare Issue #66 closeout. Do **not** chase perfect historical labels or tune thresholds from screenshots.
