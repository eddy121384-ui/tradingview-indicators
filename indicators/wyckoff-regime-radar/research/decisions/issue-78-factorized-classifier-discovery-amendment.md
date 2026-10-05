# Issue #78 — Factorized classifier discovery amendment

Date: 2026-10-05

This amendment changes the role of the already-inspected OOS3 equity cohort for the factorized-classifier track.

## Decision

OOS3 may now be used actively for **architecture discovery**.

The project is intentionally separating two phases:

1. **Discovery**
   - use the existing heterogeneous OOS3 stock data;
   - inspect forward returns and conditional behavior;
   - compare alternative factor definitions and interactions;
   - iterate quickly on representation;
   - allow exploratory threshold / bin / weighting diagnostics where useful.

2. **Validation**
   - only after a candidate factorized architecture is worth freezing;
   - freeze formulas and translation rules;
   - then challenge them on untouched OOS4 / cross-asset / prospective data.

The purpose of the current phase is not to make an OOS claim. It is to answer:

> What representation of direction, range/expansion, lifecycle and supply-demand is actually useful enough to deserve a fresh validation?

## Consequence

The stricter OOS3 forward-outcome firewall in
`issue-78-factorized-classifier-architecture-preregistration.md`
is relaxed for the discovery phase.

The factor formulas in that preregistration are now **baseline candidate A0**, not immutable production candidates.

Allowed on OOS3:

- forward-return comparison;
- quintile / decile diagnostics;
- conditional interactions;
- alternative simple weights;
- monotonicity checks;
- temporal / sector / sleeve cuts;
- redundancy tests;
- lifecycle / supply-demand decomposition;
- comparison with the old six-stage representation.

Still prohibited:

- calling OOS3 a fresh OOS validation;
- presenting discovery improvements as production alpha;
- changing the historical OOS2/OOS3 findings;
- merging PR #80 as though the old six-stage architecture were validated.

The untouched OOS4 universe builder remains available, but OOS4 is deferred until discovery produces a candidate worth freezing.

Refs #78 #148 #147 #138 #135 #132 #131 #80.
