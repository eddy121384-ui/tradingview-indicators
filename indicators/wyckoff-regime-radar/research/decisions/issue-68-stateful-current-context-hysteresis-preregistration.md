# Issue #68 — Stateful current-context hysteresis preregistration

## Purpose

Test whether the exact symmetric current-context repair can preserve short-lived, still-valid S1/S4 state continuity without reintroducing stale historical-memory persistence.

Production C-2 remains frozen. This is a research-only lifecycle audit. No PnL, no Strategy Tester, no threshold search, no stage-weight tuning.

## Established evidence before this audit

The direct exhaustion-gate path was localized as the dominant source of the FR10Y / DE10Y stale-S1 pathology:

`historical maturity / slope memory -> exhaustion -> exhaustion gate -> S1/S4 gate amplification`

The exact symmetric hard current-context intervention is:

- S1: `min(DownEx gate, current Bear gate)`
- S4: `min(UpEx gate, current Bull gate)`

Across US10Y, DE10Y, FR10Y, GB10Y, AU10Y, and JP10Y, that hard cap preferentially removes stale states and retains most mechanically defined Fresh-S1/Fresh-S4 anchors. High-confidence losses consistently show weak current context, strong historical background gates, large historical-minus-current gaps, and 100% `trace > current` share.

## New hypothesis

The hard cap is directionally correct but may be unnecessarily abrupt at the exact bar where current context weakens. A stateful lifecycle should separate **acquisition** from **retention**:

- acquisition must pass the hard current-context classifier;
- once S1 or S4 is acquired, a short disagreement grace period may preserve continuity;
- historical maturity trace is not allowed to reacquire or indefinitely sustain the state by itself;
- if production itself no longer has the same S1/S4 TOP, the grace is cancelled immediately;
- if the hard current-context classifier selects the opposite S1/S4 state, the opposite state is acquired immediately.

## Frozen hysteresis rule

No new lookback or threshold is introduced. The existing production `confirmBars` setting is reused as the only lifecycle horizon.

Let `hardTop` be the exact symmetric hard-cap TOP already audited.

For S1:

1. If `hardTop == S1`, acquire/refresh S1 and reset disagreement count to zero.
2. If S1 is currently held, `hardTop != S1`, but production `topId == S1`, increment disagreement count.
3. Keep S1 only while disagreement count `< confirmBars`.
4. On the `confirmBars`-th consecutive disagreement bar, release to `hardTop`.
5. If production `topId != S1`, release immediately.
6. If `hardTop == S4`, switch immediately to S4. S4 is the exact mirror.

This means the existing `confirmBars=3` default holds the old state for at most two consecutive hard-cap disagreement bars before release. The audit does not search alternative values.

## Primary comparison

Compare three semantics on the same full-history data:

1. `PROD` — frozen production C-2 TOP.
2. `HARD` — exact symmetric current-context hard cap.
3. `STATE` — the frozen hysteresis overlay above.

Primary charts: US10Y, DE10Y, FR10Y, GB10Y, AU10Y, JP10Y, daily, full available history.

## Metrics fixed before review

For S1 and exact mirrored S4, report:

- Fresh retention under HARD vs STATE;
- Other/possibly-stale removal under HARD vs STATE;
- Fresh bars rescued by STATE relative to HARD;
- stale/Other bars reintroduced by STATE relative to HARD;
- global TOP changed vs production under HARD vs STATE;
- TOP switch count under HARD vs STATE;
- number and maximum run of hysteresis-held S1/S4 bars;
- releases caused because production itself left the held state;
- exact `confirmBars` used.

## Interpretation rule

The stateful proposal advances only if it shows a genuine lifecycle trade-off rather than a blanket rollback of the hard cap:

- Fresh retention should improve relative to HARD in at least some sensitive corners;
- stale/Other removal must remain materially present rather than collapsing back toward production;
- STATE should not create more classifier churn than HARD as its intended purpose is hysteresis;
- maximum grace-held run must obey the preregistered `< confirmBars` rule;
- S1 and S4 must remain exact mirrors with no one-sided exception.

If Fresh improves only because STATE broadly reintroduces stale S1/S4 or increases churn, reject this implementation and keep the hard cap as the stronger candidate.

## Hard boundary

- no production edit;
- no one-sided S1/S4 exception;
- no 35/75 or margin threshold tuning;
- no MA, Break, Structure, Strong, Formal, gamma, Volume, MTF, Divergence, or HMM changes;
- no returns, Sharpe, hit-rate, drawdown, or Strategy Tester;
- keep PR #73 Draft/Open;
- do not close Issue #68.
