# Issue #57 — Bridge formation behavior-map definitions

Status: **BURNED-DATA EXPLORATION — definitions frozen before outcomes**

Purpose: understand whether early Wyckoff-like Top-2 bridge states identify a potential transition before the actionable 2+3 / 5+6 pair is fully formed. This is not independent OOS and does not change production rules.

## Event definition

A bridge state is an unordered Candidate + Secondary pair:

- bullish bridge: `1+2` or `1+3`;
- bearish bridge: `4+5` or `4+6`.

Only the first bar of a bridge watch is counted. Once a watch starts, no additional bridge onset is counted until that watch resolves.

## Resolution

From the bridge onset, scan forward for at most 20 bars:

- bullish bridge succeeds when actionable `2+3` appears;
- bearish bridge succeeds when actionable `5+6` appears;
- if the opposite actionable pair appears first, the watch resolves as opposite failure;
- if neither happens by 20 bars, the watch resolves as timeout.

Report same-direction conversion rates within 5, 10, and 20 bars. The 10-bar outcome is the fixed middle-horizon grouping used to compare successful vs not-yet-successful bridge characteristics; it is not selected from PnL.

## Onset characteristics

At bridge onset record, without fitting thresholds:

- Top-2 combined strength;
- normalized six-stage entropy;
- context-stage weight (`1` for bull, `4` for bear);
- target actionable-family weight (`2+3` for bull, `5+6` for bear);
- same-side structural pressure (`1+2+3` bull, `4+5+6` bear);
- opposite-side structural pressure;
- 3-bar changes in Top-2 strength, entropy, same-side pressure and opposite-side pressure where available;
- Formal direction category: aligned / neutral-transition / opposite.

## Outcomes

Report:

- event counts and conversion rates at 5/10/20 bars;
- median bars to same-direction actionable formation;
- success-within-10 vs no-success-within-10 onset-characteristic medians;
- 5/10/20-bar direction-aligned forward return;
- 10-bar MFE and MAE from bridge onset;
- per-pair consistency.

## Boundary

These seven FX fixtures are intentionally reused because the purpose is to understand existing indicator behavior. No threshold, weight, or production rule may be selected from this map and then claimed as independently validated on the same data.
