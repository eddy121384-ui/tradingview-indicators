# Issue #68 — Yield-Safe HARD Production Candidate Static Finding

## Decision

**STATIC / GENERATION GATE: PASS.**

The negative-yield representation blocker has been repaired in a new full production candidate without altering the already-approved HARD S1/S4 routing.

This is not runtime authorization. The exact generated Pine must still compile/load in TradingView and demonstrate finite behavior through negative/near-zero yield history.

## Artifacts

Generator:
`indicators/wyckoff-regime-radar/research/generate_issue68_yield_safe_hard_production_candidate_pine.py`

Generated candidate:
`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue68-yield-safe-hard-production-candidate.pine`

Deterministic diff versus the prior full HARD candidate:
`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue68-yield-safe-hard-production-candidate.diff`

GitHub Actions generated the artifacts in bot commit:
`f4b7c953eab5c842a58c3a7f87134569e6ed62f1`

## What changed

A representation mode was added with `Auto`, `Price Log`, and `Yield Level`.

Auto resolves to Yield Level only under static TradingView metadata:

`syminfo.type == "bond" and syminfo.currency == "NONE"`

Yield Level changes only the Issue #66 B-1 representation family: slope/volatility source, MA representation, true-range representation, normalized MA distances, low-vol rank input, range-width normalization, MA cross representation, MA-side break evidence, and MA-spread normalization.

## What did not change

- HARD current Bear/Bull gates and min caps are byte-preserved.
- S1/S4 HARD direct routing is byte-preserved.
- Stage RAW formulas are unchanged.
- Stage gate formulas outside the selected representation inputs are unchanged.
- No threshold or weight changed.
- No historical-value Auto detection was added.
- Volume/MTF/Divergence production modes remain present.
- Production visuals/dashboard/alerts remain present.
- Plot-generating call footprint is unchanged.
- No strategy/PnL logic is present.

## Price-log preservation

The original Issue #66 log variables and formulas remain intact as the Price Log branch. Under Auto on non-yield datasets, the selected model variables alias those existing log-space values. The yield repair therefore does not generically discard the reciprocal-safe price representation.

## Runtime gate

Load the exact generated candidate in TradingView with `資料表示模式 = Auto`.

Primary check: `TVC:FR10Y`, 1D, full history. The 2019–2021 negative/near-zero yield period must no longer disappear from the model because of `log(yield)` domain failure.

Then check DE10Y, JP10Y, US10Y. If Auto metadata does not resolve as expected on a specific provider symbol, use the explicit `Yield Level` override only to diagnose metadata classification; do not use it as a symbol-specific classifier tuning exception.

After representation runtime PASS, resume the frozen six-market HARD regression. PR #73 remains Draft/Open; Issue #68 remains Open.