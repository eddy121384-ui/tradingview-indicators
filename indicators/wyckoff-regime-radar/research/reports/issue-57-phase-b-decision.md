# Issue #57 — Phase B decision

Decision: **phase_b_passed_stale_decay_2x**

Phase B is accepted as an engineering redesign of Formal-state persistence. This decision uses only already-observed / burned Issue #55 history and internal state-machine behavior; no trading PnL was consulted.

## Frozen Phase-B rule

Strong-candidate confirmation remains unchanged.

An existing nonzero Formal state accumulates stale pressure when there is:

1. chaos;
2. a weak displayed challenger different from the current Formal state; or
3. coexistence pressure with no displayed candidate.

Weak challengers are **never promoted directly**.

If unsupported pressure persists for `2 * confirm_bars`, the old Formal state is cleared to Neutral (`0`). With the frozen defaults, `confirm_bars = 3`, so stale decay occurs after **6 consecutive bars**.

A replacement state must still qualify as a strong candidate and complete the original confirmation / fast-switch path.

## Why 6 bars

The preregistered engineering sweep compared exact `1x / 2x / 3x` multiples of the existing confirmation horizon, after excluding the indicator warm-up. The live window begins at index 1052 (`2016-12-23`) for all four frozen FX pairs.

Warm-up-excluded median / aggregate results:

| Metric | Phase A | 3 bars | 6 bars | 9 bars |
|---|---:|---:|---:|---:|
| Formal carry share | 21.29% | 12.20% | 17.69% | 20.51% |
| Formal zero share | 0.74% | 12.28% | 5.82% | 2.63% |
| Carry-run P90 | 6.80 | 3.00 | 5.00 | 6.75 |
| Formal dwell median | 15.00 | 13.00 | 14.50 | 15.50 |
| One-bar Formal flips | 1 | 3 | 3 | 2 |
| Total Formal switches | 226 | 340 | 289 | 243 |

Engineering trade-off versus Phase A:

- 3 bars: `42.68%` carry reduction, but `+11.54 pp` Neutral share and `+114` Formal switches — rejected as too aggressive.
- 6 bars: `16.90%` carry reduction, `+5.08 pp` Neutral share and `+63` Formal switches — selected as the middle engineering trade-off.
- 9 bars: only `3.66%` carry reduction with `+17` switches — rejected as too close to the original sticky behavior.

## Why weak challengers are not promoted

After warm-up, weak opposing challengers account for `56.70%` of Formal-carry bars, but only `26.34%` are followed by Formal adoption within 5 bars and `36.59%` within 10 bars. They become strong candidates more often (`54.63%` / `65.85%`), so they are useful evidence that the old Formal label may be stale, but are too noisy to deserve direct promotion.

## Boundary

This Phase-B decision does **not** validate predictive utility, profitability, confidence calibration, or state cardinality. The Issue #55 Final OOS remains burned.

## Next gate

Proceed to **Phase C: state-cardinality audit**. Compare the original six-stage representation against predeclared four-state and three-state semantic mappings on already-burned history. Prefer the smallest representation that preserves materially useful and temporally stable path separation. A new independent sample will still be required later.
