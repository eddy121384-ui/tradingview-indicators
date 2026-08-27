# Issue #68 Phase B3.1 — Entry / Hold Separation Preregistration

Status: **preregistered / human-semantic repair / no PnL / no new thresholds**

## Trigger

Human review of the Phase B3 EURUSD 1D audit found that the regime-first v3 fixed the main holding problem: major 2022 bearish and 2025 bullish regimes were held materially better than human-review-v2. However, the 2023-2024 broad range still produced too many Flat -> Long/Short entries because any persisted Formal 2/5 was treated as sufficient entry authorization.

B3 is therefore a **partial semantic pass**:

- holding semantics: provisionally PASS;
- initial-entry semantics: FAIL / too permissive inside broad ranges;
- no Strategy Tester or performance interpretation is authorized.

## Existing C-2 signal reused

Do not invent another threshold. C-2 already defines `strongCandidate` from the existing classifier contract:

- valid sharpened probabilities;
- top weight >= existing `dominantMin`;
- top gap >= existing `topGapMin`;
- evidence >= existing evidence requirement;
- no `candidateConflict`.

Python equivalent is `strong_stage = where(strong_candidate, top_id, 0)`.

## v3.1 entry / hold contract

### Initial / replacement entry

A trader who is not already holding the same direction may enter:

- Long only when `formal_id == 2` **and** `strong_stage == 2` on the same close;
- Short only when `formal_id == 5` **and** `strong_stage == 5` on the same close.

No breakout, ARM, confirmBars handshake, Early Fail, stop, target, or newly tuned threshold participates.

### Existing Long

- Formal 2: hold Long even if current strongCandidate disappears or points elsewhere;
- Formal 3: hold Long;
- Formal 0: preserve Long;
- Formal 1 or 4: exit to Flat;
- Formal 5: exit Long; flip to Short on the same close **only if** `strong_stage == 5`, otherwise Flat;
- Formal 6 cannot initiate Short from a Long/Flat state.

### Existing Short

Exact reciprocal mirror:

- Formal 5: hold Short even if current strongCandidate disappears or points elsewhere;
- Formal 6: hold Short;
- Formal 0: preserve Short;
- Formal 1 or 4: exit to Flat;
- Formal 2: exit Short; flip to Long on the same close **only if** `strong_stage == 2`, otherwise Flat;
- Formal 3 cannot initiate Long from a Short/Flat state.

### Flat

- Formal 1/3/4/6/0: remain Flat;
- Formal 2: Long only with aligned strong Stage 2 authorization;
- Formal 5: Short only with aligned strong Stage 5 authorization.

## Research question

Can C-2's already-defined strong current-bar evidence act as a clean **entry authorization layer**, while persistent Formal state remains the **holding layer**, reducing range entries without destroying the large-trend holds recovered by v3?

## Gates before TradingView review

1. synthetic reciprocal sequences mirror exactly;
2. burned four-FX desired-position reciprocal mirror >= 99.00%;
3. no new numeric threshold or parameter is introduced;
4. every v3.1 entry occurs on aligned Formal + strong stage;
5. held same-direction Formal 2/3/5/6 does not require strongCandidate to persist;
6. Stage 1/4 flatten and Formal 0 preservation remain unchanged from v3;
7. no PnL / return / Sharpe / drawdown / costs / Strategy Tester metrics are computed.

## Decision

If static + burned-data semantic gates pass, generate a pure TradingView audit indicator for EURUSD 1D human review. Performance research remains locked until human review says the 2023-2024 range behavior and major-trend holding behavior are both coherent.
