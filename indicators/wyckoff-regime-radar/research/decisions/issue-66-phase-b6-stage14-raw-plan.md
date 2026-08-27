# Issue #66 Phase B-6 — Stage 1/4 Raw Symmetry Repair Plan

Status: preregistered before implementation.

## Parent and target

Parent: accepted Phase B-5 classifier.

B-4 localized B-3 raw-stage error to Stage 3/6 first and Stage 1/4 second. B-5 changed only Stage 3/6 and reduced its reciprocal raw MAE from ~4.21 to ~0.07 while leaving Stage 1/4 untouched. Therefore Stage 1 Accumulation ↔ Stage 4 Distribution is now the dominant remaining raw-stage family.

## Source non-isomorphism

Current raw formulas are aligned in the first four components, but their final 10% components differ:

- Accumulation uses `low_vol_score`;
- Distribution uses `bear_pressure_rising`.

`low_vol_score` is direction-neutral / reciprocal-invariant after the accepted B-1 representation repair. Its mirror is itself. `bear_pressure_rising` is directional and is not the reciprocal mirror of low-volatility context.

## Registered change

Create one shared direction-neutral quiet-range primitive equal to the existing `low_vol_score` and use it as the final 10% component of both Stage 1 and Stage 4 raw scores.

No weights, smoothing, other raw-stage components, gates, break evidence, persistence, or thresholds may change.

`bear_pressure_rising` remains available for its existing downstream semantics (for example Re-accumulation gating) and is not deleted.

## Primary symmetry gate

On the same frozen four-FX reciprocal fixtures, both directions must improve versus B-5:

- `acc_raw -> inverse dist_raw` MAE lower;
- `dist_raw -> inverse acc_raw` MAE lower.

Inherited invariants must remain unchanged within floating-point tolerance:

- B-2 break-evidence reciprocal metrics;
- B-3 Stage 2/5 trend-entry reciprocal metrics;
- B-5 Stage 3/6 raw reciprocal metrics;
- raw range-break and MA-cross reciprocal Jaccard remain 100%.

Candidate/Formal/PnL metrics are not PASS/FAIL criteria.

## Secondary observations only

Report overall raw-stage, gate, effective, and probability vector MAE plus Candidate/Formal/transition mirrors. These may not retune B-6.

## Forbidden

No PnL, Sharpe, CAGR, drawdown, win rate, trade count, Strategy Tester optimization, Volume, MTF, Divergence, HMM, frozen v0.5.2.1 edits, or archived-branch edits.

PR #67 remains Draft; Issue #66 remains open.
