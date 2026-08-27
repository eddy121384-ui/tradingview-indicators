# Issue #66 Phase C-1 — Candidate-Conflict Residual Pre-Audit

Status: **diagnostic only / reused frozen data / no PnL / no formula change**

## Parent finding

Phase C v3 proved the inherited Issue #57 Phase-B stale-pressure persistence state machine is structurally reciprocal-symmetric and can replay all stored state series exactly.

On B-7 outputs, `candidate_conflict` accounts for 857 of 866 strong-stage mismatch bars (98.96% overlap).

## Question

Which mirrored stage family creates the remaining candidate-conflict asymmetry?

Families:

- Stage 1 Accumulation ↔ Stage 4 Distribution;
- Stage 2 Markup ↔ Stage 5 Markdown;
- Stage 3 Re-accumulation ↔ Stage 6 Re-distribution.

## Attribution rule

Use only post-warmup bars where the current top stage itself is already reciprocal-mirrored (`mirror(left_top_id) == right_top_id`).

Among those bars, count `candidate_conflict` boolean mismatches by the left-side top-stage mirrored family.

Bars where top stage is not mirrored are reported separately and may not be assigned to a conflict-clause family.

## Source-level expectation (not a pass criterion)

The current source is visibly non-isomorphic for Stage 1/4:

- Stage 1 conflict uses `resistance_holding`, `rebound_failure_gate > 0.50`, and `~markup_cont_override`;
- Stage 4 conflict uses `support_holding`, `downside_exhaustion`, and `~markup_cont_override`.

Stage 2/5 and Stage 3/6 clauses are already written as mirrored exhaustion/holding pairs with mirrored markup/markdown continuation overrides.

The data must decide whether Stage 1/4 is in fact the dominant residual family; the source observation alone does not authorize a repair.

## Decision rule

If one mirrored family contributes >=90% of attributable conflict mismatch bars, it becomes the only eligible C-2 repair family.

Otherwise stop and decompose the clauses more deeply before changing code.
