# Issue #68 — Yield-Safe HARD Six-Market Regression Final Finding

Date: 2026-09-08

Status: **PASS TO FINAL RELEASE-CANDIDATE SMOKE TEST — NOT FINAL PRODUCTION AUTHORIZATION**

This finding closes the frozen human TradingView A/B regression comparing:

- **A:** accepted Issue #66 C-2 with the Issue #68 yield-safe representation split, but without the S1/S4 current-context cap;
- **B:** the same yield-safe C-2 implementation plus the exact symmetric HARD current-context cap.

No PnL, threshold tuning, stage-weight tuning, market-specific exception, Stateful/grace logic, or lookahead was used.

## Frozen intervention

S1:

```pine
currentBearGate = f_gate(bearBg, 35.0, 75.0)
ctxDownExGate = math.min(downsideExhaustionGate, currentBearGate)
```

S4 mirror:

```pine
currentBullGate = f_gate(bullBg, 35.0, 75.0)
ctxUpExGate = math.min(upsideExhaustionGate, currentBullGate)
```

Only the direct S1/S4 exhaustion routing is capped. S2/S3/S5/S6 raw formulas, gates and witness multipliers remain frozen.

## TradingView A/B snapshots

All markets were reviewed on 1D with representation mode `Auto`. Government bond yield datasets resolved to `Yield Level`.

| Market | Valid bars | Cap bind S1 / S4 | TOP changed | Changed % | Baseline S1 removed | Baseline S4 removed | Cross-release enter S1 / S4 | -> Bull family | -> Bear family | S1 <-> S4 direct | Max changed run | Invariant fails |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FR10Y | 8,674 | 5,613 / 6,151 | 1,125 | 12.97% | 586 | 538 | 124 / 142 | 449 | 410 | 265 | 31 | 0 |
| DE10Y | 10,784 | 7,038 / 7,415 | 1,159 | 10.75% | 590 | 569 | 85 / 126 | 436 | 512 | 211 | 34 | 0 |
| US10Y | 10,131 | 6,608 / 6,942 | 993 | 9.80% | 556 | 437 | 104 / 129 | 406 | 354 | 233 | 21 | 0 |
| GB10Y | 10,014 | 6,520 / 7,090 | 1,198 | 11.96% | 605 | 593 | 108 / 167 | 420 | 503 | 275 | 28 | 0 |
| AU10Y | 10,393 | 6,807 / 7,189 | 1,254 | 12.07% | 607 | 646 | 106 / 162 | 432 | 554 | 267 | 22 | 0 |
| JP10Y | 4,431 | 3,261 / 2,742 | 751 | 16.95% | 327 | 416 | 104 / 132 | 201 | 314 | 228 | 31 | 0 |

Pooled descriptive total: 54,427 valid bars and 6,480 TOP changes (11.91%). This pooled percentage is descriptive only and is **not** an optimization target or acceptance threshold.

## Mechanical safety result

**PASS on all six markets.**

Every reviewed market displayed `INVARIANTS PASS` with `Invariant fails = 0`.

This confirms the preregistered safety properties during TradingView runtime review:

- no TOP difference occurs through an unregistered non-HARD code path;
- the direct S1/S4 HARD effective score is monotonic non-increasing versus the uncapped C-2 arm;
- the repair remains exact-mirror in source construction;
- no new Stateful or grace memory is involved.

## Human semantic review

**PASS / no blocking lifecycle regression observed.**

Across FR10Y, DE10Y, US10Y, GB10Y, AU10Y and JP10Y, A/B TOP differences were visually concentrated around regime/lifecycle transition regions rather than appearing as persistent chart-wide churn.

FR10Y 2021–2023, the motivating stale-confidence case, showed the intended pattern: HARD released stale S1/S4 dominance around major repricing/transition regions without taking over the full trend history.

DE10Y reproduced the same qualitative behavior under a deeper negative-yield history. US10Y provided a positive-yield control with a lower 9.80% TOP-change rate and a max changed run of 21 bars. GB10Y and AU10Y supplied additional independent rate-market controls with no invariant failure.

JP10Y had the highest intervention share at 16.95%. Given its unusually long near-zero/YCC history, this is recorded as a **watch item**, not a blocker. No threshold adjustment or Japan-specific exception is authorized from this observation.

## Representation prerequisite

Before this A/B pass, the Issue #68 yield-safe representation runtime gate passed on:

- FR10Y — negative/near-zero continuity;
- DE10Y — deeper/longer negative-yield continuity;
- JP10Y — near-zero repeated-crossing stability;
- US10Y — positive-yield control;
- OANDA:USDJPY — positive-price / FX Price Log control.

Therefore the six-market result is not attributed to the earlier `log(yield)` domain defect.

## Decision

The exact symmetric HARD current-context repair is **accepted for final release-candidate smoke testing** together with the already-passed yield-safe representation split.

This is **not** final production authorization.

The following remain frozen:

- 35/75 current-context gate bounds;
- classifier thresholds and weights;
- confirmation behavior;
- Volume / MTF / Divergence semantics;
- exact S1/S4 mirror construction;
- representation Auto routing;
- rejected Stateful/grace alternative.

## Next gate

Generate a clean release-candidate source from the frozen `v0.5.2.1` lineage plus accepted C-2, yield-safe representation, exact HARD cap, and approved presentation defaults. The RC must contain **no A/B audit harness**.

Then perform one final TradingView smoke test for:

1. compile / Add to chart;
2. no runtime or plot-limit errors;
3. full production dashboard / visuals / alerts present;
4. `Auto` representation resolves correctly on a bond-yield chart;
5. downside panic-risk default is dashed and phase palette defaults are correct.

Only after that smoke test passes may PR #73 move from Draft to Ready for Review for Eddy's explicit production/merge decision. Issue #68 remains open until that decision.