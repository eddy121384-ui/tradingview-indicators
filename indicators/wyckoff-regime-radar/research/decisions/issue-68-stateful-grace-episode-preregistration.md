# Issue #68 — Stateful grace-episode outcome preregistration

## Purpose

Determine whether the existing `confirmBars` hysteresis grace period has real lifecycle value or merely delays exits that the exact HARD current-context classifier would have made immediately.

This is a research-only episode audit on frozen C-2. Production remains unchanged. No PnL, Strategy Tester, threshold search, stage-weight tuning, or market-specific exception is permitted.

## Established evidence before this audit

The exact symmetric current-context repair is:

- S1: `min(DownEx gate, current Bear gate)`
- S4: `min(UpEx gate, current Bull gate)`

The stateful overlay uses the existing production `confirmBars` only:

1. acquisition/refresh requires the exact HARD classifier to select S1/S4;
2. while production TOP still remains the same S1/S4 state, a HARD disagreement can be held for fewer than `confirmBars` consecutive bars;
3. production leaving the held stage cancels grace immediately;
4. exact opposite HARD S1/S4 selection switches immediately;
5. S1 and S4 are exact mirrors.

On the six-market daily panel, STATE improves Fresh retention and reduces TOP footprint / switch count versus HARD, but it also reintroduces Other/possibly-stale bars. The unresolved question is whether those grace bars bridge temporary context noise or simply postpone a valid exit.

## Frozen episode definition

A **grace episode** starts on the first bar where:

- STATE is holding S1 or S4;
- HARD no longer selects that same stage;
- production TOP still selects that same held stage.

The episode anchor is classified mechanically at the first held bar:

- `FRESH` if the preregistered Fresh-S1/Fresh-S4 definition is true on that entry bar;
- otherwise `OTHER`.

No later bar can change the episode anchor classification.

## Frozen outcome taxonomy

Every completed episode receives exactly one terminal outcome, evaluated without lookahead:

1. `RECOVER` — before grace expires, HARD re-selects the same held S1/S4 stage.
2. `OPPOSITE` — HARD selects the exact opposite S1/S4 stage before recovery.
3. `PROD EXIT` — production TOP leaves the held S1/S4 stage before HARD recovery and without an exact opposite-HARD switch taking precedence.
4. `TIMEOUT` — production still selects the held stage, HARD still disagrees, and the preregistered `confirmBars` grace expires.

An episode still open on the final available chart bar is reported as `ACTIVE` and excluded from completed-outcome percentages.

Episode duration is the number of bars actually held by hysteresis. It must remain `< confirmBars`; with the current default `confirmBars=3`, completed episode duration can be at most two held bars.

## Primary panel

Run the same generated Pine on full available daily history for:

- US10Y
- DE10Y
- FR10Y
- GB10Y
- AU10Y
- JP10Y

No date selection, symbol-specific parameter changes, or threshold tuning.

## Metrics fixed before review

Report separately for `S1 FRESH`, `S1 OTHER`, `S4 FRESH`, and `S4 OTHER`:

- episode count;
- completed episode count;
- RECOVER count and share of completed episodes;
- TIMEOUT count and share;
- PROD EXIT count and share;
- OPPOSITE count and share;
- average held bars among completed episodes;
- maximum held bars;
- any ACTIVE episode at chart end.

Also report pooled S1 and pooled S4 recovery shares after the six charts are reviewed.

## Decision rule fixed before review

The stateful grace period is preferred over the HARD-only lifecycle only if all of the following hold:

1. **Majority recovery:** pooled completed grace episodes recover (`RECOVER > 50%`) for both S1 and S4. If either side is at or below 50%, grace more often delays a non-recovery than bridges temporary noise, so STATE does not advance over HARD.
2. **Fresh is not worse than stale:** pooled FRESH recovery share must be at least the corresponding OTHER recovery share for S1 and for S4. A grace mechanism that preferentially rescues Other/stale episodes is rejected.
3. **Lifecycle contract:** no episode duration may reach or exceed `confirmBars`; any such occurrence is a logic failure, not a market result.
4. **Exact mirror:** the same taxonomy and mechanics must apply to S1 and S4 with no one-sided exception.

Market-level heterogeneity is reported descriptively and is not used to tune thresholds or horizons.

## Hard boundary

- no production edit;
- no new lifecycle horizon;
- no alternative `confirmBars` search;
- no one-sided S1/S4 rescue rule;
- no 35/75, margin, MA, Break, Structure, Strong, Formal, gamma, Volume, MTF, Divergence, or HMM changes;
- no returns, Sharpe, hit-rate, drawdown, or Strategy Tester;
- keep PR #73 Draft/Open;
- do not close Issue #68.
