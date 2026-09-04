# Issue #68 — Support-Invariant Slope-Dulling Shadow Preregistration

Status: discovery-only counterfactual. Production C-2 remains frozen.

## Trigger

The FR10Y vs DE10Y NegSlope transformation audit localized the largest cross-market split to the support loss created by the production `log(yield)` chain before the 756-bar percentile rank.

Over the shared 2022-01-03 through 2023-12-29 Bull-yield window, raw 20D bp-slope geometry is similar across FR10Y and DE10Y, while the fraction of valid positive/log-domain history differs materially. The largest transform shift appears between the full-support bp-slope rank and the positive/log-supported rank; later log and volatility-normalization steps contribute much less additional separation.

This makes a domain-support defect plausible: current slope semantics can depend on how much of a market's historical yield series happened to be <= 0, even when current bp path geometry is similar.

## Primary question

If slope-dulling is computed from a full-support basis-point slope percentile, with the same 756-bar horizon and the same frozen 15/55 dulling gates, do FR10Y and DE10Y become materially more semantically consistent?

## Frozen symmetric shadow

The counterfactual changes **only** the slope-rank input used by the reciprocal slope-dulling pair:

Production:
- `negSlopeDullScore = gate(speedRank, 15, 55) * 100`
- `posSlopeDullScore = gate(100 - speedRank, 15, 55) * 100`
- `speedRank` ultimately depends on `log(yield)` and therefore loses support when yield <= 0.

Shadow:
- compute the existing 20D linear-regression slope directly in basis points;
- compute `bpSlopeRankFull = percentrank(bpSlope20, 756)` on the full numeric yield history, including negative yields;
- `negSlopeDullShadow = gate(bpSlopeRankFull, 15, 55) * 100`;
- `posSlopeDullShadow = gate(100 - bpSlopeRankFull, 15, 55) * 100`.

No new thresholds are introduced. The reciprocal pair is changed together to preserve symmetry of the diagnostic shadow.

All direct downstream dependencies are mechanically recomputed under the shadow:

- downside / upside exhaustion and their gates;
- non-absorption / non-distribution gates;
- markup / markdown continuation scores and continuation gates;
- S1-S6 RAW scores where exhaustion or continuation enters;
- S1-S6 gates where exhaustion or continuation enters;
- effective scores and global TOP ordering.

Volume / MTF / Divergence remain in the frozen price-only state inherited from C-2.

## Common-reference diagnostic

A separate **diagnostic only** common FR/DE basis-point reference is included using `TVC:FR10Y` and `TVC:DE10Y` 20D bp slopes. A rolling pooled mean / variance over the same 756-bar horizon produces a common pooled bp z-score. This common-reference z-score is never fed into the classifier shadow and introduces no tuning; it only checks whether the two markets remain similar under one shared numeric reference frame.

## Frozen comparison

- Primary charts: FR10Y 1D and DE10Y 1D.
- Shared window: 2022-01-03 through 2023-12-29 inclusive.
- Expected semantic family: Bull yield regime.
- No PnL, no threshold search, no weight changes, no `rankLen`, `speedLen`, TOP-gap, confirmation, memory, Structure, Break, Heat, Range, or maturity tuning.

## Measurements

For production vs support-invariant shadow:

1. average production `speedRank` vs full-support `bpSlopeRankFull`;
2. average production vs shadow negative/positive slope-dulling scores;
3. average production vs shadow downside/upside exhaustion;
4. average S1 and S2 RAW / effective scores;
5. S2-effective-over-S1 occupancy;
6. S1 TOP, S2 TOP, and Bull-family TOP occupancy;
7. global TOP-change occupancy;
8. average common pooled FR/DE bp z-score as a diagnostic only.

## Preregistered interpretation

### A — Cross-market convergence, both semantically improve

If FR and DE become substantially closer and FR gains the expected Bull/S2 classification without materially damaging DE, the full-support bp percentile is a serious repair candidate. It still requires JP/GB/US controls and reciprocal validation before production consideration.

### B — Cross-market convergence, but both become S1-heavy / semantically worse

This still confirms the **domain-support bug**: DE's better production result was an accidental rescue caused by missing log-domain history. However, replacing `speedRank` with bp rank is **not** itself a semantic repair. The next task becomes redesigning slope-dulling semantics while preserving full support and reciprocal symmetry.

### C — Little convergence

Missing historical support is real but insufficient to explain the FR/DE split. Do not repair production from this hypothesis alone.

### D — Common pooled bp z differs materially

The markets are less path-equivalent than the earlier local geometry audit suggested; retain a market-path contribution in the causal model.

## Repair boundary

This shadow authorizes no production change. Any production proposal must be symmetric, full-support, causally justified, and pass FR/DE plus JP/GB/US controls before merge consideration.
