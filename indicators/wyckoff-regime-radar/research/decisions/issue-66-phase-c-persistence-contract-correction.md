# Issue #66 Phase C — Inherited Persistence Contract Correction

Status: **diagnostic correction / no classifier change / no PnL**

## What was wrong in the first Phase C replay

The initial Phase C localization replay was written against the older price-only inertia block visible in `price_only_core.py` (strong-candidate confirmation plus chaos-only reset).

However, the accepted B-7 core is generated through `generate_v06_phase_b_core.py`, which mechanically replaces that older block with the Issue #57 Phase-B persistence redesign.

Therefore the actual inherited B-7 Formal-state contract is:

- strong candidates retain the existing confirmation path;
- an unsupported existing Formal state accumulates `stale_pressure_bars`;
- stale pressure reason is, in priority order:
  1. chaos while Formal is non-zero;
  2. a weak/displayed challenger whose stage differs from current Formal;
  3. coexist pressure while no candidate is displayed;
- the old Formal state clears to Neutral only after `2 * confirm_bars` consecutive stale-pressure bars;
- weak challengers are never promoted directly.

This explains the first exposed replay divergence: EURUSD stored Formal cleared from Stage 5 to Neutral while `strong_candidate=0` and `chaos=0`, because the original replay omitted weak-challenger/coexist stale-pressure accumulation.

## Corrected Phase C diagnostic contract

The next replay must reproduce the inherited Issue #57 Phase-B stale-pressure state machine exactly before any attribution is trusted.

Required replay inputs:

- strong-stage id;
- candidate-display id;
- chaos;
- coexist;
- active confirmation bars;
- `confirm_bars` (for the fixed `2x` stale horizon).

Required replay state:

- confirmed Formal id;
- candidate id and candidate bars;
- stale-pressure bars;
- stale-pressure reason.

The exact replay must reproduce B-7 diagnostics:

- `formal_id`;
- `candidate_id`;
- `candidate_bars`;
- `stale_pressure_bars`;
- `stale_pressure_reason`.

## Revised localization probes

After exact replay is proven, Phase C may compare diagnostic-only counterfactuals:

1. original stale-pressure persistence;
2. fixed strong-candidate confirmation (disable fast-switch shortening only);
3. immediate strong-candidate confirmation;
4. chaos-only stale pressure (disable weak-challenger and coexist pressure);
5. disable weak-challenger stale pressure only;
6. disable coexist stale pressure only;
7. immediate stale-pressure clear (one pressure bar clears Formal);
8. no retained Formal state (stateless strong-stage output).

These probes are for causal localization only. They do not authorize any persistence change.

## Structural symmetry requirement

Synthetic mirrored inputs must still produce exact mirrored Formal output under the full stale-pressure state machine. If so, the state machine itself is direction-neutral; remaining Formal asymmetry comes from imperfectly mirrored inputs being carried through state.
