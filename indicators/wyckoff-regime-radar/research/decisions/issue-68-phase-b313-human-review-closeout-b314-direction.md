# Issue #68 Phase B3.13 human review closeout — direction for B3.14

Status: diagnostic only. Production C-2, B3.3 Core Bias, Exposure policy, thresholds and performance remain frozen.

## B3.13 reviewed artifact

`generated/wyckoff-issue68-phase-b313-continuous-structure-shadow-audit.pine`

Locked cases:
- FR10Y 1D Bull — primary adverse case
- JGB10Y 1D Bull — control

## Human result

The preregistered continuous Structure shadow does **not** materially improve the primary adverse case.

FR10Y 2021-2023 does not show a sustained early-green `SHADOW DIFF` pattern. Large portions are aligned or red, so the shadow is often no earlier and at times later than the original raw handoff. JGB10Y is somewhat more favorable in later sections, but the control cannot override failure to improve FR10Y.

This matches the generic mechanical baseline: the shadow is slightly smoother (698 vs 746 target-side transitions, 0.936x) but is already target-positive at t-1 on only 53/373 anchored handoffs (14.2%), with 54 original handoffs where the shadow is still delayed.

## Decision

Reject the single locked continuous-Structure shadow as the primary repair direction.

Do not:
- tune MA50/MA200 lengths;
- tune Structure weight;
- search alternate percentile transforms;
- run a continuous-Structure formula bakeoff;
- modify production C-2 from this evidence.

Preserve B3.12's narrower conclusion: Structure is a major discrete fresh-trend handoff switch. That does not prove Structure continuity is the cause of the visible long-rates reversal lag.

## Next direction — B3.14

Return to the remaining fresh S2-vs-S5 components, prioritizing **Break** before Heat because:

- B3.8: Break had the largest cumulative negative contribution in the S2-vs-S5 duel;
- B3.10: Break was a final blocker on 106/373 handoffs;
- Break itself contains event-memory structure: range-break evidence, recent MA-cross/current-MA-side evidence, and breakout/breakdown mode.

B3.14 should determine whether a negative Break edge immediately before fresh-trend handoff is mainly caused by:

1. **old-side evidence persistence** — recent opposite range-break / MA-cross / mode still supports S5/S2;
2. **new-side evidence absence** — the target side has not yet produced equivalent evidence;
3. **both**, or neither.

No performance use and no Break parameter change until this attribution is complete.
