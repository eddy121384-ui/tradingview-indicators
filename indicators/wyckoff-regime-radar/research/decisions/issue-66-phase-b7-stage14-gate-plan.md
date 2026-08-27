# Issue #66 Phase B-7 — Stage 1/4 Gate Symmetry Repair Plan

Status: preregistered before implementation.

## Parent and target

Parent: accepted Phase B-6 classifier.

B-6 reduced raw-stage vector reciprocal MAE from 1.250358 to 0.058428 while leaving the gate-vector MAE unchanged at 0.020136. The prior B-4 decomposition showed Stage 1 Accumulation ↔ Stage 4 Distribution gate MAE (~0.0583) overwhelmingly dominates the remaining gate-layer asymmetry; Stage 2/5 and Stage 3/6 gates are already near zero.

## Source non-isomorphism

Current Stage-1 / Stage-4 gates are:

```text
acc_gate = range_gate * bear_background_acc_gate * downside_exhaustion_gate * support_holding_gate * non_markdown_cont_gate

dist_gate = range_gate * mature_bull_gate * upside_exhaustion_gate * resistance_holding_gate * non_markup_cont_gate
```

All factors except the second are reciprocal mirrors. The second-factor definitions are not isomorphic:

```text
bear_background_acc_gate = gate(max(bear_bg, bear_maturity_trace), 35, 75)
mature_bull_gate          = gate(bull_maturity_trace, 60, 85)
```

The direct mirror of the Accumulation background/maturity gate is:

```text
bull_background_dist_gate = gate(max(bull_bg, bull_maturity_trace), 35, 75)
```

## Registered change

Introduce one shared direction-neutral background/maturity gate primitive and use it symmetrically:

```text
background_maturity_gate(background, maturity_trace)
    = gate(max(background, maturity_trace), 35, 75)
```

Use it for:

- `bear_background_acc_gate`;
- new `bull_background_dist_gate`.

Replace only the second factor of `dist_gate` from `mature_bull_gate` to `bull_background_dist_gate`.

Keep `mature_bull_gate` available for diagnostic compatibility; do not alter other gate formulas, raw scores, weights, thresholds, persistence, break evidence, or continuation/extension logic.

## Primary symmetry gate

On the same frozen four-FX reciprocal fixtures, both directions must improve versus B-6:

- `acc_gate -> inverse dist_gate` MAE lower;
- `dist_gate -> inverse acc_gate` MAE lower.

Inherited B-2 break, B-3 trend-entry, B-5 Stage3/6 raw, B-6 Stage1/4 raw metrics must remain unchanged within floating-point tolerance. Raw range-break and MA-cross reciprocal Jaccard remain 100%.

Candidate/Formal/PnL metrics are secondary observations only and may not decide PASS/FAIL.

## Forbidden

No PnL, Sharpe, CAGR, drawdown, trade count, win rate, Strategy Tester optimization, Volume, MTF, Divergence, HMM, frozen v0.5.2.1 edits, or archived-branch edits.

PR #67 remains Draft; Issue #66 remains open.
