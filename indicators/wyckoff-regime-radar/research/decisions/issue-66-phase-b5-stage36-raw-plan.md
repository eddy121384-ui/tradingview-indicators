# Issue #66 Phase B-5 — Stage 3/6 Raw Symmetry Repair Plan

Status: preregistered before implementation.

## Parent and evidence

Parent: accepted B-3 classifier. B-4 diagnostic-only pre-audit localized the remaining raw-stage reciprocal error:

- Stage 3 Re-accumulation ↔ Stage 6 Re-distribution: 54.20% of raw absolute error, weighted MAE 4.207516;
- Stage 1 Accumulation ↔ Stage 4 Distribution: 41.51%;
- Stage 2 Markup ↔ Stage 5 Markdown: 4.29%.

Per the preregistered B-4 rule, Stage 3/6 is the only authorized B-5 target.

## Source non-isomorphism

Current raw formulas are structurally aligned except for the fourth 20% component:

- Re-accumulation uses `100 - panic_heat_dn`;
- Re-distribution uses `rebound_failure`.

Under reciprocal bull/bear mirroring, the direct mirror of `100 - panic_heat_dn` is `100 - heat_up`, not `rebound_failure`.

`rebound_failure` remains available for its existing gate/conflict semantics; B-5 changes only its use inside `redist_raw0`.

## Registered change

Introduce a shared direction-neutral primitive:

```text
non_opposite_heat(opposite_heat) = 100 - opposite_heat
```

Use it symmetrically:

```text
reacc_raw0  fourth component = non_opposite_heat(panic_heat_dn)
redist_raw0 fourth component = non_opposite_heat(heat_up)
```

Weights, smoothing, all other raw-stage components, all gates, break evidence, persistence, and thresholds remain unchanged.

## Primary symmetry gate

On the same frozen four-FX reciprocal fixtures, both directions must improve versus B-3:

- `reacc_raw -> inverse redist_raw` MAE lower;
- `redist_raw -> inverse reacc_raw` MAE lower.

Also require these inherited invariants to remain unchanged within floating-point tolerance:

- B-3 Stage 2/5 trend-entry gate reciprocal metrics;
- B-2 break-evidence reciprocal metrics;
- raw range-break and MA-cross reciprocal Jaccard remain 100%.

No Candidate/Formal/PnL metric may determine PASS/FAIL or choose thresholds.

## Secondary observations only

Report overall raw-stage vector MAE, gate/effective/probability vector MAE, Candidate mirror, Formal mirror, and Formal transition mirror. These are causal observations only and may not retune B-5.

## Forbidden

No PnL, Sharpe, CAGR, drawdown, win rate, trade count, Strategy Tester optimization, Volume, MTF, Divergence, HMM, frozen v0.5.2.1 edits, or archived-branch edits.

PR #67 remains Draft; Issue #66 remains open.
