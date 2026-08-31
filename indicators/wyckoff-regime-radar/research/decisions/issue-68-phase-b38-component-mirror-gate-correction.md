# Issue #68 Phase B3.8 — Component Mirror Gate Correction

Status: engineering-spec correction only. No classifier, raw weight, threshold, gate, persistence, Core Bias, or Exposure change.

## What failed

The first B3.8 burned-data run passed its synthetic contracts and exact Stage-2-vs-Stage-5 raw0 reconstruction, but the report's primary engineering gate also required every individual weighted component delta to mirror under reciprocal quotation with MAE <= 1e-6.

That 1e-6 requirement was introduced in implementation after preregistration. It was not part of the preregistered acceptance contract, which explicitly allowed the already-known tiny C-2 numerical/tie residuals in reciprocal diagnostics.

## Observed residuals

A one-shot frozen four-FX diagnostic showed maximum pair MAE by weighted component:

- BREAK: 0.0593948839 points
- CONTINUATION: 0.0261434240 points
- TRACE: 0.0218012260 points
- EXTENSION: ~5.5e-16
- HEAT: ~1.0e-15
- STRUCTURE: 0.0

The nonzero residuals are localized to event/window/state-history components. Primitive direction components remain essentially exact mirrors.

At the same time:

- Stage2-vs-Stage5 raw0 delta reconstructed from the six preregistered weighted components to max absolute error 2.84e-14;
- raw-winner attribution had zero unexplained winners;
- minimum Bull/Bear reciprocal boolean attribution agreement remained 99.8176%.

Therefore the 1e-6 per-component numeric requirement is an overconstraint on a diagnostic decomposition, not evidence of a new classifier asymmetry.

## Corrected engineering gate

B3.8 primary acceptance keeps only preregistered structural checks:

1. raw winner grouping must be exhaustive (`winner_unexplained == 0`);
2. six-component Stage2-vs-Stage5 raw0 reconstruction must be exact to numerical tolerance (`<= 1e-9`);
3. reciprocal boolean attribution agreement must remain >= 99%.

Per-component reciprocal MAE remains reported as a diagnostic and must not be threshold-shopped into a new pass/fail number.

## Boundary

This correction does not alter C-2 calculations or Issue #68 lifecycle logic. It only removes a post-preregistration engineering assertion that was stricter than the already-accepted C-2 numeric residual behavior.
