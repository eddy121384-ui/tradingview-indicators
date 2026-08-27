# Issue #66 Phase B-4 — Raw-Stage Residual Pre-Audit Plan

Status: preregistered diagnostic only. No classifier formula change is authorized by this file.

## Parent

Accepted Phase B-3 direction-neutral trend-entry gate core on the same frozen four-FX fixtures and reciprocal OHLC transforms.

## Question

After B-3, aggregate raw-stage reciprocal MAE remains ~2.678 while gate/effective/probability symmetry improved sharply. Which mirrored raw-stage family contributes most of the remaining raw-stage asymmetry?

Required mirror families:

- Stage 1 Accumulation ↔ Stage 4 Distribution
- Stage 2 Markup ↔ Stage 5 Markdown
- Stage 3 Re-accumulation ↔ Stage 6 Re-distribution

## Measurements

For each family, measure both orientations on every frozen FX pair after the existing rank warm-up:

- left stage raw → reciprocal mirror-stage raw MAE;
- mirror-stage raw → reciprocal left-stage raw MAE;
- valid-value-weighted family MAE;
- family absolute-error contribution and share of all six raw-stage mirrored comparisons.

Also report the same family decomposition for stage gates, effective weights, and probability weights as secondary localization context only.

The weighted sum across the three raw-stage families must reconstruct the existing B-3 `raw_stage_vector_mae` within floating-point tolerance.

## Decision rule

This phase makes no formula change and therefore has no optimization gate. The next repair slice is assigned to the raw-stage family with the largest preregistered weighted raw-stage absolute-error contribution. Ties are resolved by larger family MAE, not by downstream Candidate/Formal results.

After the dominant family is identified, inspect that family's source formula for explicit non-isomorphic primitives before preregistering any B-5 repair.

## Forbidden during B-4

- no formula or threshold changes;
- no PnL, Sharpe, CAGR, drawdown, trade count, win rate, Strategy Tester result;
- no Candidate/Formal metric may choose the dominant raw family;
- no Volume, MTF, Divergence, or HMM;
- no changes to frozen v0.5.2.1 or archived research branches.

PR #67 stays Draft. Issue #66 stays open.
