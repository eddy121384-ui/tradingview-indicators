# Issue #68 — FR10Y vs DE10Y Downside-Exhaustion Component Preregistration

Status: discovery-only causal attribution. Production C-2 remains frozen.

## Trigger

The relative-gate crossing audit shows that both FR10Y and DE10Y have `S1 RAW >= S2 RAW` on all 512 bars in the shared 2022-2023 Bull-yield window, but DE flips to `S2 effective > S1 effective` on 185 bars versus 110 for FR. The direct algebra check has zero mismatches. Qualitatively, S2 reversals are breakout-gate led and the dominant S1 suppression bottleneck on flip bars is the downside-exhaustion gate.

Therefore the next causal question is not whether gates matter; it is which frozen input inside `downsideExhaustion` makes DE suppress S1 more persistently than FR.

## Frozen formula

`downsideExhaustion =`

- `noBreakLowScore * 0.30`
- `+ negSlopeDullScore * 0.25`
- `+ panicDullScore * 0.20`
- `+ lowVolScore * 0.15`
- `+ lowZoneStableScore * 0.10`

`downsideExhaustionGate = f_gate(downsideExhaustion, 35, absorbThreshold)`

No weights, thresholds, smoothing, lookbacks, or gate formulas may be changed in this audit.

## Attribution transform

For component `x` with weight `w`, define weighted deficit:

`deficit = (100 - x) * w`

The five weighted deficits must reconstruct:

`sum(deficits) = 100 - downsideExhaustion`

up to floating-point tolerance.

This transform is used only for attribution. It does not change the production model.

## Frozen population

- Window: 2022-01-03 through 2023-12-29 inclusive.
- Timeframe: 1D.
- Primary charts: FR10Y and DE10Y.
- Valid population: bars with frozen C-2 S1/S2 RAW, gates, effective scores, and all five downside-exhaustion components available.
- Key flip: `accRaw >= markupRaw and markupEff > accEff`.
- No-flip comparison: `accRaw >= markupRaw and not (markupEff > accEff)`.

## Measurements

For ALL, FLIP, and NO-FLIP populations separately:

1. average `downsideExhaustion` score;
2. average `downsideExhaustionGate`;
3. average of each of the five raw components;
4. average weighted deficit points for each component;
5. largest weighted-deficit source by average deficit points;
6. reconstruction error between summed weighted deficits and `100 - downsideExhaustion`.

Additional context:

7. valid-bar count and flip count;
8. share of bars with `downsideExhaustion < 35`, `35 <= downsideExhaustion < absorbThreshold`, and `>= absorbThreshold`;
9. flip-run count and max run, copied only as context—not as a selection target.

## Preregistered interpretation

- **One component has materially larger weighted deficit in DE flip bars than FR flip bars, and the difference remains directionally coherent versus no-flip bars:** localize the primary mechanism to that component and only then decompose that component one level deeper.
- **Several components contribute comparably:** treat downside-exhaustion as a composite-path mismatch; do not tune one weight. Next step must be a frozen counterfactual attribution across the joint components.
- **FR and DE component profiles are similar despite different flip occupancy:** downside-exhaustion is only a correlated bottleneck, not the causal market splitter. Return to relative S1-vs-S2 gate timing and inspect other multiplicative S1 gates jointly.
- **Reconstruction error is non-trivial:** stop and audit implementation lineage before any semantic conclusion.

## Repair boundary

No production repair is authorized by this audit. Any later repair proposal requires a separately preregistered counterfactual and cross-market controls including FR/DE plus JP/GB/US.