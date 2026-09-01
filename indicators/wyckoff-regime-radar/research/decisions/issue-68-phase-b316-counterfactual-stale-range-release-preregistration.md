# Issue #68 Phase B3.16 — Counterfactual Stale-Range Release preregistration

Status: diagnostic shadow only / frozen production C-2 / no performance use.

## Question

B3.15 established a narrow but credible stale-memory population: Break-final-blocker events where the current MA relation is already on the new target side while the old-direction range-break memory remains active.

B3.16 asks a causal counterfactual:

> Once MA relation is already target-side, is the surviving old-direction range-memory contribution actually sufficient to keep Break and/or the total S2-vs-S5 fresh raw duel on the old side?

This is **not** a test of a better `breakoutBars` value.

## Frozen population

Reuse the exact B3.10 / B3.14 event detector and the B3.15 clock definitions.

Primary population remains exactly:

- Break is the final blocker immediately before an exact S2↔S5 fresh raw handoff;
- at the blocker bar `t-1`, current MA relation is already on the target side;
- old-direction range-break memory is active.

The mechanically observed B3.15 primary population is 20 events and must be reproduced rather than hard-coded.

The 86 PRE_MA_FLIP_AT_BLOCKER cases remain context only and must not be folded into the primary causal result.

## One allowed counterfactual shadow

Only during `MA target-side + old range memory active` overlap, construct a shadow Break score in which the **old-direction range-memory source is removed**.

Everything else stays byte-for-byte / numerically unchanged:

- target-side range evidence remains unchanged;
- target-side MA evidence remains unchanged;
- old-side MA evidence remains unchanged;
- breakout / breakdown mode overrides remain unchanged;
- all non-Break raw components remain unchanged;
- Break weight remains unchanged;
- MA lengths remain unchanged;
- `breakoutBars` remains unchanged;
- no threshold or alternative decay function is introduced.

The old-side Break score must be recomputed through the existing source hierarchy after removing only the old range-memory source. Do not directly force Break positive and do not clamp the result.

## Primary outputs

For the strict B3.15 primary population report:

1. exact event reproduction count;
2. observed Break sign at `t-1` versus counterfactual Break sign;
3. number/share of events where the shadow makes Break target-positive;
4. number/share where Break remains old or neutral because MA/mode evidence still blocks;
5. counterfactual total six-component S2-vs-S5 raw sign at `t-1`;
6. number/share where removing stale old range memory alone would already have moved the total raw duel to the target side;
7. if not immediately positive, first lead in bars before the observed handoff where the shadow total becomes target-positive;
8. reciprocal agreement for event population, shadow Break sign and shadow total sign.

Also report overlap-bar accounting across the primary event windows:

- observed old-negative Break bars;
- shadow old-negative / neutral / target-positive bars;
- cases where NEW RANGE EVIDENCE is already present while the observed Break is old but the shadow Break is target-positive.

## Controls / human review

After mechanical frozen-FX gates pass, generate one TradingView shadow audit for:

- FR10Y 1D Bull — primary adverse case;
- JGB10Y 1D Bull — locked rates control;
- US10Y 1D Bull — additional rates context;
- EURUSD 1D Bull and S&P 500 1D Bull — controls only.

The visual question is not whether the shadow looks prettier. It is whether the fixed one-source removal advances the specific adverse handoffs where B3.15 showed yellow stale overlap and red Break-old behavior.

## Engineering gates

- exact primary-event reproduction versus B3.15;
- reciprocal shadow sign agreement >=99%;
- six-component reconstruction remains exact under both observed and shadow calculations;
- unexplained accounting = 0;
- no performance keys in output.

There is deliberately no gate requiring the shadow to improve anything. A null result is acceptable and would demote stale range memory from causal blocker to correlated context.

## Decision rule

- If removing only stale old range-memory frequently makes Break target-positive **and** materially advances the total raw handoff in the strict primary population, stale range memory becomes a confirmed local causal blocker and may justify a later semantics-design phase.
- If Break improves but total raw does not, Break is real but not sufficient; move to multi-component interaction (likely Break × Heat / Structure timing) rather than tuning Break.
- If even Break itself does not materially release, demote the stale-memory hypothesis.

## Hard boundary

No PnL, no Strategy Tester selection, no `breakoutBars` tuning, no Break-weight tuning, no MA-length changes, no threshold search, no production C-2 modification, no Volume / MTF / Divergence / HMM rescue.
