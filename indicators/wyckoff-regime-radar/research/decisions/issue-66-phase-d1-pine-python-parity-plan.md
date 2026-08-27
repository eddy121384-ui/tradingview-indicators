# Issue #66 Phase D-1 — C-2 Pine↔Python Parity Plan

Status: **preregistered before Phase D-1 parity-harness implementation**

No PnL, Sharpe, CAGR, MaxDD, or strategy metrics are permitted in this phase.

## Question

Can the accepted Issue #66 Phase C-2 price-only classifier be translated into Pine Script so TradingView and the C-2 Python reference produce the same calculations from the same TradingView OHLC rows?

This is an implementation-parity test, not an economic-validity or trading-utility test.

## Reference lineage

The Pine harness must be mechanically derived from the immutable v0.5.2.1 Pine source and apply the same accepted research lineage as the Python reference:

1. Issue #57 v0.6 continuous boundary primitives;
2. Issue #57 Phase-B stale-pressure persistence;
3. Issue #66 B-1 reciprocal-safe representation;
4. B-2 direction-neutral break evidence/gates;
5. B-3 mirrored fresh trend-entry gate;
6. B-5 Stage-3/6 raw repair;
7. B-6 Stage-1/4 raw repair;
8. B-7 Stage-1/4 background/maturity gate repair;
9. C-2 Stage-1 candidate-conflict mirror repair.

The frozen v0.5.2.1 Pine source itself must not be edited.

## D-1 deliverables

- a source-anchored generator for the Issue #66 parity Pine harness;
- generated Pine under `research/generated/`;
- a dedicated comparator that evaluates TradingView parity CSV against the **C-2** Python loader, not frozen v0.5.2.1 Python;
- unit/contract tests proving the generator starts from the expected frozen Pine blob and contains the accepted C-2 formulas;
- CI that can validate deterministic generation and comparator semantics without pretending to execute TradingView.

## TradingView parity fields

Expose enough Data Window / CSV fields to localize implementation differences, including at minimum:

- heat/maturity/range representation;
- exhaustion/holding;
- extension/continuation;
- six stage gates;
- six stage probabilities/weights;
- top id/value/gap;
- evidence strength;
- candidate display id;
- formal id;
- stale-pressure bars/reason where practical.

## Acceptance gate once a TradingView CSV is supplied

Use TradingView OHLC rows as the Python input. The preregistered engineering gate is:

- Formal stage agreement >= 99.5%;
- Candidate-display agreement >= 99.0%;
- core continuous-field P99 absolute error <= 0.50 points.

A parity failure authorizes only implementation-semantic diagnosis/fixes. It does **not** authorize classifier threshold or formula tuning.

## CI boundary

GitHub CI can prove generation determinism, source anchors, syntax-contract structure, field mapping, C-2 reference selection, and comparator unit tests. CI cannot honestly prove TradingView runtime parity because TradingView does not run inside this repository workflow.

Therefore D-1 must remain **PENDING TRADINGVIEW RUNTIME EVIDENCE** until a TradingView chart-data CSV or equivalent checkpoint capture from the generated Issue #66 harness is supplied.
