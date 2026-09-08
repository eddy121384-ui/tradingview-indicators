# Issue #68 Phase A — Lifecycle Transplant Preregistration

Status: **preregistered / no PnL / no threshold tuning**

## Parent

- Repository baseline: current `main` after Issue #66 / PR #67 squash merge.
- Classifier baseline: symmetry-repaired Issue #66 C-2 price-only classifier.
- Lifecycle source of truth: archived Issue #61 human-review v2, not the earlier over-trading implementation.

## Research question

Can the already human-reviewed Issue #61 lifecycle v2 be mechanically reattached to the symmetry-repaired C-2 classifier while preserving its intended causal semantics and materially improving reciprocal lifecycle symmetry versus the old 86.44% desired-position mirror baseline?

Phase A answers only the semantic / engineering question. **No return, Sharpe, drawdown, Strategy Tester score, or transaction-cost result may choose or modify lifecycle rules in this phase.**

## Frozen lifecycle contract

### Initial long setup

1. Flat trader must first encounter Stage 1 context.
2. Fresh `rangeBreakUp` arms a bullish setup.
3. Formal Stage 2 must confirm within existing `confirmBars = 3`.
4. A fresh break on the exact Stage 1 -> Stage 2 transition bar is accepted.
5. No direct flat entry from an arbitrary fresh break inside an already-running Stage 2.

### Initial short setup

Exact reciprocal mirror:

1. Flat trader must first encounter Stage 4 context.
2. Fresh `rangeBreakDn` arms a bearish setup.
3. Formal Stage 5 must confirm within `confirmBars = 3`.
4. A fresh breakdown on the exact Stage 4 -> Stage 5 transition bar is accepted.
5. No direct flat entry inside an already-running Stage 5.

### Position persistence

- Long exits only when Formal enters bearish family `4/5/6`.
- Short exits only when Formal enters bullish family `1/2/3`.
- Formal `0` is unresolved and does not force exit.
- Same-side consolidation does not automatically flatten the position.
- Fresh continuation breaks while holding are `ADD?` events only; base exposure is unchanged.

### Early Fail

- Entry breakout/breakdown level is an invalidation anchor for entry ages `1..confirmBars` only.
- `confirmBars` remains the existing default 3; no new fail horizon is introduced.
- After an Early Fail exit, automatic same-direction re-entry is forbidden.
- A brand-new setup cycle is required.

### Execution

- One-bar-lag accounting in Python research.
- TradingView semantic preview uses `process_orders_on_close=false`.
- Visual preview uses fixed 1-unit sizing.
- Performance preview, when Phase B is reached, may normalize capital/sizing only in the strategy declaration; lifecycle body must be byte-identical.

## Explicitly frozen / forbidden in Phase A

Do not change:

- C-2 classifier formulas or thresholds;
- `confirmBars`;
- structural break definition;
- Early Fail horizon;
- opposite-family exit semantics;
- no-chase rule inside active Stage 2/5;
- no-reentry-after-fail rule;
- position size;
- add-on size;
- stop/target rules;
- Volume / MTF / Divergence / HMM.

Do not revive rejected Issue #61 experiments:

- Stage 3/6 partial sizing;
- `rangeScore >= 70` half-size rule;
- permanent breakout invalidation;
- ATR/percentage stop search;
- naive stage-color strategy as anything other than a later comparator.

## Phase A implementation requirements

1. Reuse the Issue #66 C-2 Python core from current mainline.
2. Port the archived Issue #61 v2 state machine mechanically, preserving variable/state semantics where practical.
3. Produce event series for at minimum:
   - bullish arm;
   - bearish arm;
   - long entry;
   - short entry;
   - long opposite-family exit;
   - short opposite-family exit;
   - long Early Fail;
   - short Early Fail;
   - long `ADD?` candidate;
   - short `ADD?` candidate;
   - desired position / held position.
4. Audit setup-to-confirmation lag distribution.
5. Audit event counts, exposure-state occupancy, and holding-duration distribution without computing return.
6. Run original vs reciprocal OHLC lifecycle mirror diagnostics.

## Primary engineering gates

The transplant passes Phase A only if:

1. synthetic mirrored lifecycle inputs produce exact mirrored lifecycle outputs;
2. original-vs-reciprocal desired-position mirror materially exceeds the archived Issue #61 baseline of 86.44%;
3. bullish and bearish event families do not show an unexplained source-level asymmetry;
4. no direct flat chase entry inside an already-running Stage 2/5 is observed by contract tests;
5. Early Fail occurs only during the first `confirmBars` bars;
6. post-fail same-direction re-entry is impossible without a new arm/setup event.

Candidate/Formal symmetry itself is inherited from Issue #66 and is not retuned here.

## Secondary observations

Report but do not optimize:

- arm count;
- confirmation count;
- setup expiration count;
- setup-to-confirmation lag histogram;
- Early Fail frequency;
- opposite-family exit frequency;
- `ADD?` frequency;
- median / distribution of holding bars;
- time spent flat / long / short.

## Data governance

Issue #57/#61/#66 FX histories are burned development evidence. They may be reused for semantic and engineering diagnostics, but cannot later be described as independent validation.

No untouched validation basket is opened in Phase A.

## Decision after Phase A

Allowed outcomes:

- `PASS_ready_for_tradingview_semantic_preview`;
- `FAIL_lifecycle_transplant_semantic_mismatch`;
- `FAIL_lifecycle_symmetry_regression`.

A Phase A PASS authorizes Phase B visual semantic review only. It does not authorize strategy-performance interpretation yet.
