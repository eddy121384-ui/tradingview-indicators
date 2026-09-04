# Issue #68 Phase B3.11 — Trace Persistence / Decay Closeout

Status: mechanical diagnostic PASS. Frozen C-2. No model or performance change.

## Result

The inherited Trace is visibly stale but is **not the primary blocker** when the other five fresh-trend components already agree on the new direction.

Frozen-FX audit:

- stale-opposition bars (Break + Heat + Structure + Extension + Continuation all favor target, Trace favors old direction): 1,479
- other-five-consensus bars: 2,475
- stale-opposition bars where Trace actually keeps the total fresh raw duel on the old side: **0 (0.00%)**
- stale Trace run length: median 9 bars, p90 29.1, max 87
- opposing Trace source age on stale bars: median 28 bars, p90 47, max 49
- exact fresh-raw handoffs: 373
- Trace still opposes target at handoff t-1: 185 (49.6%)
- Trace still opposes target at handoff t: 184 (49.3%)
- full-vs-no-Trace sign flips across all mixed-component states: 122, exactly balanced between blocking target (61) and rescuing target (61)
- max six-component reconstruction error: 2.842e-14
- pooled stale-opposition reciprocal agreement: 99.909%
- pooled full-vs-no-Trace sign-flip reciprocal agreement: 99.954%
- minimum exact-handoff reciprocal agreement: 99.818%

## Interpretation

Trace is indeed a fixed-window stale-memory mechanism: the source maximum is commonly several weeks old and can remain almost the full 50-bar window. That explains the rates screenshots where Trace is the final residual S5 edge after all five contemporary components favor S2.

However, this residual is not sufficient to prevent the new direction from winning when the other five components unanimously agree. The model frequently completes a raw handoff while Trace is still opposing the new direction.

Therefore the visual cross-rates Trace residual should **not** be used as justification to shorten `absorb_len`, reduce Trace weight, add a reset, or replace the rolling maximum.

## Decision

Demote Trace from primary repair candidate to secondary residual behavior.

Return the main causal investigation to the B3.10 handoff evidence. Structure is now the highest-priority next target because it is both:

- the most frequent frozen-FX final blocker (140 / 373 handoffs), and
- the dominant handoff driver (279 / 373 handoffs).

Break remains the second-priority comparator.

Next phase: B3.12 Structure Step / MA-Cross Audit.

No PnL is unlocked.