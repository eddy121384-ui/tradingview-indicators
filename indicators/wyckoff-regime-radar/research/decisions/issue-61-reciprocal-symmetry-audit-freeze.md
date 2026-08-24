# Issue #61 — v0.6 reciprocal / bull-bear symmetry audit freeze

## Question

Before interpreting the observed FX performance tilt as a market/macro effect, determine whether the frozen v0.6 price-only classifier and the current human-review lifecycle are actually symmetric when the same market is quoted reciprocally.

This is a diagnostic audit, not a strategy optimization.

## Frozen transformation

For every frozen OHLC bar with strictly positive prices, construct the reciprocal quote as:

- `open' = 1 / open`
- `close' = 1 / close`
- `high' = 1 / low`
- `low' = 1 / high`

All dates and non-price columns are preserved. No resampling, smoothing or parameter changes are allowed.

## Expected mirror map

If the full classifier were perfectly reciprocal-symmetric, the following states should mirror bar-for-bar:

- `0 ↔ 0`
- `1 Accumulation ↔ 4 Distribution`
- `2 Markup ↔ 5 Markdown`
- `3 Re-accumulation ↔ 6 Redistribution`

Expected event mirrors:

- `rangeBreakUp ↔ reciprocal rangeBreakDn`
- `rangeBreakDn ↔ reciprocal rangeBreakUp`
- `maCrossUp ↔ reciprocal maCrossDn`
- `breakoutModeUp ↔ reciprocal breakdownModeDn`
- bullish lifecycle position `+1 ↔ reciprocal -1`
- long entry ↔ reciprocal short entry
- long early fail ↔ reciprocal short early fail
- long opposite-regime exit ↔ reciprocal short opposite-regime exit

## Diagnostic layers

The audit must report, before any PnL interpretation:

1. **Raw structural-break symmetry** — fresh 20-bar range break pulses.
2. **Representation symmetry** — MA crosses and ATR-scaled break strengths under reciprocal prices.
3. **Classifier-score symmetry** — mirrored breakout/breakdown and continuation score/gate pairs.
4. **State symmetry** — candidate/formal stage mirror agreement.
5. **Lifecycle symmetry** — current human-review lifecycle desired-position/event mirror agreement.

## Known source-level asymmetries to report, not repair

The current frozen v0.6 generator contains explicit bull/bear formula differences inherited from the research core, including:

- upside range breakout evidence scaled by `0.70` versus downside by `0.85` in the breakout-score path;
- upside recent-range gate scaled by `0.85` versus downside by `0.90`;
- downside MA-breakdown evidence requires additional `panic_heat_dn` and `structure_weak` conditions, while the upside MA-breakout path uses a different, looser construction.

These are audit findings, not permission to edit them in this slice.

## Data

Primary audit uses all already-burned frozen Issue #55 static FX fixtures available through `load_frozen_pairs()`. This is reused diagnostic evidence only.

## Interpretation

- If raw range breaks mirror nearly perfectly but later score/state/lifecycle layers do not, the asymmetry is internal to representation and/or classifier logic rather than the underlying market path.
- If the entire stack mirrors closely, later USD-strength performance asymmetry is more plausibly a market-behavior/sample phenomenon.
- If asymmetry is material, do **not** repair or retune in this audit. First localize which layer introduces it, then open a separately frozen repair experiment.

No profitability claim, no threshold shopping, and no modification of the current strategy semantics in this audit.