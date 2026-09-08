# Issue #68 — FR10Y vs DE10Y Relative-Gate Crossing Preregistration

Status: discovery-only causal attribution. Production C-2 remains frozen.

## Trigger

The RAW margin-distribution audit over 2022-01-03 through 2023-12-29 shows that S1 Accumulation leads S2 Markup at RAW essentially throughout the full window in both FR10Y and DE10Y. FR is actually closer to RAW S2/S1 parity than DE: FR conditional RAW levels are approximately S2 59.1 vs S1 75.1, while DE is approximately S2 54.1 vs S1 76.1.

Earlier Bull-source attribution already showed that final Bull TOP is almost entirely S2 Markup rather than S3 Reaccumulation, with FR S2 TOP around 21.1% and DE around 36.1%, while S3 is around 0.1% in both. Because the gamma transform and common normalization are monotonic, they cannot reverse S1/S2 ordering.

Therefore the relevant causal event is not `RAW S2 > S1 -> EFF S1`; that population is almost empty. The necessary event is `RAW S1 >= S2 -> EFF S2 > S1`, created at the RAW × gate -> effective-score layer.

## Primary question

Why does DE10Y obtain substantially more S2 effective-score wins and final S2 TOP occupancy even though DE starts from a worse S2-vs-S1 RAW ratio than FR?

## Frozen algebra

For each valid bar:

`S1 effective = S1 RAW × S1 gate`

`S2 effective = S2 RAW × S2 gate`

When `S1 RAW >= S2 RAW`, S2 can reverse the ordering only if:

`S2 gate / S1 gate > S1 RAW / S2 RAW`

Define:

- required gate ratio = `S1 RAW / S2 RAW`;
- observed relative gate ratio = `S2 gate / S1 gate`;
- gate surplus = observed relative gate ratio − required gate ratio.

A positive gate surplus should be algebraically equivalent to `S2 effective > S1 effective` when ratios are defined and the effective scores are exactly RAW × gate.

## Frozen comparison

- Window: 2022-01-03 through 2023-12-29 inclusive.
- Primary charts: FR10Y 1D and DE10Y 1D.
- Expected semantic family: Bull yield regime.
- Frozen C-2 calculations and all production thresholds.
- No PnL, no threshold search, no weight changes, no gate formula changes, no `confirmBars` changes, no TOP-gap changes.

## Measurements

1. Share of bars with `RAW S1 >= S2`.
2. Share of bars with `EFF S2 > S1`.
3. Share of `RAW S1 >= S2 -> EFF S2 > S1` flips.
4. Average required gate ratio.
5. Average observed relative gate ratio.
6. Average gate surplus and share with gate surplus > 0.
7. Consistency count between algebraic gate-surplus crossing and direct effective-score ordering.
8. Average / max length and count of consecutive `RAW S1 -> EFF S2` flip runs.
9. Conditional average S1 gate and S2 gate on flip vs non-flip bars.
10. Dominant S1 multiplicative bottleneck on flip vs non-flip bars from:
   - `rangeGate`
   - `bearBackgroundForAccGate`
   - `downsideExhaustionGate`
   - `supportHoldingGate`
   - `nonMarkdownContinuationGate`
11. Dominant S2 gate source on flip vs non-flip bars from:
   - `breakoutMarkupGate`
   - `markupExtensionGate`
   - `markupContinuationGate`

## Preregistered interpretation

- **DE has materially larger observed gate ratio / positive gate surplus despite a higher required ratio:** relative gating is the primary FR-vs-DE semantic splitter. Continue by localizing whether the difference comes mainly from stronger DE S2 gate, weaker DE S1 gate, or both.
- **Flip occupancy differs but average gate ratios do not:** investigate time-distribution / persistence and conditional gate-source composition rather than tuning averages.
- **Flip occupancy and gate ratios are similar:** the remaining difference must come from other-stage global competition after S1/S2 pairwise ordering; do not alter S1/S2 gates.
- **Gate-surplus crossing disagrees with direct effective-score ordering:** stop and audit the implementation algebra before any semantic conclusion.

## Repair boundary

This audit authorizes no production change. Any later repair proposal requires a specific causal mechanism, a frozen counterfactual, and cross-market controls including FR/DE plus JP/GB/US before merge consideration.