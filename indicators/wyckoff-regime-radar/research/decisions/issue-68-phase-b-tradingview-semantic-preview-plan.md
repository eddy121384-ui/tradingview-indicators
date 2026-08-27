# Issue #68 Phase B — TradingView Lifecycle Semantic Preview Plan

Status: **preregistered / no Strategy Tester interpretation yet**

## Parent

Phase A passed:

- human-review-v2 lifecycle transplanted onto C-2;
- aggregate reciprocal desired-position mirror = 99.92%;
- all semantic unit contracts passed;
- no PnL was computed.

## Question

Does the mechanically transplanted lifecycle *look and behave* like the intended human trading lifecycle when rendered as actual TradingView strategy events?

This phase is a semantic review, not a profitability review.

## One-body / two-declaration contract

Generate two Pine strategies from one shared C-2 calculation core and one shared lifecycle body:

### Visual preview

- fixed 1-unit strategy sizing;
- `process_orders_on_close=false`;
- lifecycle marks visible by default;
- intended only for human inspection of timing/semantics.

### Performance preview

- normalized strategy declaration suitable for later cross-symbol performance comparison;
- `process_orders_on_close=false`;
- **the complete Pine body after the strategy declaration must be byte-identical to the visual preview**.

No lifecycle rule may differ between builds.

## Source lineage

The generated strategy must be mechanically derived from the already runtime-validated Issue #66 C-2 Pine calculation lineage. Volume, MTF, Divergence, and witness stage bias remain forced into the same price-only configuration used for Issue #66 parity/visual review.

Do not hand-copy a second classifier implementation.

## Frozen lifecycle body

The body must preserve the exact Phase-A Python/Pine semantics:

- Stage1 fresh `rangeBreakUp` arms long; Stage2 confirms within `confirmBars`;
- mirrored Stage4/5 short setup;
- exact 1->2 / 4->5 transition-bar fresh break accepted;
- no flat chase inside already-running Stage2/5;
- long exits only on Formal 4/5/6;
- short exits only on Formal 1/2/3;
- Formal0 survives;
- ADD? continuation events do not change size;
- Early Fail only at ages 1..`confirmBars`;
- after fail, no same-direction re-entry without a new setup;
- no same-bar reopen after an opposite-family or Early-Fail close.

## Visual defaults

For the semantic-review build, default:

- Formal-stage background: ON;
- ARM markers: ON;
- entry/exit/fail markers: ON;
- early-fail protection line: ON;
- raw fresh-break markers: OFF;
- ADD? markers: OFF (available by input, but off by default to reduce clutter).

## Static gates before handing Pine to TradingView

1. C-2 source lineage is present and price-only witnesses remain forced off.
2. No D1 parity plots/checkpoint table leak into the strategy preview.
3. Both strategy declarations use `process_orders_on_close=false` and `pyramiding=0`.
4. Visual declaration uses fixed 1-unit sizing.
5. After removing only the strategy declaration line, visual and performance outputs are byte-identical.
6. Source tokens/contracts prohibit arbitrary Stage2/5 flat chase and preserve opposite-family-only exits.

## Human review checklist

Do not look at Strategy Tester performance during this review. Inspect chart events only.

Confirm on representative charts:

1. ARM happens in Stage1/4 context before ordinary confirmed entry.
2. Entry occurs on Stage2/5 confirmation within the three-bar handshake.
3. Exact transition-bar breaks may enter immediately.
4. A later fresh break inside an already-running Stage2/5 does not create a new flat chase entry.
5. Formal0 / same-side pauses do not flatten a held trade.
6. Opposite Formal family closes the trade.
7. Early Fail is visually limited to the first three bars after entry.
8. After Early Fail, the same trend cannot re-enter until a new precursor setup appears.

## Phase-B decision

Allowed outcomes:

- `PASS_ready_for_frozen_development_performance_retest`;
- `FAIL_pine_translation_or_execution_semantics`;
- `FAIL_human_lifecycle_semantics`.

Only the first outcome unlocks Phase C performance analysis. No performance result may be used to change Phase-B semantics.
