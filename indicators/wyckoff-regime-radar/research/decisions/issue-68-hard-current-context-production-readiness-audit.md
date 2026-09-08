# Issue #68 — HARD Current-Context Production-Readiness Audit

## Decision

**PASS TO PRODUCTION CANDIDATE — NOT FINAL PRODUCTION AUTHORIZATION.**

The exact symmetric HARD current-context cap is engineering-safe enough to be wired into a full C-2 production candidate. Final authorization still requires a compiled production candidate, deterministic baseline diff, and six-market TradingView regression.

Stateful / hysteresis remains rejected. No LOST-case rescue, threshold tuning, PnL, lookahead, or market-specific exception is permitted.

## Frozen repair

S1:

```pine
currentBearGate = f_gate(bearBg, 35.0, 75.0)
ctxDownExGate = math.min(downsideExhaustionGate, currentBearGate)
```

S4 exact mirror:

```pine
currentBullGate = f_gate(bullBg, 35.0, 75.0)
ctxUpExGate = math.min(upsideExhaustionGate, currentBullGate)
```

Only the direct exhaustion-gate routing inside S1/S4 effective eligibility may change.

## Source provenance / generator-chain audit

The immutable source anchor remains:

- `src/chase-risk-market-regime-radar-v0.5.2.1.pine`
- frozen blob SHA: `ab6861181a27697ad566c19bf405a0571be2eb1a`

`generate_price_only_parity_pine.py` and the Issue #66 D-1 generator both refuse generation if that frozen blob changes. The Issue #68 symmetric audit is mechanically downstream from that anchored C-2 lineage.

Important production constraint: **do not ship the generated Issue #68 audit Pine as production.** The D-1 parity harness forces Volume/MTF/Divergence off, changes witness governance to price-only, strips the production visual/alert layer, and adds parity diagnostics. A production candidate must instead apply accepted C-2 lineage to the full production source, preserve production witnesses/visuals/alerts, then add only the symmetric HARD routing change.

## Exact-mirror audit

PASS.

The research implementation is algebraically paired:

- S1 bound = `min(downsideExhaustionGate, currentBearGate)`
- S4 bound = `min(upsideExhaustionGate, currentBullGate)`
- S1 current context = `bearBg`
- S4 current context = `bullBg`
- both gates reuse the same existing `35 / 75` bounds
- no side-specific threshold, weight, lookback, grace, or exception exists

## RAW / routing boundary audit

PASS.

The HARD intervention does **not** redefine `accRaw`, `distRaw`, or any other stage RAW score. It changes only the exhaustion factor used by the S1/S4 effective gates.

The production candidate must preserve the C-2 calculations for:

- S2 Markup
- S3 Reaccumulation
- S5 Markdown
- S6 Redistribution
- Break / Structure / Strong / Formal / gamma
- Volume / MTF / Divergence witness logic
- lifecycle / confirmation logic

### Important parity clarification

S2/S3/S5/S6 **normalized probabilities are not expected to remain numerically identical** on cap-binding bars. Reducing S1 and/or S4 effective score changes the six-stage normalization denominator, so unchanged stages can receive different normalized percentages and can become TOP without any change to their own RAW/gate/effective logic.

The invariant is that S2/S3/S5/S6 RAW, gate, witness multiplier, and pre-normalization effective score calculations remain unchanged.

## Warmup / NA audit

PASS.

`f_gate(x, lo, hi)` returns `0.0` when `x` is `na`. Therefore `currentBearGate` and `currentBullGate` are finite zero during unavailable-history periods, and `math.min(existingExhaustionGate, currentGate)` does not introduce a new NA chain.

The Issue #68 research `close[20]` condition is only a Fresh-cohort audit label. It is **not** part of the production HARD repair and must not be copied into production eligibility.

## Lookahead audit

PASS.

The HARD repair consumes current-bar `bearBg` / `bullBg` and already-existing current exhaustion gates. It introduces no `request.*`, pivot, forward offset, future index, or stateful grace logic. The repair itself contains no historical path test.

## Plot-count audit

PASS, provided the production patch adds no diagnostic plots.

The current production visual/alert layer is already explicitly plot-count compact. Under current TradingView Pine plot-count rules, the source is statically about **44 plot counts** (dynamic/input-color plots included, series-color fills included, `bgcolor` included, and 20 `alertcondition()` calls; `hline()` and `alert()` do not add plot counts). The 64-count limit therefore has material headroom.

The HARD production patch requires **zero** new `plot*`, `fill`, `bgcolor`, `barcolor`, or `alertcondition` calls, so production plot count must remain unchanged from baseline.

## Deterministic production diff contract

A production candidate is acceptable only if all of the following hold:

1. Source provenance is anchored to the accepted full C-2 lineage; no research-only forced-price-only or parity-visual transformation leaks into production.
2. `currentBearGate` / `currentBullGate` are exact mirrors using the frozen `35 / 75` bounds.
3. `ctxDownExGate <= downsideExhaustionGate` and `ctxUpExGate <= upsideExhaustionGate` on every finite bar.
4. S1/S4 direct pre-normalization effective scores can only stay equal or decrease versus C-2; they may never increase because of the cap.
5. S2/S3/S5/S6 RAW, gate, witness multiplier, and pre-normalization effective scores are exact C-2 parity.
6. On bars where neither S1 nor S4 cap binds, all downstream classifier outputs must be exact C-2 parity.
7. On cap-binding bars, downstream normalized probabilities, TOP, Evidence, Candidate, and Formal may change as a deterministic consequence of S1/S4 reduction. Such changes are allowed and must not be falsely classified as unrelated-stage logic edits.
8. Cross-release is allowed: S1 or S4 may become TOP without its own score increasing if the opposite capped stage is reduced more. Direct-score monotonicity, not TOP occupancy, is the invariant.
9. No new state variables, grace period, tuning parameter, lookback, PnL/strategy call, or lookahead mechanism is introduced.
10. Production plot count remains unchanged and below TradingView's 64-count limit.

## Remaining authorization gates

This audit authorizes **construction of the production candidate**, not merge.

Next sequence:

1. Build the full C-2 production candidate with the exact symmetric HARD routing only.
2. Run static/deterministic source diff against C-2 using the contract above.
3. Compile / load in TradingView and confirm no plot-count or runtime/warmup regression.
4. Run six-market 1D regression: US10Y, DE10Y, FR10Y, GB10Y, AU10Y, JP10Y.
5. If all gates pass, move PR #73 from Draft to Ready for Review. Do not merge or close #68 before the final production decision.
