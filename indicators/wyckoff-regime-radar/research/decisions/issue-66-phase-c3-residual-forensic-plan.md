# Issue #66 Phase C-3 — Residual Strong/Formal Mismatch Forensic

Status: **diagnostic only / reused frozen data / no PnL / no formula change**

## Parent

Accepted C-2 repaired the only explicit Stage-1/Stage-4 candidate-conflict clause non-isomorphism while preserving every registered B-7 numeric classifier metric.

C-2 downstream state:

- strong-stage mirror: ~99.33%;
- Formal mirror: ~99.73%;
- Formal transition mirror: ~99.59%;
- strong-stage mismatch bars: 44;
- Formal mismatch bars: 18.

## Question

Do the remaining 44 strong-stage / 18 Formal mismatches reveal one additional explicit directional non-isomorphism that warrants repair, or are they residual threshold/argmax effects from small numeric reciprocal error in otherwise mirrored formulas?

## Required decomposition

### Strong-stage mismatch attribution

Re-run the exact Phase-C current-bar attribution on the C-2 core and report overlap with:

- top-stage mismatch;
- probability-valid mismatch;
- dominant threshold mismatch;
- top-gap threshold mismatch;
- evidence threshold mismatch;
- candidate-conflict mismatch;
- unexplained.

Report by FX pair and aggregate.

### Stage-1/4 residual conflict predicate forensic

On bars satisfying all of:

- top stage itself is already correctly mirrored;
- left/right top stages belong to the Stage-1/4 mirrored family;
- C-2 candidate-conflict booleans differ;

classify which reciprocal predicate changes truth value:

1. holding predicate: `resistance_holding >= absorb_threshold` ↔ `support_holding >= absorb_threshold`;
2. exhaustion predicate: `upside_exhaustion >= absorb_threshold` ↔ `downside_exhaustion >= absorb_threshold`;
3. continuation-override predicate: inferred when holding/exhaustion truth values mirror but final symmetric conflict clause differs.

For holding/exhaustion predicate mismatches, report absolute distance of each side from the existing `absorb_threshold`. These distances are descriptive only and may not be used to move the threshold.

### Formal residual

Report:

- 18 Formal mismatch bars by FX pair;
- mismatch episodes / maximum duration;
- current persistence-input mismatch vs pure state-carry share;
- stale-pressure reason/bar mirror agreement.

## Decision rule

C-3 authorizes **no automatic formula change**.

A further C-series repair is eligible only if the forensic finds a single explicit directional source formula that is still non-isomorphic.

If remaining mismatch is produced by:

- mirrored formulas whose numeric values straddle existing thresholds;
- argmax/tie sensitivity to already-small probability residuals;
- or symmetric persistence carrying those rare mismatches,

then stop classifier formula repair. Record the residual as an engineering tolerance issue and prepare the Phase-C→Phase-D handoff for Pine↔Python parity.

No threshold shopping for 100% mirror agreement is allowed.
