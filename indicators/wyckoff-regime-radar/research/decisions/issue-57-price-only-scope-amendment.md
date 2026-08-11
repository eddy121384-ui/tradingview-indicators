# Issue #57 — price-only scope amendment

Date: 2026-08-11

## Decision

Keep the current Wyckoff v0.6 / Top-2 research path **price-only**.

Do not add Volume, MTF, or Divergence back into the stage-weight engine merely to rescue or explain the current Candidate/Secondary hypothesis.

## Rationale

Live usage feedback is that the Volume layer did not improve practical usefulness and instead made the indicator harder to interpret. Simplicity and interpretability are therefore part of the product/research objective, not just implementation convenience.

The temporary idea of reproducing frozen v0.5.2.1 with default `Volume Mode = Auto` was diagnostic only. Its generator, test, workflow, and generated Pine harness were removed before user testing.

## Consequence

The next diagnostic must stay within the six **price-derived** regime weights. If the observed live intuition is real, search for a better description of the relationship among Candidate, Secondary, Formal, weight concentration, gap, transition state, and persistence using already-burned data only.

Do not use witness layers as post-hoc explanatory variables in this research branch.
