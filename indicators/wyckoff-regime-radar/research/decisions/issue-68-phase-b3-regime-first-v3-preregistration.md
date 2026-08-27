# Issue #68 Phase B3 — Regime-first Lifecycle v3 Preregistration

Status: **preregistered / human-semantic repair / no PnL / no threshold tuning**

## Why v2 is rejected

Phase B/B2 human visual review rejected the transplanted Issue #61 human-review-v2 lifecycle as a trading-semantic baseline. The implementation was reciprocal-symmetric, but its behavior concentrated entries around range-break handshakes, left the strategy flat through much of established Stage 2/5 trend regimes, and allowed three-bar breakout-anchor Early Fail exits to cut positions before the intended regime lifecycle had actually ended.

This is a semantic failure, not a symmetry failure. Symmetry only established that long and short rules behaved alike; it did not establish that the lifecycle expressed the intended trading philosophy.

## Original trading philosophy restored

The base hypothesis is intentionally simple:

> Hold directional exposure during confirmed trend regimes; avoid directional exposure during range / base / distribution regimes; allow same-side trend consolidations to preserve an already-established core position.

The lifecycle must be regime-first. Breakout events are not base entry or exit gates.

## Frozen v3 state transitions

At each confirmed bar close after classifier warmup:

- Formal Stage 2 (Markup) => desired position `+1`.
- Formal Stage 5 (Markdown) => desired position `-1`.
- Formal Stage 1 (Accumulation) => desired position `0`.
- Formal Stage 4 (Distribution) => desired position `0`.
- Formal Stage 3 (Re-accumulation) => keep `+1` only if already long; otherwise desired position `0`.
- Formal Stage 6 (Redistribution) => keep `-1` only if already short; otherwise desired position `0`.
- Formal Stage 0 (unresolved) => preserve the previous desired position.

Consequences:

1. Stage 2/5 may initiate a position even if no fresh structural break occurs on that bar.
2. Stage 3/6 cannot initiate a new position from flat.
3. Stage 3/6 preserve only the matching same-side core position.
4. Stage 1/4 flatten directional exposure because they are range / observe states.
5. A direct opposite trend Stage 2 <-> Stage 5 transition may flip desired direction on that bar.
6. Stage 0 alone never forces a position change.

## Explicit removals from the base lifecycle

The following are **not** part of v3 base entry/exit logic:

- ARM / setup-confirm handshake;
- `confirmBars` entry timing;
- Early Fail breakout-anchor exit;
- fresh `rangeBreakUp / rangeBreakDn` as mandatory entry gates;
- permanent structural stop;
- profit target;
- trailing stop;
- time exit;
- add sizing;
- Stage 3/6 partial sizing.

Breakout / breakdown evidence may remain visible as a later quality witness, but cannot change v3 base desired position in this phase.

## No-PnL semantic gates

Before any Strategy Tester or return metric is opened, v3 must satisfy:

1. synthetic reciprocal Formal sequences produce exact mirrored desired positions and mirrored entry/exit events;
2. actual C-2 original-vs-reciprocal lifecycle desired-position mirror remains >= 99.0%;
3. Stage 2 creates/maintains long, Stage 5 creates/maintains short;
4. Stage 3 holds an existing long but cannot create one from flat;
5. Stage 6 holds an existing short but cannot create one from flat;
6. Stage 1/4 flatten;
7. Stage 0 preserves prior state;
8. human TradingView review should show materially more trend occupancy and materially longer coherent holds than rejected v2, without using PnL to choose rules.

## Diagnostic comparison allowed before PnL

On the already-burned four-FX development fixtures, report only semantic quantities:

- flat / long / short occupancy;
- number of position episodes;
- median / mean / maximum holding bars;
- entry / exit / flip counts;
- reciprocal position/event mirror agreement;
- comparison against rejected v2 occupancy and holding duration.

Do not report return, Sharpe, drawdown, hit rate, transaction costs, or Strategy Tester results.

## Decision after B3

Allowed outcomes:

- `PASS_ready_for_regime_first_tradingview_human_review`;
- `FAIL_regime_first_semantic_contract`;
- `FAIL_regime_first_symmetry_regression`.

A B3 PASS authorizes only a clean TradingView audit indicator. Performance research remains locked until Eddy visually accepts the regime-first lifecycle behavior.
