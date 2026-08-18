# Issue #57 — Transition Health visual preview contract

Status: **FROZEN BEFORE PINE PREVIEW IMPLEMENTATION**

This note translates the already frozen and independently OOS-tested Transition Health candidate into a TradingView visual preview. It does **not** create a trading rule and does not change the validated candidate definition.

## Preservation boundary

- `src/chase-risk-market-regime-radar-v0.5.2.1.pine` remains immutable.
- The v0.6 preview remains **price-only**: Volume / MTF / Divergence are forced Off exactly as in Issue #57 research parity.
- Phase A/B/C/D mechanics remain unchanged.
- No new threshold, return filter, volatility filter, companion-stage rule, stop, target, or holding-period rule may be added.
- Independent OOS data already read in `issue-57-transition-health-independent-oos.md` is now burned and may not be used to tune this implementation.

## Frozen Transition Health semantics

The online state machine must mechanically reproduce the research event extraction.

### Bridge watch

A non-overlapping watch begins on the first semantic bridge bar:

- bullish bridge: Top2 is unordered `{1,2}` or `{1,3}`;
- bearish bridge: Top2 is unordered `{4,5}` or `{4,6}`.

Once a watch begins, no second watch may begin until the current watch resolves by:

1. same-direction actionable Top2 (`{2,3}` bullish or `{5,6}` bearish),
2. opposite-direction actionable Top2, or
3. 20-bar timeout.

This non-overlap rule applies even when the first bridge is context-dominant and therefore produces no visible Transition Health candidate.

### Tracked handoff / seizure

At watch onset:

- bullish context stage = 1; target stages = 2 and 3;
- bearish context stage = 4; target stages = 5 and 6;
- `carried` = the one target stage already present in Top2;
- `companion` = the other target stage;
- the watch is a visible **Handoff** only when `carried_weight > context_weight` on the onset bar.

No minimum gap or percentage threshold is permitted.

### +3 health checkpoint

The fixed checkpoint is **+3 bars after Handoff onset**.

The candidate is eligible for health classification only if the watch is still unresolved after +3, matching the research condition `resolution_lag > 3`.

- **Healthy**: `carried_weight > context_weight` on every bar from onset through +3 inclusive.
- **Damaged**: the candidate was a valid Handoff at onset, but on at least one bar through +3 the old context tied or retook the lead (`context_weight >= carried_weight`).

If same-direction actionable, opposite actionable, or timeout resolves before/on +3, no Healthy/Damaged classification is emitted for that watch.

The +3 classification is frozen. For dashboard convenience it may remain visible until the watch resolves, but no later bar is allowed to upgrade or downgrade the +3 label.

## Visual contract

The preview should preserve the v0.5.2.1 visual layer and add only:

- a small Handoff event label at tracked onset;
- a Healthy label at the eligible +3 checkpoint when continuously held;
- a Damaged label at the eligible +3 checkpoint when the lead was lost/tied at least once;
- a compact separate Transition Health dashboard showing current state, direction, age, and the frozen `+3` definition;
- Data Window fields for state code / direction / watch age;
- optional parity log lines, disabled by default.

Suggested state codes:

- `0` = none / hidden context-dominant watch;
- `1` = Handoff pending +3;
- `2` = Healthy at +3;
- `3` = Damaged at +3.

Direction code: `+1` bullish, `-1` bearish, `0` none.

## Claim boundary

Independent OOS evidence supports **directional discrimination** between Healthy and Damaged on the frozen 5-FX 2022–2026 sample. It does not establish a complete trading strategy, optimal holding period, stop/target policy, or profitability after costs.

The TradingView preview must use `Transition Health`, `Handoff`, `Healthy`, and `Damaged` language. It must not call these labels Buy / Sell / Long / Short signals.
