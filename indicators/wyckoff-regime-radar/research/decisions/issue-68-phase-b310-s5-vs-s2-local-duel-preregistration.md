# Issue #68 Phase B3.10 — S5 vs S2 Local Formula Duel Preregistration

Status: **PREREGISTERED / DIAGNOSTIC ONLY / NO PERFORMANCE**

## Question

When a fresh Bull reversal is developing, why can S5 Markdown raw remain competitive with or above S2 Markup raw?

This phase does not modify C-2. It decomposes the already-frozen S2-vs-S5 raw0 difference into the exact reciprocal weighted components already validated in B3.8.

## Frozen formula identity

For every scored bar:

`S2 raw0 - S5 raw0 = Break edge + Heat edge + Structure edge + Extension edge + Continuation edge + Trace edge`

using the existing weights and existing C-2 primitives only.

Components:

- Break = 0.17 × (breakout - breakdown)
- Heat = 0.17 × (heat_up - panic_down)
- Structure = 0.17 × (structure_up - structure_down)
- Extension = 0.2125 × (markup_extension - markdown_extension)
- Continuation = 0.1275 × (markup_continuation - markdown_continuation)
- Trace = 0.15 × (acc_trace - dist_trace)

No threshold or new feature is introduced.

## Mechanical diagnostics

### A. S5-leading-bar attribution

On scored bars where `S2 raw0 < S5 raw0`, report for each component:

- negative-edge bar count/share (`S5 side > S2 side`);
- cumulative negative deficit (`sum(min(edge, 0))`);
- mean and median edge.

Also report the largest negative component count as continuity with B3.8.

### B. Exact S5 -> S2 raw handoff attribution

A Bull handoff is the exact sign crossing:

- previous scored bar: `S2 raw0 - S5 raw0 <= 0`;
- current scored bar: `S2 raw0 - S5 raw0 > 0`.

For every handoff, report:

1. **final blocker**: the most negative component edge on the immediately preceding bar;
2. **handoff driver**: the component with the largest positive one-bar improvement from preceding bar to handoff bar;
3. component sign on the handoff bar.

No persistence window is added. The transition is defined only by the existing exact raw crossing.

### C. Reciprocal mirror

Run the reciprocal OHLC diagnostic. Bull S5->S2 handoffs must mirror Bear S2->S5 handoffs under the existing stage/component reciprocal mapping.

Primary engineering gates:

- six-component reconstruction error <= 1e-9;
- no unexplained handoff or component attribution;
- reciprocal handoff-event agreement >= 99%;
- reciprocal final-blocker / handoff-driver agreement >= 99% where both sides are comparable.

Per-component floating-point mirror residuals remain diagnostics, not hard gates, consistent with the B3.8 correction.

## TradingView human audit

Generate a diagnostic-only Pine with fixed bands:

1. S2 > S5 RAW
2. BREAK EDGE
3. HEAT EDGE
4. STRUCTURE EDGE
5. EXTENSION EDGE
6. CONTINUATION EDGE
7. TRACE EDGE

Green = S2 side contribution wins; red = S5 side contribution wins; gray = tie/not ready.

The right-edge table should show current S2-vs-S5 raw winner and the currently largest negative edge, without exposing strategy/PnL information.

Priority human review remains:

- FR10Y 1D, 2021–2024 — primary adverse reversal case;
- JGB10Y 1D, 2021–2024 — control.

## Hard boundary

Before B3.10 human review:

- no formula/weight/threshold changes;
- no Strategy Tester or PnL interpretation;
- no stop/target/sizing search;
- no Volume/MTF/Divergence/HMM rescue;
- keep B3.3 Core Bias frozen;
- keep B3.4 A-vs-C Exposure selection paused.

This phase localizes the raw duel; it does not decide a repair.
