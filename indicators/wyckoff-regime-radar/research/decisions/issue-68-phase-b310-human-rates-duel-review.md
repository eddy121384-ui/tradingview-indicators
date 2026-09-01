# Issue #68 Phase B3.10 — Human Rates Duel Review

Status: human diagnostic checkpoint only. Frozen C-2 classifier. No parameter, threshold, lifecycle, exposure, or performance change.

## Reviewed charts

TradingView B3.10 `S5 vs S2 Local Formula Duel` on 10Y government-yield daily charts supplied for:

- France 10Y
- UK 10Y
- US 10Y

(The France chart was supplied twice; the duplicate is not treated as an independent observation.)

## Human observation

At the right edge of all three distinct rates charts:

- total fresh raw duel: S2 > S5
- Break: S2
- Heat: S2
- Structure: S2
- Extension: S2
- Continuation: S2
- Trace: S5
- the displayed largest remaining S5 component edge is Trace

This is a cross-rates observation that an opposite-family Trace can remain after the other five contemporary fresh-trend components already favor S2.

## Interpretation boundary

This does **not** establish Trace as the historical cause of the 2021-2024 reversal lag.

B3.10 frozen-FX mechanical attribution remains the stronger handoff-causality evidence:

- 373 exact raw handoffs
- pooled reciprocal final-blocker agreement 99.730%
- pooled reciprocal handoff-driver agreement 99.730%
- final blockers: Structure 140, Break 106, Heat 93, Extension 14, Continuation 14, Trace 6
- handoff drivers: Structure 279, Heat 38, Break 36, Continuation 19, Trace 1

Therefore the rates screenshots identify Trace as a **persistent residual / stale-memory suspect**, not as a convicted primary handoff blocker.

## Newly localized mechanism

The inherited frozen raw formulation defines:

- `acc_trace_for_markup = rolling_highest(acc_raw0, absorb_len)`
- `dist_trace_for_markdown = rolling_highest(dist_raw0, absorb_len)`
- default `absorb_len = 50`
- Trace contributes 15% of S2/S5 fresh raw.

This is a fixed-window rolling maximum, not a gradual decay. A prior high Acc/Dist raw observation can remain the trace value until a higher observation replaces it or the old maximum exits the 50-bar window.

## Decision

Promote Trace to Phase B3.11 for persistence/decay diagnostics only.

B3.11 must determine whether the 50-bar rolling-max memory is merely a visible residual or whether it materially delays S2/S5 raw handoffs. Do not tune `absorb_len`, Trace weight, or any reset/decay rule before that attribution is complete.

No PnL is unlocked by this checkpoint.