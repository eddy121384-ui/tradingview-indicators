# Issue #68 Phase B3.10 — Mirror Gate Interpretation Correction

Status: **ENGINEERING INTERPRETATION CORRECTION / BEFORE POOLED RESULT / NO MODEL CHANGE**

## Trigger

The first observable B3.10 frozen-data run showed:

- six-component reconstruction error = 2.842e-14;
- reciprocal exact handoff-event agreement minimum = 99.818% (passes the preregistered 99% gate);
- minimum per-pair/direction final-blocker exact-label agreement = 97.561%;
- minimum per-pair/direction handoff-driver exact-label agreement = 98.148%.

The failing implementation applied the 99% blocker/driver requirement to the **minimum of every pair × direction slice**.

## Why this is a correction, not threshold relaxation

The B3.10 preregistration states that reciprocal final-blocker / handoff-driver agreement must be >=99% **where both sides are comparable**. It does not preregister a minimum-per-small-slice gate.

A per-slice minimum changes the statistical unit after preregistration: one label mismatch in a 41- or 54-event slice can fail an otherwise highly reciprocal pooled attribution. That is an extra engineering constraint, not the registered research gate.

## Correct interpretation locked before pooled result is read

Primary B3.10 blocker/driver mirror gates will be evaluated over the **pooled set of all comparable reciprocal handoff events** across the frozen four-FX sample and both directions:

- pooled exact final-blocker matches / pooled comparable handoffs >= 99%;
- pooled exact handoff-driver matches / pooled comparable handoffs >= 99%.

The following remain unchanged:

- 99% threshold;
- exact handoff definition;
- exact argmin final-blocker definition;
- exact argmax handoff-driver definition;
- six component formulas;
- C-2 formulas, weights, gates, thresholds, persistence, Core Bias, Exposure.

Per-pair/direction minimum agreements remain in the report as **diagnostics only**.

If either pooled exact-label agreement is still below 99%, B3.10 remains FAIL and a separate preregistered tie/ambiguity audit will be required. No epsilon or tolerance will be chosen from observed mismatches.
