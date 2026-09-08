# Issue #68 Phase B3.11 — Trace Persistence / Decay Audit Preregistration

Status: preregistered diagnostic only. Frozen C-2 classifier and B3.3 Core Bias remain unchanged. No performance use.

## Question

When the five non-Trace S2-vs-S5 fresh-trend components already favor the new direction, does the inherited 50-bar rolling-maximum Trace merely remain as a harmless residual, or does it materially delay the raw S5->S2 / S2->S5 handoff?

## Frozen mechanism under audit

The existing C-2 raw formulation is not changed:

- `acc_trace_for_markup = rolling_highest(acc_raw0, absorb_len)`
- `dist_trace_for_markdown = rolling_highest(dist_raw0, absorb_len)`
- frozen default `absorb_len = 50`
- fresh raw Trace weight = 0.15

No alternative decay, reset, length, or weight is tested in B3.11.

## Diagnostics

For each burned FX series and its reciprocal representation, measure:

1. **Trace source age**
   - bars since the current rolling-window maximum Acc/Dist raw observation that supplies the active trace;
   - deterministic tie convention: most recent equal maximum wins for age attribution.

2. **Stale-opposition state**
   - Bull audit: Break, Heat, Structure, Extension, and Continuation edges all favor S2 while Trace favors S5;
   - Bear audit: exact reciprocal definition.
   - This uses sign only; no new magnitude threshold.

3. **Stale-opposition run length**
   - consecutive bars in the state above;
   - report count, median, p90, maximum, and trace-source age distribution.

4. **Raw-blocking attribution**
   - among stale-opposition bars, count how often total S2-vs-S5 raw still favors the old direction;
   - this distinguishes visible residual Trace from Trace that is actually sufficient to hold the raw duel on the old side.

5. **Counterfactual identity, diagnostic only**
   - compute total fresh raw edge with the Trace term removed while leaving all other five existing components untouched;
   - count bars where the sign of the full raw duel differs from the no-Trace diagnostic duel.
   - This is attribution only, not a proposed model.

6. **Handoff vicinity**
   - for exact old->new fresh raw handoffs, report whether Trace opposed the new direction on t-1 and on t;
   - report Trace source age at t-1.

## Engineering gates

- Existing six-component reconstruction identity must remain at numerical precision.
- Stale-opposition boolean reciprocal agreement >= 99% on pooled comparable bars.
- Full-vs-no-Trace sign-flip attribution reciprocal agreement >= 99% on pooled comparable bars.
- Exact fresh-raw handoff-event reciprocal agreement >= 99%.
- No unexplained attribution category.

Per-pair minima are diagnostic, not separate primary gates unless explicitly preregistered later.

## Human follow-up

Only after the mechanical audit passes, generate a minimal TradingView audit showing:

- total S2 vs S5 raw
- other-five consensus
- Trace direction
- Acc Trace source age
- Dist Trace source age
- whether Trace currently changes the full raw-duel sign

Use FR10Y / JGB10Y as the primary visual reversal cases; GB10Y / US10Y may be used as controls for the cross-rates residual observation.

## Boundary

B3.11 may diagnose the inherited Trace memory but may not change `absorb_len`, Trace weight, rolling-max semantics, stage formulas, gates, Formal persistence, Core Bias, Exposure, or any strategy/PnL rule.